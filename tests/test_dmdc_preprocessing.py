"""
Unit tests for DMDc Preprocessing, Normalization, and Data Leakage Audit
"""
import pytest
import numpy as np
from pathlib import Path
from models.dmdc.preprocessing import DMDcPreprocessor, DataLeakageAuditor


def test_dmdc_preprocessor_fitting_and_invertibility():
    np.random.seed(42)
    n_states, n_controls = 15, 8
    N = 200

    X_train = np.random.normal(loc=120.0, scale=40.0, size=(N, n_states))
    U_train = np.random.normal(loc=15.0, scale=5.0, size=(N, n_controls))

    preprocessor = DMDcPreprocessor()
    preprocessor.fit(X_train, U_train)

    assert preprocessor.is_fitted
    assert len(preprocessor.state_mean) == n_states
    assert len(preprocessor.control_mean) == n_controls

    # Transform and inverse transform
    X_scaled = preprocessor.transform_state(X_train)
    X_recovered = preprocessor.inverse_transform_state(X_scaled)

    np.testing.assert_allclose(X_recovered, X_train, rtol=1e-5, atol=1e-5)

    U_scaled = preprocessor.transform_control(U_train)
    U_recovered = preprocessor.inverse_transform_control(U_scaled)

    np.testing.assert_allclose(U_recovered, U_train, rtol=1e-5, atol=1e-5)


def test_dmdc_preprocessor_nan_handling():
    n_states, n_controls = 15, 8
    X_train = np.ones((50, n_states)) * 100.0
    X_train[0, 0] = np.nan
    X_train[1, 1] = np.inf

    U_train = np.ones((50, n_controls)) * 10.0

    preprocessor = DMDcPreprocessor()
    preprocessor.fit(X_train, U_train)

    assert not np.isnan(preprocessor.state_mean[0])
    assert not np.isinf(preprocessor.state_mean[1])


def test_dmdc_preprocessor_serialization(tmp_path: Path):
    n_states, n_controls = 15, 8
    X_train = np.random.rand(50, n_states) * 50.0
    U_train = np.random.rand(50, n_controls) * 10.0

    preprocessor = DMDcPreprocessor()
    preprocessor.fit(X_train, U_train)

    json_path = tmp_path / "scaler.json"
    preprocessor.save(json_path)
    assert json_path.exists()

    loaded = DMDcPreprocessor.load(json_path)
    assert loaded.is_fitted
    np.testing.assert_allclose(loaded.state_mean, preprocessor.state_mean)
    np.testing.assert_allclose(loaded.state_scale, preprocessor.state_scale)


def test_data_leakage_audit():
    train_times = ["2023-11-01T00:00:00Z", "2023-11-01T01:00:00Z", "2023-11-01T02:00:00Z"]
    val_times = ["2023-11-01T03:00:00Z", "2023-11-01T04:00:00Z"]
    test_times = ["2023-11-01T05:00:00Z", "2023-11-01T06:00:00Z"]

    clean_audit = DataLeakageAuditor.audit_splits(train_times, val_times, test_times, scaler_fitted_on_test=False)
    assert clean_audit["status"] == "PASS"
    assert clean_audit["future_target_leakage"] == "NONE"

    # Leakage scenario 1: overlapping times
    leaky_times = ["2023-11-01T02:00:00Z", "2023-11-01T03:00:00Z"]
    leaky_audit = DataLeakageAuditor.audit_splits(train_times, leaky_times, test_times, scaler_fitted_on_test=False)
    assert leaky_audit["status"] == "FAIL"
    assert leaky_audit["train_val_overlap_count"] == 1

    # Leakage scenario 2: scaler contaminated with test data
    scaler_leaky = DataLeakageAuditor.audit_splits(train_times, val_times, test_times, scaler_fitted_on_test=True)
    assert scaler_leaky["status"] == "FAIL"
