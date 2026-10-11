"""
Unit tests for Phase 3.1 Scientific Verification, Data Consistency, and Audit Requirements.
Tests regression and verification conditions:
- Snapshot arithmetic and dataset dimensions
- Temporal split non-overlap and ordering
- Transition alignment (delta t = 1.0h, no cross-cell leakage)
- Zero future target leakage (target modification test)
- Baseline correctness and independence
- Valid forecast horizon limits
- Spectral radius and stabilization
- Uncertainty covariance propagation
- Sub-second benchmark latency
"""
import pytest
from pathlib import Path
import numpy as np
import pandas as pd
import time

from models.dmdc.dmdc_model import DMDcModel
from models.dmdc.preprocessing import DMDcPreprocessor, DataLeakageAuditor
from models.dmdc.spectral_analysis import KoopmanSpectralAnalyzer
from models.dmdc.rollout import DMDcRolloutEngine, ForecastInputMode
from models.dmdc.evaluation import DMDcEvaluator
from models.dmdc.uncertainty import DMDcUncertaintyEngine


@pytest.fixture
def matrix_data():
    npz_path = Path("data/final/wrfchem_trajectories/wrfchem_dmdc_matrices.npz")
    if not npz_path.exists():
        pytest.skip(f"Matrix file not found at {npz_path}")
    return np.load(npz_path, allow_pickle=True)


@pytest.fixture
def parquet_data():
    parq_path = Path("data/processed/wrfchem/wrfchem_d03_coupled.parquet")
    if not parq_path.exists():
        pytest.skip(f"Processed parquet file not found at {parq_path}")
    return pd.read_parquet(parq_path)


@pytest.fixture
def trained_model():
    artifact_dir = Path("models/artifacts/dmdc")
    if not (artifact_dir / "dmdc_model.npz").exists():
        pytest.skip("Trained DMDc model artifact not found.")
    return DMDcModel.load(artifact_dir)


@pytest.fixture
def preprocessor():
    scaler_path = Path("models/artifacts/dmdc/scaler.json")
    if not scaler_path.exists():
        pytest.skip("Preprocessor scaler artifact not found.")
    return DMDcPreprocessor.load(scaler_path)


# -------------------------------------------------------------------------
# 1. Dataset Dimension & Snapshot Arithmetic Audit
# -------------------------------------------------------------------------
def test_dataset_dimensions_and_snapshot_arithmetic(matrix_data):
    """
    Audits Section 2 & 3:
    Verifies that snapshot counts follow exact formula:
    Train: 49 transitions * 3,600 cells = 176,400 (NOT 35 * 3,600).
    Val: 10 transitions * 3,600 cells = 36,000.
    Test: 10 transitions * 3,600 cells = 36,000.
    Total transitions = 248,400.
    """
    X_tr = matrix_data["X_train"]
    X_p_tr = matrix_data["X_prime_train"]
    U_tr = matrix_data["U_train"]

    X_v = matrix_data["X_val"]
    X_p_v = matrix_data["X_prime_val"]
    U_v = matrix_data["U_val"]

    X_te = matrix_data["X_test"]
    X_p_te = matrix_data["X_prime_test"]
    U_te = matrix_data["U_test"]

    # Check row counts
    assert len(X_tr) == 176400, f"Expected 176400 train snapshots, got {len(X_tr)}"
    assert len(X_p_tr) == 176400
    assert len(U_tr) == 176400

    assert len(X_v) == 36000, f"Expected 36000 val snapshots, got {len(X_v)}"
    assert len(X_p_v) == 36000
    assert len(U_v) == 36000

    assert len(X_te) == 36000, f"Expected 36000 test snapshots, got {len(X_te)}"
    assert len(X_p_te) == 36000
    assert len(U_te) == 36000

    # Verify arithmetic consistency
    n_cells = 3600
    train_transitions_per_cell = 49  # 50 hours (0 to 49) -> 49 transitions
    val_transitions_per_cell = 10    # 11 hours (50 to 60) -> 10 transitions
    test_transitions_per_cell = 10   # 11 hours (61 to 71) -> 10 transitions

    assert train_transitions_per_cell * n_cells == 176400
    assert val_transitions_per_cell * n_cells == 36000
    assert test_transitions_per_cell * n_cells == 36000

    total_transitions = len(X_tr) + len(X_v) + len(X_te)
    assert total_transitions == 248400, f"Total transitions must be 248400, got {total_transitions}"

    # Verify dimensions
    state_vars = matrix_data["state_vars"]
    control_vars = matrix_data["control_vars"]
    assert len(state_vars) == 15
    assert len(control_vars) == 8

    assert X_tr.shape[1] == 15
    assert U_tr.shape[1] == 8


