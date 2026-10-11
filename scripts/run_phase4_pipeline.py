"""
Phase 4 End-to-End Execution, Attribution, Counterfactual Intelligence, and MPC Runner
"""
import sys
import json
import time
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import settings
from config.logging_config import get_logger
from models.dmdc.dmdc_model import DMDcModel
from models.dmdc.preprocessing import DMDcPreprocessor
from models.dmdc.uncertainty import DMDcUncertaintyEngine
from models.attribution import (
    SourceAttributionEngine,
    CounterfactualEngine,
    SourcePerturbation,
    AttributionSector,
    ProvenanceType
)
from models.explainability import WhyAQIRisesEngine
from models.control import (
    MPCController,
    PolicyStrategy
)

logger = get_logger("scripts.run_phase4_pipeline")


def run_phase4():
    print("=" * 70)
    print("STARTING SAMEER PHASE 4 PIPELINE EXECUTION")
    print("=" * 70)

    # 1. Load Verified Phase 3 Artifacts
    artifact_dir = Path("models/artifacts/dmdc")
    data_path = Path("data/final/wrfchem_trajectories/wrfchem_dmdc_matrices.npz")
    firms_path = Path("DATASETS/02_satellite_firms_viirs.csv")

    model = DMDcModel.load(artifact_dir)
    preprocessor = DMDcPreprocessor.load(artifact_dir / "scaler.json")
    
    unc_path = artifact_dir / "uncertainty_model.npz"
    uncertainty_engine = None
    if unc_path.exists():
        uncertainty_engine = DMDcUncertaintyEngine(model, preprocessor)
        raw_unc = np.load(unc_path, allow_pickle=True)
        if "Sigma_w" in raw_unc:
            uncertainty_engine.Sigma_w = raw_unc["Sigma_w"]
            uncertainty_engine.is_calibrated = True

    data = np.load(data_path, allow_pickle=True)
    X_test = data["X_test"]
    U_test = data["U_test"]

    # Sample realistic test initial state and control sequence (24h)
    x0 = X_test[0].copy()
    u_seq = U_test[:24].copy()

    # Load FIRMS active fires if available
    fires_df = pd.DataFrame()
    if firms_path.exists():
        fires_df = pd.read_csv(firms_path)
    elif Path("data/raw/firms/firms_demo_2026.csv").exists():
        fires_df = pd.read_csv(Path("data/raw/firms/firms_demo_2026.csv"))

    # Ensure required output directories exist
    Path("models/artifacts/attribution").mkdir(parents=True, exist_ok=True)
    Path("models/artifacts/control").mkdir(parents=True, exist_ok=True)
    Path("reports/attribution").mkdir(parents=True, exist_ok=True)
    Path("reports/control").mkdir(parents=True, exist_ok=True)

    # ---------------------------------------------------------------------
    # System 1: Source Attribution & Regional Plume Clock
    # ---------------------------------------------------------------------
    print("\n[1/4] Running Source Attribution & Plume Arrival Engine...")
    t0_attr = time.perf_counter()
    attr_engine = SourceAttributionEngine(model, preprocessor)
    attr_result = attr_engine.analyze(
        x0_physical=x0,
        u_sequence_physical=u_seq,
        fires_df=fires_df,
        u_wind=-2.5,
        v_wind=-1.8,
        horizon=24
    )
    attr_latency_ms = (time.perf_counter() - t0_attr) * 1000.0

    print(f"  -> Dominant Sector: {attr_result.dominant_sector} ({attr_result.dominant_sector_percentage}%)")
    print(f"  -> Local / Regional / Background: {attr_result.regional_breakdown.local_percentage}% / "
          f"{attr_result.regional_breakdown.regional_percentage}% / {attr_result.regional_breakdown.background_percentage}%")
    print(f"  -> Plume Clusters Tracked: {len(attr_result.plume_estimates)}")
    print(f"  -> Execution Latency: {attr_latency_ms:.2f} ms")

    # Serialize sector contributions
    sector_df = pd.DataFrame([
        {
            "sector": sec,
            "delta_pm25_ug_m3": item.delta_pm25,
            "delta_pm10_ug_m3": item.delta_pm10,
            "delta_o3_ug_m3": item.delta_o3,
            "percentage_contribution": item.percentage_pm25,
            "provenance": item.provenance.value
        }
        for sec, item in attr_result.sector_contributions.items()
    ])
    sector_df.to_parquet("reports/attribution/sector_contributions.parquet", index=False)

    # Serialize fire clusters / plume clock
    fire_records = [p.model_dump() for p in attr_result.plume_estimates]
    if fire_records:
        fire_df = pd.DataFrame(fire_records)
        fire_df.to_parquet("reports/attribution/fire_attribution.parquet", index=False)

    with open("models/artifacts/attribution/attribution_model.json", "w", encoding="utf-8") as f:
        json.dump(attr_result.model_dump(), f, indent=2)

    # ---------------------------------------------------------------------
    # System 2: Counterfactual What-If Scenarios
    # ---------------------------------------------------------------------
    print("\n[2/4] Running Counterfactual What-If Simulations...")
    cf_engine = CounterfactualEngine(model, preprocessor)
    sample_perts = [
        SourcePerturbation(
            sector=AttributionSector.ROAD_TRANSPORT.value,
            baseline_value=1.0,
            perturbation_fraction=-0.25,  # 25% traffic reduction
            perturbed_value=0.75
        ),
        SourcePerturbation(
            sector=AttributionSector.AGRICULTURE.value,
            baseline_value=1.0,
            perturbation_fraction=-0.40,  # 40% stubble burning suppression
            perturbed_value=0.60
        )
    ]
    cf_result = cf_engine.simulate(x0, u_seq, sample_perts, horizon=24)
    print(f"  -> Peak PM2.5 Reduction: {cf_result['peak_pm25_reduction']} ug/m3")
    print(f"  -> Peak AQI Reduction: {cf_result['peak_aqi_reduction']} points")
    print(f"  -> Category Shift: {cf_result['final_baseline_category']} -> {cf_result['final_counterfactual_category']}")

    cf_timeline_df = pd.DataFrame(cf_result["hourly_timeline"])
    cf_timeline_df.to_parquet("reports/attribution/counterfactual_results.parquet", index=False)

    # ---------------------------------------------------------------------
    # System 3: Explainability / "Why AQI Rises" Engine
    # ---------------------------------------------------------------------
    print("\n[3/4] Diagnosing Air Quality Degradation Mechanisms...")
    why_engine = WhyAQIRisesEngine(preprocessor.state_vars, preprocessor.control_vars)
    # Forward simulation for baseline
    rollout_res = attr_engine.rollout_engine.forecast(
        x0, u_seq[0], horizon=24, actual_future_U=u_seq
    )
    base_traj = rollout_res["trajectory_matrix"]
    why_result = why_engine.diagnose(
        initial_state=x0,
        forecast_trajectory=base_traj,
        control_trajectory=u_seq,
        initial_aqi=cf_result["baseline_initial_aqi"],
        final_aqi=cf_result["baseline_final_aqi"]
    )
    print(f"  -> Dominant Driver: {why_result.dominant_driver}")
    for d in why_result.driver_scores[:3]:
        print(f"     - {d.display_title}: Score {d.score}/100 ({d.evidence})")

    # ---------------------------------------------------------------------
    # System 4: Model Predictive Control (MPC) Engine
    # ---------------------------------------------------------------------
    print("\n[4/4] Executing Model Predictive Control Optimization...")
    mpc = MPCController(model, preprocessor, uncertainty_engine)

    # 1. Compute control sensitivities
    sensitivities = mpc.compute_control_sensitivities(x0, u_seq, horizon=24)
    with open("reports/control/control_sensitivity.json", "w", encoding="utf-8") as f:
        json.dump(sensitivities, f, indent=2)
    print("  -> Control Sensitivities:")
    for s in sensitivities[:3]:
        print(f"     * {s['display_name']}: Efficiency {s['cost_efficiency_score']} "
              f"(Sensitivity: {s['sensitivity_ug_m3_per_unit']:.3f} ug/m3 per unit)")

    # 2. Benchmark three policy strategies
    print("\n  -> Comparing Policy Strategies (LOW_COST vs. BALANCED vs. AGGRESSIVE):")
    t0_mpc = time.perf_counter()
    strategy_comparison = mpc.compare_strategies(x0, u_seq, horizon=24)
    mpc_latency_ms = (time.perf_counter() - t0_mpc) * 1000.0

    for strat_key, strat_data in strategy_comparison["strategies"].items():
        print(f"     [{strat_key:10s}] Peak PM2.5: {strat_data['peak_pm25']} ug/m3 | "
              f"Peak AQI: {strat_data['peak_aqi']} | Rel Cost: {strat_data['relative_cost']}")

    # 3. Target-based optimization
    target_res = mpc.optimize_target(x0, u_seq, target_aqi=300.0, deadline_hours=24)
    print(f"\n  -> Target Optimization (Target AQI <= 300 in 24h): {target_res['feasibility_status']}")
    if target_res["feasibility_status"] == "FEASIBLE":
        print(f"     * Selected Strategy: {target_res.get('minimum_cost_strategy')}")
        print(f"     * Relative Cost: {target_res['relative_cost']}")

    # 4. Intervention narrative explanation
    balanced_sol = mpc.optimize_policy(x0, u_seq, strategy=PolicyStrategy.BALANCED, horizon=24)
    explanation = mpc.explain_intervention(balanced_sol, sensitivities, why_result.dominant_driver)
    print(f"\n  -> Decision Explanation:\n     {explanation}")

    # Serialize MPC artifacts
    mpc_policy_df = pd.DataFrame(balanced_sol["hourly_timeline"])
    mpc_policy_df.to_parquet("reports/control/mpc_policy_results.parquet", index=False)

    mpc_config_summary = {
        "framework": "Model Predictive Control (SLSQP / DMDc Linear System)",
        "horizon_hours": 24,
        "controllable_sectors": mpc.mapper.sectors,
        "lever_definitions": {k: v.model_dump() for k, v in mpc.mapper.LEVER_DEFINITIONS.items()},
        "tested_target_optimization": target_res,
        "provenance": ProvenanceType.SCENARIO.value
    }
    with open("models/artifacts/control/mpc_config.json", "w", encoding="utf-8") as f:
        json.dump(mpc_config_summary, f, indent=2)

    print("\n" + "=" * 70)
    print("PHASE 4 PIPELINE COMPLETED SUCCESSFULLY")
    print("=" * 70)


if __name__ == "__main__":
    run_phase4()
