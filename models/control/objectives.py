"""
MPC Multi-Objective Cost Formulation Engine
"""
from typing import Dict, Any, List
import numpy as np

from models.control.control_variables import MPCControlMapper


class MPCObjectiveManager:
    """
    Formulates the multi-objective cost function:
        min J(Theta) = w_poll * J_pollution + w_cost * J_cost + w_smooth * J_smooth
    where:
        J_pollution = sum_{k=1}^H [ (PM2.5_k / PM2.5_target)^2 ]
        J_cost = sum_{k=1}^H sum_s [ c_s * theta_(s, k) ]  (RELATIVE INTERVENTION COST)
        J_smooth = sum_{k=2}^H sum_s [ (theta_(s, k) - theta_(s, k-1))^2 ]
    """

    def __init__(
        self,
        mapper: MPCControlMapper,
        weight_pollution: float = 2.0,
        weight_cost: float = 1.0,
        weight_smoothness: float = 0.5,
        target_pm25: float = 60.0  # CPCB National Ambient Air Quality Standard 24h limit
    ):
        self.mapper = mapper
        self.w_poll = weight_pollution
        self.w_cost = weight_cost
        self.w_smooth = weight_smoothness
        self.target_pm25 = max(1.0, target_pm25)

        # Vector of relative cost weights c_s in R^S
        self.cost_weights = np.array([
            self.mapper.LEVER_DEFINITIONS[sec].relative_cost_weight
            for sec in self.mapper.sectors
        ], dtype=np.float64)

    def evaluate_cost(
        self,
        pm25_trajectory: np.ndarray,      # (H,)
        theta_matrix: np.ndarray          # (H, S)
    ) -> Dict[str, float]:
        """
        Evaluates overall and component costs for a candidate intervention trajectory.
        """
        # 1. Pollution penalty (quadratic penalty for exceeding target)
        pm25_norm = pm25_trajectory / self.target_pm25
        j_poll = float(np.mean(pm25_norm**2))

        # 2. Intervention relative economic cost
        # theta_matrix is (H, S), cost_weights is (S,)
        step_costs = theta_matrix @ self.cost_weights  # (H,)
        j_cost = float(np.mean(step_costs))

        # 3. Smoothness penalty
        if len(theta_matrix) > 1:
            diffs = np.diff(theta_matrix, axis=0)
            j_smooth = float(np.mean(diffs**2))
        else:
            j_smooth = 0.0

        total_loss = (
            (self.w_poll * j_poll) +
            (self.w_cost * j_cost) +
            (self.w_smooth * j_smooth)
        )

        return {
            "total_loss": total_loss,
            "j_pollution": j_poll,
            "j_cost": j_cost,
            "j_smoothness": j_smooth,
            "relative_intervention_cost": round(float(np.sum(step_costs)), 2)
        }