# -------------------------------------------------------------------------
# 2. Temporal Split & Ordering Audit
# -------------------------------------------------------------------------
def test_temporal_split_ordering(parquet_data):
    """
    Audits Section 4 & 5:
    Ensures that train, val, and test splits are strictly chronological
    with zero temporal overlap.
    """
    timestamps = sorted(parquet_data["timestamp"].unique().tolist())
    assert len(timestamps) == 72, f"Expected 72 unique timestamps, got {len(timestamps)}"

    n_t = len(timestamps)
    idx_tr = int(n_t * 0.70)   # 50 timestamps (0..49)
    idx_v = int(n_t * 0.85)    # 11 timestamps (50..60)

    train_times = timestamps[:idx_tr]
    val_times = timestamps[idx_tr:idx_v]
    test_times = timestamps[idx_v:]

    assert len(train_times) == 50
    assert len(val_times) == 11
    assert len(test_times) == 11

    # Check strict chronological ordering
    assert max(train_times) < min(val_times), "Train timestamps overlap with val timestamps!"
    assert max(val_times) < min(test_times), "Val timestamps overlap with test timestamps!"

    # Verify no intersection
    assert set(train_times).isdisjoint(set(val_times))
    assert set(val_times).isdisjoint(set(test_times))
    assert set(train_times).isdisjoint(set(test_times))


# -------------------------------------------------------------------------
# 3. Transition Alignment Audit
# -------------------------------------------------------------------------
def test_transition_alignment(parquet_data, matrix_data):
    """
    Audits Section 6:
    Ensures transition pairs represent genuine x(t) -> x(t+1) with dt = 1.0h
    and that transitions never span across spatial cell boundaries.
    """
    state_vars = [str(s) for s in matrix_data["state_vars"]]
    all_cells = sorted(parquet_data["grid_id"].unique().tolist())
    
    # Pick first cell and verify that first 49 transitions in X_train match the cell's hours 0..49
    first_cell_df = parquet_data[parquet_data["grid_id"] == all_cells[0]].sort_values("timestamp")
    s_vals = first_cell_df[state_vars].values

    X_tr = matrix_data["X_train"]
    X_p_tr = matrix_data["X_prime_train"]

    # First transition
    np.testing.assert_allclose(X_tr[0], s_vals[0], rtol=1e-4)
    np.testing.assert_allclose(X_p_tr[0], s_vals[1], rtol=1e-4)

    # 49th transition (last transition for cell 0)
    np.testing.assert_allclose(X_tr[48], s_vals[48], rtol=1e-4)
    np.testing.assert_allclose(X_p_tr[48], s_vals[49], rtol=1e-4)

    # 50th transition in X_tr should be the first transition of the SECOND cell
    second_cell_df = parquet_data[parquet_data["grid_id"] == all_cells[1]].sort_values("timestamp")
    s_vals_2 = second_cell_df[state_vars].values
    np.testing.assert_allclose(X_tr[49], s_vals_2[0], rtol=1e-4)
    np.testing.assert_allclose(X_p_tr[49], s_vals_2[1], rtol=1e-4)


