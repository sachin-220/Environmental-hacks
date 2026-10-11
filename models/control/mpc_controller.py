"""
Model Predictive Control (MPC) Controller for Automated Air Pollution Abatement
"""
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import numpy as np
import pandas as pd

from config.logging_config import get_logger
from models.dmdc.dmdc_model import DMDcModel
from models.dmdc.preprocessing import DMDcPreprocessor
from models.dmdc.aqi import NationalAQICalculator
from models.dmdc.uncertainty import DMDcUncertaintyEngine
from models.attribution.attribution_schema import ProvenanceType
from models.control.control_variables import MPCControlMapper, ControlSector
from models.control.scenarios import PolicyStrategy, MPCScenarioManager, PolicyStrategyConfig
from models.control.optimizer import MPCOptimizer

logger = get_logger("models.control.mpc_controller")


class MPCController:
    """
    SAMEER Model Predictive Control (MPC) Engine.
    Solves for cost-optimal, constrained emission abatement trajectories to minimize ambient AQI spikes:
        min sum [ w_poll * Pollution + w_cost * Cost + w_smooth * Smoothness ]
    subject to:
        x_(k+1) = A x_k + B u_k
        0 <= theta_(s, k) <= max_feas_s
    """

    def __init__(
        self,
        model: DMDcModel,
        preprocessor: DMDcPreprocessor,
        uncertainty_engine: Optional[DMDcUncertaintyEngine] = None
    ):
        self.model = model
        self.preprocessor = preprocessor
        self.uncertainty_engine = uncertainty_engine

        self.control_vars = self.preprocessor.control_vars
        self.state_vars = self.preprocessor.state_vars
        self.pm25_idx = self.state_vars.index("pm25") if "pm25" in self.state_vars else 0

        self.mapper = MPCControlMapper(self.control_vars)
        self.optimizer = MPCOptimizer(self.model, self.preprocessor, self.mapper)

    def optimize_policy(
        self,
        x0_physical: np.ndarray,
        u_sequence_physical: np.ndarray,
        strategy: PolicyStrategy = PolicyStrategy.BALANCED,
        horizon: int = 24,
        target_pm25: float = 60.0,
        timestamp: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes policy optimization for a specified strategy (LOW_COST, BALANCED, AGGRESSIVE).
        """
        strat_cfg = MPCScenarioManager.get_config(strategy)

        opt_res = self.optimizer.solve(
            x0_physical=x0_physical,
            u_sequence_physical=u_sequence_physical,
            strategy_config=strat_cfg,
            horizon=horizon,
            target_pm25=target_pm25
        )

        base_traj = opt_res["baseline_trajectory"]
        opt_traj = opt_res["optimized_trajectory"]
        theta_mat = opt_res["optimal_theta_matrix"]  # (H, S)

        # Compute hourly comparisons and AQI
        hourly_records = []
        for h in range(horizon):
            b_pm25 = float(base_traj[h, self.pm25_idx])
            o_pm25 = float(opt_traj[h, self.pm25_idx])

            b_aqi_eval = NationalAQICalculator.evaluate_aqi({"pm25": b_pm25})
            o_aqi_eval = NationalAQICalculator.evaluate_aqi({"pm25": o_pm25})

            d_pm25 = round(b_pm25 - o_pm25, 2)
            d_aqi = round(b_aqi_eval["aqi"] - o_aqi_eval["aqi"], 1)

            step_actions = {
                sec: round(float(theta_mat[h, s_idx]) * 100.0, 1)
                for s_idx, sec in enumerate(self.mapper.sectors)
            }

            hourly_records.append({
                "hour": h + 1,
                "baseline_pm25": round(b_pm25, 2),
                "optimized_pm25": round(o_pm25, 2),
                "delta_pm25": d_pm25,
                "baseline_aqi": b_aqi_eval["aqi"],
                "optimized_aqi": o_aqi_eval["aqi"],
                "delta_aqi": d_aqi,
                "baseline_category": b_aqi_eval["category"],
                "optimized_category": o_aqi_eval["category"],
                "recommended_abatement_percentages": step_actions
            })

        # Mean sector efforts over the window
        mean_efforts = {
            sec: round(float(np.mean(theta_mat[:, s_idx])) * 100.0, 1)
            for s_idx, sec in enumerate(self.mapper.sectors)
        }

        # Peak and final impacts
        deltas_pm25 = [r["delta_pm25"] for r in hourly_records]
        deltas_aqi = [r["delta_aqi"] for r in hourly_records]

        return {
            "strategy": strategy.value,
            "strategy_title": strat_cfg.display_title,
            "horizon_hours": horizon,
            "optimization_success": opt_res["success"],
            "iterations": opt_res["iterations"],
            "baseline_peak_pm25": round(float(np.max(base_traj[:, self.pm25_idx])), 2),
            "optimized_peak_pm25": round(float(np.max(opt_traj[:, self.pm25_idx])), 2),
            "peak_pm25_reduction": round(float(np.max(deltas_pm25)), 2),
            "mean_pm25_reduction": round(float(np.mean(deltas_pm25)), 2),
            "peak_aqi_reduction": round(float(np.max(deltas_aqi)), 1),
            "relative_intervention_cost": opt_res["cost_breakdown"]["relative_intervention_cost"],
            "mean_sector_abatement_percentages": mean_efforts,
            "hourly_timeline": hourly_records,
            "trajectory_comparison": hourly_records,
            "provenance": ProvenanceType.SCENARIO.value
        }

    def optimize_target(
        self,
        x0_physical: np.ndarray,
        u_sequence_physical: np.ndarray,
        target_aqi: float = 300.0,
        deadline_hours: int = 24
    ) -> Dict[str, Any]:
        """
        Target-based optimization:
        Finds minimum-cost intervention to achieve AQI <= target_aqi within deadline_hours.
        Returns feasibility status: FEASIBLE, INFEASIBLE, or UNCERTAIN.
        """
        # Convert AQI target to PM2.5 target threshold using CPCB inverse lookup
        target_pm25 = 120.0 if target_aqi <= 300 else (250.0 if target_aqi <= 400 else 60.0)

        # 1. Evaluate baseline without action
        base_traj, _ = self.optimizer.simulate_controlled_rollout(
            x0_physical, u_sequence_physical, np.zeros((deadline_hours, self.mapper.n_sectors))
        )
        base_pm25_peak = float(np.max(base_traj[:, self.pm25_idx]))
        base_aqi_peak = NationalAQICalculator.evaluate_aqi({"pm25": base_pm25_peak})["aqi"]

        if base_aqi_peak <= target_aqi:
            # Generate baseline trajectory comparison
            base_records = []
            for h in range(deadline_hours):
                b_pm = float(base_traj[h, self.pm25_idx])
                b_eval = NationalAQICalculator.evaluate_aqi({"pm25": b_pm})
                base_records.append({
                    "hour": h + 1,
                    "baseline_pm25": round(b_pm, 2),
                    "optimized_pm25": round(b_pm, 2),
                    "delta_pm25": 0.0,
                    "baseline_aqi": b_eval["aqi"],
                    "optimized_aqi": b_eval["aqi"],
                    "delta_aqi": 0.0,
                    "baseline_category": b_eval["category"],
                    "optimized_category": b_eval["category"],
                    "recommended_abatement_percentages": {s: 0.0 for s in self.mapper.sectors}
                })
            return {
                "feasibility_status": "FEASIBLE",
                "message": "Baseline trajectory already satisfies target without intervention.",
                "target_aqi": target_aqi,
                "deadline_hours": deadline_hours,
                "baseline_peak_aqi": base_aqi_peak,
                "optimized_peak_aqi": base_aqi_peak,
                "relative_cost": 0.0,
                "recommended_controls": {s: 0.0 for s in self.mapper.sectors},
                "start_hour": 1,
                "hourly_timeline": base_records,
                "trajectory_comparison": base_records,
                "provenance": ProvenanceType.SCENARIO.value
            }

        # 2. Test Low-Cost, Balanced, and Aggressive to find minimum-cost feasible solution
        for strat in [PolicyStrategy.LOW_COST, PolicyStrategy.BALANCED, PolicyStrategy.AGGRESSIVE]:
            sol = self.optimize_policy(
                x0_physical=x0_physical,
                u_sequence_physical=u_sequence_physical,
                strategy=strat,
                horizon=deadline_hours,
                target_pm25=target_pm25
            )
            opt_peak_aqi = float(np.max([r["optimized_aqi"] for r in sol["hourly_timeline"]]))
            if opt_peak_aqi <= target_aqi:
                return {
                    "feasibility_status": "FEASIBLE",
                    "minimum_cost_strategy": strat.value,
                    "target_aqi": target_aqi,
                    "deadline_hours": deadline_hours,
                    "baseline_peak_aqi": base_aqi_peak,
                    "optimized_peak_aqi": opt_peak_aqi,
                    "relative_cost": sol["relative_intervention_cost"],
                    "recommended_controls": sol["mean_sector_abatement_percentages"],
                    "start_hour": 1,
                    "hourly_timeline": sol["hourly_timeline"],
                    "trajectory_comparison": sol["hourly_timeline"],
                    "provenance": ProvenanceType.SCENARIO.value
                }

        # If even Aggressive fails to meet target
        agg_sol = self.optimize_policy(
            x0_physical=x0_physical,
            u_sequence_physical=u_sequence_physical,
            strategy=PolicyStrategy.AGGRESSIVE,
            horizon=deadline_hours,
            target_pm25=target_pm25
        )
        agg_peak_aqi = float(np.max([r["optimized_aqi"] for r in agg_sol["hourly_timeline"]]))

        return {
            "feasibility_status": "INFEASIBLE",
            "message": f"Target AQI {target_aqi} cannot be fully satisfied within {deadline_hours}h even under Aggressive GRAP-IV emergency bounds.",
            "target_aqi": target_aqi,
            "deadline_hours": deadline_hours,
            "baseline_peak_aqi": base_aqi_peak,
            "best_achievable_peak_aqi": agg_peak_aqi,
            "relative_cost": agg_sol["relative_intervention_cost"],
            "recommended_controls": agg_sol["mean_sector_abatement_percentages"],
            "hourly_timeline": agg_sol["hourly_timeline"],
            "trajectory_comparison": agg_sol["hourly_timeline"],
            "provenance": ProvenanceType.SCENARIO.value
        }

    def compute_control_sensitivities(
        self,
        x0_physical: np.ndarray,
        u_sequence_physical: np.ndarray,
        horizon: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Calculates the sensitivity d(PM2.5) / d(theta_s) for each candidate sector.
        Derived directly from DMDc forward model response under marginal 10% perturbations.
        """
        sensitivities = []

        base_traj, _ = self.optimizer.simulate_controlled_rollout(
            x0_physical, u_sequence_physical, np.zeros((horizon, self.mapper.n_sectors))
        )
        base_pm25_mean = float(np.mean(base_traj[:, self.pm25_idx]))

        for s_idx, sec in enumerate(self.mapper.sectors):
            theta_pert = np.zeros((horizon, self.mapper.n_sectors))
            theta_pert[:, s_idx] = 0.10  # 10% test reduction

            pert_traj, _ = self.optimizer.simulate_controlled_rollout(
                x0_physical, u_sequence_physical, theta_pert
            )
            pert_pm25_mean = float(np.mean(pert_traj[:, self.pm25_idx]))

            # Sensitivity = delta PM2.5 / delta theta
            delta_pm25 = base_pm25_mean - pert_pm25_mean
            sensitivity = delta_pm25 / 0.10  # ug/m3 per unit abatement fraction

            cost_w = self.mapper.LEVER_DEFINITIONS[sec].relative_cost_weight
            efficiency = sensitivity / cost_w  # reduction per unit cost

            sensitivities.append({
                "sector": sec,
                "display_name": self.mapper.LEVER_DEFINITIONS[sec].display_name,
                "sensitivity_ug_m3_per_unit": round(sensitivity, 3),
                "relative_cost_weight": cost_w,
                "cost_efficiency_score": round(efficiency, 3),
                "provenance": ProvenanceType.MODELLED.value
            })

        # Rank by cost efficiency
        return sorted(sensitivities, key=lambda s: s["cost_efficiency_score"], reverse=True)

    def compare_strategies(
        self,
        x0_physical: np.ndarray,
        u_sequence_physical: np.ndarray,
        horizon: int = 24
    ) -> Dict[str, Any]:
        """
        Side-by-side comparative analysis of:
        NO_ACTION vs. LOW_COST vs. BALANCED vs. AGGRESSIVE.
        """
        # Baseline (No action)
        base_traj, _ = self.optimizer.simulate_controlled_rollout(
            x0_physical, u_sequence_physical, np.zeros((horizon, self.mapper.n_sectors))
        )
        base_pm25 = [round(float(v), 2) for v in base_traj[:, self.pm25_idx]]
        base_peak_aqi = NationalAQICalculator.evaluate_aqi({"pm25": float(np.max(base_pm25))})["aqi"]

        strategy_results = {
            "NO_ACTION": {
                "strategy_title": "No Intervention (Passive Baseline)",
                "peak_pm25": round(float(np.max(base_pm25)), 2),
                "mean_pm25": round(float(np.mean(base_pm25)), 2),
                "peak_aqi": base_peak_aqi,
                "relative_cost": 0.0,
                "pm25_trajectory": base_pm25
            }
        }

        for strat in [PolicyStrategy.LOW_COST, PolicyStrategy.BALANCED, PolicyStrategy.AGGRESSIVE]:
            sol = self.optimize_policy(
                x0_physical=x0_physical,
                u_sequence_physical=u_sequence_physical,
                strategy=strat,
                horizon=horizon
            )
            pm25_seq = [r["optimized_pm25"] for r in sol["hourly_timeline"]]
            strategy_results[strat.value] = {
                "strategy_title": sol["strategy_title"],
                "peak_pm25": sol["optimized_peak_pm25"],
                "mean_pm25": round(float(np.mean(pm25_seq)), 2),
                "peak_aqi": round(float(np.max([r["optimized_aqi"] for r in sol["hourly_timeline"]])), 1),
                "peak_aqi_reduction": sol["peak_aqi_reduction"],
                "relative_cost": sol["relative_intervention_cost"],
                "mean_abatement_percentages": sol["mean_sector_abatement_percentages"],
                "pm25_trajectory": pm25_seq
            }

        return {
            "horizon_hours": horizon,
            "strategies": strategy_results,
            "provenance": ProvenanceType.SCENARIO.value
        }

    def explain_intervention(
        self,
        policy_result: Dict[str, Any],
        sensitivities: List[Dict[str, Any]],
        dominant_driver: str
    ) -> str:
        """
        Generates clear, scientifically grounded narrative explaining why the specific
        intervention package was recommended by the MPC optimizer.
        """
        top_sec = max(
            policy_result["mean_sector_abatement_percentages"].keys(),
            key=lambda k: policy_result["mean_sector_abatement_percentages"][k]
        )
        top_pct = policy_result["mean_sector_abatement_percentages"][top_sec]

        most_efficient = sensitivities[0]["display_name"]

        explanation = (
            f"The MPC optimizer recommends a {policy_result['strategy_title']} strategy to mitigate "
            f"the forecast AQI surge primarily driven by {dominant_driver}. "
            f"The optimization prioritizes {most_efficient}, which achieves the highest modeled reduction "
            f"per unit intervention cost. The policy allocates an average of {top_pct}% reduction to {top_sec}, "
            f"projecting a peak PM2.5 reduction of {policy_result['peak_pm25_reduction']} ug/m³ "
            f"and an AQI improvement of {policy_result['peak_aqi_reduction']} points at a relative cost of {policy_result['relative_intervention_cost']}."
        )
        return explanation
