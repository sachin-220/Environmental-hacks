"""
Counterfactual Simulation Engine for Policy Interventions and What-If Scenarios
"""
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd

from config.logging_config import get_logger
from models.dmdc.dmdc_model import DMDcModel
from models.dmdc.preprocessing import DMDcPreprocessor
from models.dmdc.rollout import DMDcRolloutEngine, ForecastInputMode
from models.dmdc.aqi import NationalAQICalculator
from models.attribution.attribution_schema import (
    SourcePerturbation,
    ProvenanceType
)
from models.attribution.sector_attribution import SectorAttributionEngine

logger = get_logger("models.attribution.counterfactual")


class CounterfactualEngine:
    """
    Simulates multi-sector and single-source counterfactual policy interventions.
    Evaluates:
        x_baseline(t+h) vs. x_counterfactual(t+h)
    and computes reductions across PM2.5, PM10, O3, NO2, and Indian National AQI (NAQI).
    """

    def __init__(self, model: DMDcModel, preprocessor: DMDcPreprocessor):
        self.model = model
        self.preprocessor = preprocessor
        self.rollout_engine = DMDcRolloutEngine(model, preprocessor)
        self.sector_engine = SectorAttributionEngine(model, preprocessor)

        self.state_vars = self.preprocessor.state_vars
        self.control_vars = self.preprocessor.control_vars

    def simulate(
        self,
        x0_physical: np.ndarray,
        u_sequence_physical: np.ndarray,
        perturbations: List[SourcePerturbation],
        horizon: int = 24
    ) -> Dict[str, Any]:
        """
        Runs parallel baseline and counterfactual rollouts under the specified perturbations.
        Returns trajectories, pollutant differentials, and NAQI category shifts.
        """
        # 1. Baseline rollout
        base_rollout = self.rollout_engine.forecast(
            x0_physical=x0_physical,
            u0_physical=u_sequence_physical[0],
            horizon=horizon,
            mode=ForecastInputMode.RETROSPECTIVE,
            actual_future_U=u_sequence_physical,
            apply_physical_bounds=True
        )
        base_traj = base_rollout["trajectory_matrix"]

        # 2. Build perturbed control sequence
        u_pert = u_sequence_physical[:horizon].copy()
        for pert in perturbations:
            # Fraction: e.g. -0.20 means 20% reduction
            reduction_frac = abs(pert.perturbation_fraction)
            for h in range(horizon):
                delta_u = self.sector_engine.get_sectoral_reduction_vector(
                    sector=pert.sector,
                    reduction_fraction=reduction_frac,
                    baseline_u=u_pert[h]
                )
                # Positive reduction fraction (e.g. 0.30) represents 30% abatement
                u_pert[h] = np.maximum(0.0, u_pert[h] - delta_u)

        # 3. Counterfactual rollout
        pert_rollout = self.rollout_engine.forecast(
            x0_physical=x0_physical,
            u0_physical=u_pert[0],
            horizon=horizon,
            mode=ForecastInputMode.RETROSPECTIVE,
            actual_future_U=u_pert,
            apply_physical_bounds=True
        )
        pert_traj = pert_rollout["trajectory_matrix"]

        # Indices
        pm25_idx = self.state_vars.index("pm25") if "pm25" in self.state_vars else 0
        pm10_idx = self.state_vars.index("pm10") if "pm10" in self.state_vars else 1
        o3_idx = self.state_vars.index("o3") if "o3" in self.state_vars else 2
        no2_idx = self.state_vars.index("no2") if "no2" in self.state_vars else 3

        # 4. Hourly trajectory comparison
        hourly_records = []
        for h in range(horizon):
            b_pm25 = float(base_traj[h, pm25_idx])
            p_pm25 = float(pert_traj[h, pm25_idx])

            b_pm10 = float(base_traj[h, pm10_idx])
            p_pm10 = float(pert_traj[h, pm10_idx])

            b_o3 = float(base_traj[h, o3_idx])
            p_o3 = float(pert_traj[h, o3_idx])

            b_no2 = float(base_traj[h, no2_idx])
            p_no2 = float(pert_traj[h, no2_idx])

            # Calculate CPCB NAQI for both
            base_aqi_eval = NationalAQICalculator.evaluate_aqi({
                "pm25": b_pm25, "pm10": b_pm10, "o3": b_o3, "no2": b_no2
            })
            pert_aqi_eval = NationalAQICalculator.evaluate_aqi({
                "pm25": p_pm25, "pm10": p_pm10, "o3": p_o3, "no2": p_no2
            })

            delta_pm25 = round(b_pm25 - p_pm25, 3)
            delta_aqi = round(base_aqi_eval["aqi"] - pert_aqi_eval["aqi"], 1)

            hourly_records.append({
                "hour": h + 1,
                "baseline_pm25": round(b_pm25, 2),
                "counterfactual_pm25": round(p_pm25, 2),
                "delta_pm25": delta_pm25,
                "baseline_aqi": base_aqi_eval["aqi"],
                "counterfactual_aqi": pert_aqi_eval["aqi"],
                "delta_aqi": delta_aqi,
                "baseline_category": base_aqi_eval["category"],
                "counterfactual_category": pert_aqi_eval["category"],
                "dominant_pollutant": pert_aqi_eval["dominant_pollutant"]
            })

        # Summary statistics
        deltas_pm25 = [r["delta_pm25"] for r in hourly_records]
        deltas_aqi = [r["delta_aqi"] for r in hourly_records]

        summary = {
            "horizon_hours": horizon,
            "perturbations": [p.model_dump() for p in perturbations],
            "peak_pm25_reduction": round(float(np.max(deltas_pm25)), 2),
            "mean_pm25_reduction": round(float(np.mean(deltas_pm25)), 2),
            "final_pm25_reduction": round(deltas_pm25[-1], 2),
            "peak_aqi_reduction": round(float(np.max(deltas_aqi)), 1),
            "final_aqi_reduction": round(deltas_aqi[-1], 1),
            "baseline_initial_aqi": hourly_records[0]["baseline_aqi"],
            "baseline_final_aqi": hourly_records[-1]["baseline_aqi"],
            "counterfactual_final_aqi": hourly_records[-1]["counterfactual_aqi"],
            "initial_category": hourly_records[0]["baseline_category"],
            "final_baseline_category": hourly_records[-1]["baseline_category"],
            "final_counterfactual_category": hourly_records[-1]["counterfactual_category"],
            "hourly_timeline": hourly_records,
            "provenance": ProvenanceType.COUNTERFACTUAL.value
        }
        return summary