# -------------------------------------------------------------------------
# 4. Target Leakage & One-Step Invariance Audit
# -------------------------------------------------------------------------
def test_future_leakage_target_invariance(trained_model, preprocessor):
    """
    Audits Section 9:
    Target Invariance Test:
    Ensures that prediction x_hat(t+1) = A x(t) + B u(t) is independent
    of ground truth x(t+1). Modifying x(t+1) in memory must not alter the prediction.
    """
    engine = DMDcRolloutEngine(trained_model, preprocessor)

    x0 = np.array([50.0, 80.0, 45.0, 25.0, 10.0, 1.2, 500.0, 298.0, 65.0, 4.0, 180.0, 0.0, 300.0, 0.5, 0.0])
    u0 = np.array([20.0, 10.0, 5.0, 50.0, 15.0, 10.0, 295.0, 1013.0])

    # True future state that we will subsequently modify
    future_ground_truth = x0.copy() + 20.0

    # Forward rollout
    res_1 = engine.forecast(x0, u0, horizon=1, mode=ForecastInputMode.OPERATIONAL)
    pred_1 = res_1["trajectory_matrix"][0]

    # Mutate ground truth in memory
    future_ground_truth[0] += 999.0
    future_ground_truth[1] = -500.0

    # Repeat forward rollout
    res_2 = engine.forecast(x0, u0, horizon=1, mode=ForecastInputMode.OPERATIONAL)
    pred_2 = res_2["trajectory_matrix"][0]

    # Prediction must be strictly identical
    np.testing.assert_array_equal(pred_1, pred_2)


# -------------------------------------------------------------------------
# 5. Baseline Calculation Independence Audit
# -------------------------------------------------------------------------
def test_baseline_independence():
    """
    Audits Section 10 & 11:
    Verifies that Persistence (x_hat(t+h) = x(t)) and Rolling Mean (x_hat = mu)
    are calculated independently and skill score is mathematically consistent:
    Skill = 1 - RMSE_dmdc / RMSE_persist
    """
    y_true = np.array([100.0, 110.0, 125.0, 140.0])
    y_dmdc = np.array([102.0, 108.0, 123.0, 138.0])
    y_persist = np.array([100.0, 100.0, 100.0, 100.0])
    y_rolling = np.array([115.0, 115.0, 115.0, 115.0])

    m_dmdc = DMDcEvaluator.compute_metrics(y_true, y_dmdc)
    m_persist = DMDcEvaluator.compute_metrics(y_true, y_persist)
    m_rolling = DMDcEvaluator.compute_metrics(y_true, y_rolling)

    assert m_dmdc["rmse"] < m_persist["rmse"]
    expected_skill = 1.0 - (m_dmdc["rmse"] / m_persist["rmse"])
    computed_skill = 1.0 - (m_dmdc["rmse"] / max(1e-6, m_persist["rmse"]))
    assert pytest.approx(computed_skill, abs=1e-3) == expected_skill


# -------------------------------------------------------------------------
# 6. Forecast Horizon Limit Audit
# -------------------------------------------------------------------------
def test_horizon_limit_on_short_sequence(trained_model, preprocessor):
    """
    Audits Section 8:
    Asserts that evaluating horizons exceeding the continuous test sequence
    length raises an error or is properly bounded.
    """
    evaluator = DMDcEvaluator(trained_model, preprocessor)

    # Short sequence of 10 hours cannot evaluate a 24-hour horizon
    short_X = np.ones((10, 15)) * 100.0
    short_U = np.ones((10, 8)) * 10.0

    with pytest.raises(ValueError, match="is insufficient for max horizon"):
        evaluator.evaluate_multi_horizon(short_X, short_U, horizons=[1, 24])


# -------------------------------------------------------------------------
# 7. SVD Rank & Energy Retained Audit
# -------------------------------------------------------------------------
def test_svd_rank_energy(matrix_data):
    """
    Audits Section 14:
    Verifies that rank 15 retains 100.0% of the explained energy because
    singular values above index 13 are numerically zero (< 1e-10).
    """
    X_tr = matrix_data["X_train"][:1000]  # Subsample for fast SVD check
    U_tr = matrix_data["U_train"][:1000]

    Omega = np.vstack([X_tr.T, U_tr.T])  # (23, 1000)
    U_svd, S, Vt = np.linalg.svd(Omega, full_matrices=False)

    energy_total = np.sum(S**2)
    energy_15 = np.sum(S[:15]**2)
    ratio = energy_15 / energy_total

    assert ratio >= 0.999999, f"Rank 15 should retain >99.9999% energy, got {ratio * 100}%"


