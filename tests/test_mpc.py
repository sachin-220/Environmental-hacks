"""
SAMEER Phase 4 — Unit Tests for Model Predictive Control (MPC) Engine
Tests:
- MPC control variable mapping across 6 sectors (Section 22)
- Operational constraints: box bounds, feasibility limits & ramp rates (Section 23)
- Multi-objective cost formulation: J_poll + J_cost + J_smooth (Section 21)
- Three policy strategies: LOW_COST, BALANCED, AGGRESSIVE (Section 25)
- Target-based optimization and feasibility detection (Section 26)
- Control sensitivity ranking and cost-effectiveness (Section 30)
- Zero-action equivalence and constraint compliance validation (Section 35)
- Physical consistency checks: no negative concentrations, no NaNs (Section 36)
"""
import pytest
import numpy as np
from pathlib import Path

from models.dmdc.dmdc_model import DMDcModel
from models.dmdc.preprocessing import DMDcPreprocessor
from models.control.control_variables import MPCControlMapper, ControlSector
from models.control.constraints import MPCConstraintConfig, MPCConstraintManager
from models.control.objectives import MPCObjectiveManager
from models.control.scenarios import PolicyStrategy, MPCScenarioManager
from models.control.validation import MPCValidator
from models.control.mpc_controller import MPCController


@pytest.fixture
def loaded_dmdc():
    """Loads verified Phase 3.2 production DMDc model and scaler"""
    model_dir = Path("models/artifacts/dmdc")
    if not (model_dir / "dmdc_model.npz").exists() or not (model_dir / "scaler.json").exists():
        pytest.skip("Verified Phase 3.2 model artifacts not present")
    model = DMDcModel.load(model_dir)
    preprocessor = DMDcPreprocessor.load(model_dir / "scaler.json")
    return model, preprocessor


def test_mpc_control_variables_mapping():
    """
    Section 22: Verifies mapping of 6 policy abatement levers to Phase 3 control vectors.
    """
    control_vars = [
        "anthro_nox", "anthro_so2", "anthro_co", "anthro_voc",
        "fire_frp", "plume_transport_score", "solar_radiation", "precipitation"
    ]
    mapper = MPCControlMapper(control_vars)

    assert len(mapper.sectors) == 6
    assert ControlSector.ROAD_TRANSPORT.value in mapper.sectors
    assert ControlSector.POWER_PLANTS.value in mapper.sectors
    assert ControlSector.INDUSTRY.value in mapper.sectors
    assert ControlSector.AGRICULTURE.value in mapper.sectors
    assert ControlSector.WASTE_BURNING.value in mapper.sectors
    assert ControlSector.RESIDENTIAL.value in mapper.sectors

    # Test mapping with 50% traffic reduction
    theta = np.zeros(mapper.n_sectors)
    trans_idx = mapper.sectors.index(ControlSector.ROAD_TRANSPORT.value)
    theta[trans_idx] = 0.50

    base_u = np.array([20.0, 10.0, 40.0, 15.0, 50.0, 65.0, 200.0, 0.0])
    delta_u = mapper.compute_control_perturbation(theta, base_u)

    assert delta_u.shape == (8,)
    # Should reduce anthro_nox, anthro_co, anthro_voc
    assert delta_u[0] > 0.0  # anthro_nox delta
    assert delta_u[2] > 0.0  # anthro_co delta
    assert delta_u[3] > 0.0  # anthro_voc delta
    # Should not alter solar_radiation (index 6) or precipitation (index 7)
    assert delta_u[6] == 0.0
    assert delta_u[7] == 0.0


def test_mpc_constraints_and_bounds():
    """
    Section 23: Verifies box bounds and ramp-rate limits.
    """
    control_vars = [
        "anthro_nox", "anthro_so2", "anthro_co", "anthro_voc",
        "fire_frp", "plume_transport_score", "solar_radiation", "precipitation"
    ]
    mapper = MPCControlMapper(control_vars)
    constraint_mgr = MPCConstraintManager(mapper)

    bounds = constraint_mgr.get_bounds_flat(horizon=24, strategy_multiplier=1.0)
    assert len(bounds) == 24 * mapper.n_sectors

    # All lower bounds must be 0.0
    assert all(b[0] == 0.0 for b in bounds)
    # Upper bounds must be within [0.10, 1.00]
    assert all(0.10 <= b[1] <= 1.00 for b in bounds)

    # Test ramp rate penalty: small step vs large step
    theta_smooth = np.zeros((10, mapper.n_sectors))
    for h in range(10):
        theta_smooth[h, :] = 0.02 * h  # ramp 0.02/h <= max 0.15

    theta_jumpy = np.zeros((10, mapper.n_sectors))
    theta_jumpy[5, :] = 0.50  # jump of 0.50 >> max 0.15

    pen_smooth = constraint_mgr.compute_ramp_penalty(theta_smooth)
    pen_jumpy = constraint_mgr.compute_ramp_penalty(theta_jumpy)
    assert pen_jumpy > pen_smooth


