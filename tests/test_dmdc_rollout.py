"""
Unit tests for 72-Hour Recursive Rollout, Physical Bounds Checks, and NAQI
"""
import pytest
import numpy as np
from models.dmdc.dmdc_model import DMDcModel
from models.dmdc.preprocessing import DMDcPreprocessor
from models.dmdc.rollout import DMDcRolloutEngine, ForecastInputMode
from models.dmdc.aqi import NationalAQICalculator


@pytest.fixture
def fitted_rollout_components():
    np.random.seed(42)
    n_states, n_controls = 15, 8
    N = 100

    X = np.random.normal(100.0, 20.0, (N, n_states))
    X_prime = np.random.normal(100.0, 20.0, (N, n_states))
    U = np.random.normal(10.0, 2.0, (N, n_controls))

    prep = DMDcPreprocessor()
    prep.fit(X, U)

    X_s = prep.transform_state(X)
    X_p_s = prep.transform_state(X_prime)
    U_s = prep.transform_control(U)

    model = DMDcModel()
    model.fit(X_s, X_p_s, U_s, rank=10, reg_lambda=1e-4)

    return model, prep


def test_recursive_72h_rollout(fitted_rollout_components):
    model, prep = fitted_rollout_components
    engine = DMDcRolloutEngine(model, prep)

    x0 = np.ones(15) * 80.0
    u0 = np.ones(8) * 5.0

    res = engine.forecast(
        x0_physical=x0,
        u0_physical=u0,
        horizon=72,
        mode=ForecastInputMode.OPERATIONAL
    )

    assert res["summary"]["horizon_hours"] == 72
    assert len(res["forecast"]) == 72
    assert res["trajectory_matrix"].shape == (72, 15)

    # Check checkpoints: 1h, 6h, 12h, 24h, 48h, 72h
    checkpoints = res["summary"]["checkpoints"]
    assert "1h" in checkpoints
    assert "24h" in checkpoints
    assert "72h" in checkpoints
    assert checkpoints["72h"]["pm25"] >= 0.0


def test_future_input_modes(fitted_rollout_components):
    model, prep = fitted_rollout_components
    engine = DMDcRolloutEngine(model, prep)

    x0 = np.ones(15) * 120.0
    u0 = np.ones(8) * 10.0
    actual_U = np.ones((72, 8)) * 15.0

    # Retrospective
    res_retro = engine.forecast(x0, u0, horizon=72, mode=ForecastInputMode.RETROSPECTIVE, actual_future_U=actual_U)
    assert res_retro["summary"]["forecast_mode"] == "RETROSPECTIVE"

    # Scenario: 50% reduction in traffic NOx
    scenario_multipliers = {"anthro_nox": 0.50}
    res_scen = engine.forecast(x0, u0, horizon=72, mode=ForecastInputMode.SCENARIO, actual_future_U=actual_U, scenario_multipliers=scenario_multipliers)
    assert res_scen["summary"]["forecast_mode"] == "SCENARIO"
    assert res_scen["forecast"][0]["exogenous_inputs"]["anthro_nox"] == 7.5  # 15.0 * 0.5


def test_physical_consistency_checks(fitted_rollout_components):
    model, prep = fitted_rollout_components
    engine = DMDcRolloutEngine(model, prep)

    # Force an unconstrained model prediction with negative initial values
    x0_invalid = np.ones(15) * -50.0
    u0 = np.ones(8) * 5.0

    res = engine.forecast(x0_invalid, u0, horizon=10, mode=ForecastInputMode.OPERATIONAL, apply_physical_bounds=True)
    
    # Assert physical clipping and logging
    assert res["summary"]["physical_constraint_violations_count"] > 0
    assert len(res["violations_log"]) > 0
    # PM2.5 must be non-negative in output
    assert res["forecast"][0]["pm25"] >= 0.0


def test_cpcb_naqi_calculation():
    # Good
    aqi_good = NationalAQICalculator.evaluate_aqi({"pm25": 20.0, "pm10": 40.0, "no2": 25.0})
    assert aqi_good["category"] == "Good"
    assert aqi_good["aqi"] <= 50.0

    # Severe
    aqi_severe = NationalAQICalculator.evaluate_aqi({"pm25": 320.0, "pm10": 480.0, "no2": 150.0})
    assert aqi_severe["category"] == "Severe"
    assert aqi_severe["aqi"] >= 401.0
    assert aqi_severe["dominant_pollutant"] in ["pm25", "pm10"]