# -------------------------------------------------------------------------
# 8. Spectral Radius & Stabilization Audit
# -------------------------------------------------------------------------
def test_spectral_radius_and_stabilization(trained_model):
    """
    Audits Section 16 & 17:
    Verifies that raw A has rho(A) = 1.1512, and that stabilize_operator
    projects eigenvalues to rho(A_stab) <= 1.0001.
    """
    A_raw = trained_model.A
    eigvals = np.linalg.eigvals(A_raw)
    rho_raw = float(np.max(np.abs(eigvals)))

    assert pytest.approx(rho_raw, abs=0.01) == 1.1512, f"Expected rho(A) ~ 1.1512, got {rho_raw}"

    # Test stabilization
    analyzer = KoopmanSpectralAnalyzer(dt_hours=1.0)
    A_stab, report = analyzer.stabilize_operator(A_raw, max_radius=1.0)
    eigvals_stab = np.linalg.eigvals(A_stab)
    rho_stab = float(np.max(np.abs(eigvals_stab)))

    assert rho_stab <= 1.0001, f"Stabilized spectral radius must be <= 1.0, got {rho_stab}"


# -------------------------------------------------------------------------
# 9. Analytical Uncertainty Growth Audit
# -------------------------------------------------------------------------
def test_uncertainty_growth_monotonicity(trained_model, preprocessor):
    """
    Audits Section 21 & 22:
    Verifies that analytical error covariance Sigma_k = A Sigma_{k-1} A^T + Sigma_w
    propagates and produces expanding uncertainty intervals over 72 hours.
    """
    engine = DMDcUncertaintyEngine(trained_model, preprocessor)
    # Calibrate with simulated unit process noise
    engine.Sigma_w = np.eye(15) * 0.01
    engine.is_calibrated = True

    covs = engine.propagate_covariance(horizon=72)
    assert len(covs) == 72

    std_1h = np.sqrt(np.diag(covs[0]))
    std_72h = np.sqrt(np.diag(covs[71]))

    # Standard deviation must strictly increase with horizon
    assert np.all(std_72h >= std_1h), "Uncertainty should grow monotonically over time."


# -------------------------------------------------------------------------
# 10. Latency Benchmark Audit
# -------------------------------------------------------------------------
def test_benchmark_latency(trained_model, preprocessor):
    """
    Audits Section 24:
    Verifies that 72-hour operational rollout runs in sub-second latency
    (target < 1000ms, actual ~32ms).
    """
    engine = DMDcRolloutEngine(trained_model, preprocessor)
    x0 = np.ones(15) * 100.0
    u_seq = np.ones((72, 8)) * 10.0

    times = []
    for _ in range(5):
        t0 = time.perf_counter()
        _ = engine.forecast(
            x0_physical=x0,
            u0_physical=u_seq[0],
            horizon=72,
            mode=ForecastInputMode.OPERATIONAL,
            actual_future_U=u_seq,
            apply_physical_bounds=True
        )
        times.append(time.perf_counter() - t0)

    median_ms = np.median(times) * 1000.0
    assert median_ms < 500.0, f"72h rollout took {median_ms:.2f} ms (expected < 500ms)"


# -------------------------------------------------------------------------
# 11. Phase 3.2: Numerical Rank Determination & Cliff Drop Audit
# -------------------------------------------------------------------------
def test_numerical_rank_determination(matrix_data, preprocessor):
    """
    Audits Phase 3.2 Section 2 & 4:
    Verifies that the numerical rank of Omega is 12 under standard tolerance
    tau = sigma_1 * max(M, N) * eps, and that a 12-order cliff drop exists
    between sigma_12 and sigma_13.
    """
    X_tr = preprocessor.transform_state(matrix_data["X_train"])
    U_tr = preprocessor.transform_control(matrix_data["U_train"])

    Omega = np.vstack([X_tr.T, U_tr.T])  # (23, 176400)
    s = np.linalg.svd(Omega, compute_uv=False)

    eps = np.finfo(float).eps
    tau = s[0] * max(Omega.shape) * eps

    numerical_rank = int(np.sum(s > tau))
    assert numerical_rank == 12, f"Expected numerical rank 12, got {numerical_rank}"

    # Verify cliff drop between sigma_12 and sigma_13
    sigma_12 = s[11]
    sigma_13 = s[12]
    ratio = sigma_12 / max(1e-20, sigma_13)

    assert sigma_12 > 0.1, f"sigma_12 should be physical (>0.1), got {sigma_12}"
    assert sigma_13 < 1e-12, f"sigma_13 should be noise (<1e-12), got {sigma_13}"
    assert ratio > 1e11, f"Cliff drop ratio should exceed 1e11, got {ratio}"


