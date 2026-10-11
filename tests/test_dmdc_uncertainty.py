"""
Unit tests for Analytical Residual Covariance Propagation and Forecast Uncertainty
"""
import pytest
import numpy as np
from pathlib import Path
from models.dmdc.dmdc_model import DMDcModel
from models.dmdc.preprocessing import DMDcPreprocessor
from models.dmdc.uncertainty import DMDcUncertaintyEngine


def test_uncertainty_calibration_and_covariance_propagation():
    np.random.seed(42)
    n_states, n_controls = 15, 8
    N = 150

    X_train = np.random.normal(100.0, 25.0, (N, n_states))
    X_p_train = np.random.normal(100.0, 25.0, (N, n_states))
    U_train = np.random.normal(15.0, 3.0, (N, n_controls))

    prep = DMDcPreprocessor()
    prep.fit(X_train, U_train)

    X_s = prep.transform_state(X_train)
    X_p_s = prep.transform_state(X_p_train)
    U_s = prep.transform_control(U_train)

    model = DMDcModel()
    model.fit(X_s, X_p_s, U_s, rank=10, reg_lambda=1e-4)

    unc_engine = DMDcUncertaintyEngine(model, prep)
    unc_engine.calibrate(X_train, X_p_train, U_train)

    assert unc_engine.is_calibrated
    assert unc_engine.Sigma_w.shape == (n_states, n_states)
    assert np.all(np.diag(unc_engine.Sigma_w) > 0.0)

    # Covariance propagation over 72 hours
    covs = unc_engine.propagate_covariance(horizon=72)
    assert len(covs) == 72
    assert covs[0].shape == (n_states, n_states)
    assert covs[-1].shape == (n_states, n_states)

    # Prediction intervals
    test_traj = np.ones((72, n_states)) * 120.0
    intervals = unc_engine.compute_prediction_intervals(test_traj, confidence_level=0.95)

    assert intervals["horizon_hours"] == 72
    assert "uncertainty_growth" in intervals
    assert "1h" in intervals["uncertainty_growth"]
    assert "72h" in intervals["uncertainty_growth"]

    # Lower bound < Trajectory < Upper bound
    low = intervals["lower_bounds"]
    up = intervals["upper_bounds"]
    assert np.all(low <= test_traj)
    assert np.all(up >= test_traj)


def test_uncertainty_serialization(tmp_path: Path):
    model = DMDcModel()
    prep = DMDcPreprocessor()
    unc_engine = DMDcUncertaintyEngine(model, prep)
    unc_engine.Sigma_w = np.eye(15) * 0.05
    unc_engine.is_calibrated = True

    save_file = tmp_path / "uncertainty_model.npz"
    unc_engine.save(save_file)
    assert save_file.exists()

    loaded = DMDcUncertaintyEngine.load(save_file, model, prep)
    assert loaded.is_calibrated
    np.testing.assert_allclose(loaded.Sigma_w, unc_engine.Sigma_w)