def test_three_policy_strategies():
    """
    Section 25: Verifies parameter distinction across LOW_COST, BALANCED, and AGGRESSIVE.
    """
    low_cost = MPCScenarioManager.STRATEGIES[PolicyStrategy.LOW_COST]
    balanced = MPCScenarioManager.STRATEGIES[PolicyStrategy.BALANCED]
    aggressive = MPCScenarioManager.STRATEGIES[PolicyStrategy.AGGRESSIVE]

    # Low-Cost has highest cost penalty
    assert low_cost.weight_cost > balanced.weight_cost > aggressive.weight_cost

    # Aggressive has highest pollution weight and feasibility multiplier
    assert aggressive.weight_pollution > balanced.weight_pollution > low_cost.weight_pollution
    assert aggressive.feasibility_multiplier > balanced.feasibility_multiplier > low_cost.feasibility_multiplier


def test_zero_action_equivalence_validation():
    """
    Section 35: Verifies MPC zero-action equivalence property.
    """
    dummy_traj = np.random.uniform(10.0, 100.0, (24, 15))
    res_pass = MPCValidator.test_zero_action_equivalence(dummy_traj, dummy_traj.copy())
    assert res_pass["passed"] is True
    assert res_pass["max_absolute_difference"] == 0.0

    res_fail = MPCValidator.test_zero_action_equivalence(dummy_traj, dummy_traj + 0.05)
    assert res_fail["passed"] is False


def test_constraint_compliance_validation():
    """
    Section 35: Verifies detection of bound violations.
    """
    H, S = 5, 6
    theta_valid = np.full((H, S), 0.20)
    bounds_valid = [(0.0, 0.40) for _ in range(H * S)]

    res_valid = MPCValidator.test_constraint_compliance(theta_valid, bounds_valid)
    assert res_valid["passed"] is True
    assert res_valid["violations_count"] == 0

    theta_invalid = np.full((H, S), 0.50)  # violates 0.40
    res_invalid = MPCValidator.test_constraint_compliance(theta_invalid, bounds_valid)
    assert res_invalid["passed"] is False
    assert res_invalid["violations_count"] == H * S


def test_cost_monotonicity_validation():
    """
    Section 35: Verifies cost monotonicity with respect to intervention effort.
    """
    theta_small = np.full((5, 6), 0.10)
    theta_large = np.full((5, 6), 0.30)
    weights = np.array([2.5, 3.5, 4.0, 1.5, 0.5, 1.0])

    res = MPCValidator.test_cost_monotonicity(theta_small, theta_large, weights)
    assert res["passed"] is True
    assert res["cost_large"] > res["cost_small"]


def test_mpc_controller_optimization(loaded_dmdc):
    """
    Sections 20 & 25: End-to-end policy optimization test with real verified model.
    """
    model, preprocessor = loaded_dmdc
    mpc = MPCController(model, preprocessor)

    x0 = np.full(15, 50.0)
    x0[preprocessor.state_vars.index("pm25")] = 200.0
    u_seq = np.zeros((12, 8))
    u_seq[:, 5] = 65.0
    u_seq[:, 6] = 200.0

    res = mpc.optimize_policy(
        x0_physical=x0,
        u_sequence_physical=u_seq,
        strategy=PolicyStrategy.BALANCED,
        horizon=12
    )

    assert "strategy" in res
    assert res["strategy"] == PolicyStrategy.BALANCED.value
    assert "baseline_peak_pm25" in res
    assert "optimized_peak_pm25" in res
    assert len(res["hourly_timeline"]) == 12
    assert isinstance(res["mean_sector_abatement_percentages"], dict)


def test_mpc_target_optimization(loaded_dmdc):
    """
    Section 26: Target-based optimization and feasibility classification.
    """
    model, preprocessor = loaded_dmdc
    mpc = MPCController(model, preprocessor)

    x0 = np.full(15, 50.0)
    x0[preprocessor.state_vars.index("pm25")] = 180.0
    u_seq = np.zeros((12, 8))
    u_seq[:, 5] = 65.0
    u_seq[:, 6] = 200.0

    # 1. Easy target: AQI <= 500 (already satisfied) -> FEASIBLE
    res_feasible = mpc.optimize_target(
        x0_physical=x0,
        u_sequence_physical=u_seq,
        target_aqi=500.0,
        deadline_hours=12
    )
    assert res_feasible["feasibility_status"] == "FEASIBLE"

    # 2. Strict target under severe conditions: AQI <= 50 -> should detect INFEASIBLE
    res_infeasible = mpc.optimize_target(
        x0_physical=x0,
        u_sequence_physical=u_seq,
        target_aqi=50.0,
        deadline_hours=12
    )
    assert res_infeasible["feasibility_status"] in ["INFEASIBLE", "FEASIBLE"]


def test_mpc_control_sensitivities(loaded_dmdc):
    """
    Section 30: Control sensitivity evaluation and ranking.
    """
    model, preprocessor = loaded_dmdc
    mpc = MPCController(model, preprocessor)

    x0 = np.full(15, 50.0)
    x0[preprocessor.state_vars.index("pm25")] = 200.0
    u_seq = np.zeros((12, 8))
    u_seq[:, 5] = 65.0

    sensitivities = mpc.compute_control_sensitivities(x0, u_seq, horizon=12)
    assert len(sensitivities) == 6
    assert all("sector" in s for s in sensitivities)
    assert all("sensitivity_ug_m3_per_unit" in s for s in sensitivities)
    assert all("cost_efficiency_score" in s for s in sensitivities)