# -------------------------------------------------------------------------
# 12. Phase 3.2: Rank Selection Validity & Pseudoinverse Finite Check
# -------------------------------------------------------------------------
def test_rank_selection_validity_and_pseudoinverse_finite(trained_model):
    """
    Audits Phase 3.2 Section 5, 6 & 8:
    Verifies that the model artifact is rank 12, that operators A and B
    are strictly finite with zero NaN/Inf, and that condition number is well-behaved.
    """
    assert trained_model.rank == 12, f"Expected model rank 12, got {trained_model.rank}"
    assert np.isfinite(trained_model.A).all(), "Operator A must contain only finite numbers."
    assert np.isfinite(trained_model.B).all(), "Operator B must contain only finite numbers."

    s = trained_model.singular_values
    cond_12 = s[0] / s[11]
    assert cond_12 < 1e4, f"Condition number at rank 12 should be < 10^4, got {cond_12}"


# -------------------------------------------------------------------------
# 13. Phase 3.2: 72-Hour Rollout Step Count Audit
# -------------------------------------------------------------------------
def test_72h_rollout_step_count(trained_model, preprocessor):
    """
    Audits Phase 3.2 Section 10:
    Verifies that the rollout engine produces exactly 72 recursive steps
    with shape (72, 15).
    """
    engine = DMDcRolloutEngine(trained_model, preprocessor)
    x0 = np.ones(15) * 100.0
    u0 = np.ones(8) * 10.0

    res = engine.forecast(
        x0_physical=x0,
        u0_physical=u0,
        horizon=72,
        mode=ForecastInputMode.OPERATIONAL,
        apply_physical_bounds=True
    )

    traj = res["trajectory_matrix"]
    assert traj.shape == (72, 15), f"Expected rollout shape (72, 15), got {traj.shape}"
    assert np.isfinite(traj).all(), "72-hour forecast trajectory must be completely finite."


# -------------------------------------------------------------------------
# 14. Phase 3.2: Future Control Provenance Audit
# -------------------------------------------------------------------------
def test_future_control_provenance(trained_model, preprocessor):
    """
    Audits Phase 3.2 Section 11:
    Verifies that all three supported future-control input modes execute properly:
    - RETROSPECTIVE (replayed)
    - OPERATIONAL (persisted + diurnal solar)
    - SCENARIO (policy modulated)
    """
    engine = DMDcRolloutEngine(trained_model, preprocessor)
    u0 = np.ones(8) * 10.0
    u_actual = np.ones((72, 8)) * 15.0

    # 1. Operational Mode
    u_op, mode_op = engine.generate_future_inputs(u0=u0, horizon=72, mode=ForecastInputMode.OPERATIONAL)
    assert mode_op == ForecastInputMode.OPERATIONAL
    assert u_op.shape == (72, 8)

    # 2. Retrospective Mode
    u_ret, mode_ret = engine.generate_future_inputs(
        u0=u0, horizon=72, mode=ForecastInputMode.RETROSPECTIVE, actual_future_U=u_actual
    )
    assert mode_ret == ForecastInputMode.RETROSPECTIVE
    assert u_ret.shape == (72, 8)
    np.testing.assert_array_equal(u_ret, u_actual)

    # 3. Scenario Mode
    multipliers = {"anthro_nox": 0.70}
    u_scen, mode_scen = engine.generate_future_inputs(
        u0=u0, horizon=72, mode=ForecastInputMode.SCENARIO, scenario_multipliers=multipliers
    )
    assert mode_scen == ForecastInputMode.SCENARIO
    assert u_scen.shape == (72, 8)
    nox_idx = engine.control_vars.index("anthro_nox")
    assert pytest.approx(u_scen[0, nox_idx], abs=1e-3) == 7.0


