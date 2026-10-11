"""
Unit tests for Atmospheric Metrics, Baseline Comparisons, and Multi-Horizon Evaluation
"""
import pytest
import numpy as np
from models.dmdc.dmdc_model import DMDcModel
from models.dmdc.preprocessing import DMDcPreprocessor
from models.dmdc.evaluation import DMDcEvaluator


def test_metric_calculation():
    y_true = np.array([100.0, 150.0, 200.0, 250.0, 300.0])
    y_pred = np.array([105.0, 145.0, 210.0, 240.0, 310.0])

    metrics = DMDcEvaluator.compute_metrics(y_true, y_pred)

    assert metrics["count"] == 5
    assert metrics["mae"] == pytest.approx(8.0, abs=0.1)
    assert metrics["mean_bias"] == pytest.approx(2.0, abs=0.1)
    assert metrics["r2"] > 0.95
    assert metrics["pearson_r"] > 0.98


def test_multi_horizon_evaluation():
    np.random.seed(42)
    n_states, n_controls = 15, 8
    N = 100

    X_train = np.random.normal(120.0, 30.0, (N, n_states))
    X_p_train = np.random.normal(120.0, 30.0, (N, n_states))
    U_train = np.random.normal(15.0, 3.0, (N, n_controls))

    prep = DMDcPreprocessor()
    prep.fit(X_train, U_train)

    X_s = prep.transform_state(X_train)
    X_p_s = prep.transform_state(X_p_train)
    U_s = prep.transform_control(U_train)

    model = DMDcModel()
    model.fit(X_s, X_p_s, U_s, rank=10, reg_lambda=1e-4)

    evaluator = DMDcEvaluator(model, prep)

    # Test sequence of 80 hours
    X_test_seq = np.random.normal(120.0, 30.0, (80, n_states))
    U_test_seq = np.random.normal(15.0, 3.0, (80, n_controls))

    eval_res = evaluator.evaluate_multi_horizon(
        X_test_seq=X_test_seq,
        U_test_seq=U_test_seq,
        horizons=[1, 6, 24]
    )

    assert "results_by_horizon" in eval_res
    assert "1h" in eval_res["results_by_horizon"]
    assert "24h" in eval_res["results_by_horizon"]

    pm25_1h = eval_res["results_by_horizon"]["1h"]["pm25"]
    assert "dmdc" in pm25_1h
    assert "persistence_baseline" in pm25_1h
    assert "rolling_mean_baseline" in pm25_1h
    assert "skill_score_vs_persistence" in pm25_1h
