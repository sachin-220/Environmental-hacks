"""
Constrained Optimization Solver for Model Predictive Control (DMDc Dynamics + SLSQP)
"""
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import scipy.optimize as opt

from config.logging_config import get_logger
from models.dmdc.dmdc_model import DMDcModel
from models.dmdc.preprocessing import DMDcPreprocessor
from models.dmdc.rollout import DMDcRolloutEngine
from models.control.control_variables import MPCControlMapper
from models.control.constraints import MPCConstraintManager
from models.control.objectives import MPCObjectiveManager
from models.control.scenarios import PolicyStrategyConfig

logger = get_logger("models.control.optimizer")


class MPCOptimizer:
    """
    Solves the constrained Model Predictive Control problem:
        min_Theta J(Theta)
        subject to:
            x_(k+1) = A_rollout x_k + B_rollout (u_base,k - M(u_base,k) * theta_k) + c_rollout
            0 <= theta_(s, k) <= max_feas_s
    Uses scipy.optimize.minimize (SLSQP) for fast, robust constrained non-linear optimization.
    """

    def __init__(
        self,
        model: DMDcModel,
        preprocessor: DMDcPreprocessor,
        mapper: MPCControlMapper
    ):
        self.model = model
        self.preprocessor = preprocessor
        self.mapper = mapper
        self.rollout_engine = DMDcRolloutEngine(self.model, self.preprocessor)

        self.state_vars = self.preprocessor.state_vars
        self.control_vars = self.preprocessor.control_vars
        self.n_states = len(self.state_vars)
        self.n_controls = len(self.control_vars)
        self.n_sectors = self.mapper.n_sectors

        self.pm25_idx = self.state_vars.index("pm25") if "pm25" in self.state_vars else 0

    def simulate_controlled_rollout(
        self,
        x0_physical: np.ndarray,
        u_sequence_physical: np.ndarray,
        theta_matrix: np.ndarray  # (H, S)
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Simulates the forward trajectory under intervention theta:
        Returns:
            X_physical: (H, n)
            U_perturbed: (H, m)
        """
        horizon = len(theta_matrix)
        u_pert = u_sequence_physical[:horizon].copy()

        # Apply sectoral perturbations to control inputs
        for h in range(horizon):
            d_u = self.mapper.compute_control_perturbation(theta_matrix[h], u_pert[h])
            u_pert[h] = np.maximum(0.0, u_pert[h] - d_u)

        # Forward recursive linear propagation using coupled atmospheric Koopman operator
        traj_phys = np.zeros((horizon, self.n_states), dtype=np.float64)
        curr_x = x0_physical.astype(np.float64).copy()

        A_roll = self.rollout_engine.A_rollout
        B_roll = self.rollout_engine.B_rollout
        c_roll = self.rollout_engine.c_rollout

        for h in range(horizon):
            curr_x = (A_roll @ curr_x) + (B_roll @ u_pert[h]) + c_roll
            traj_phys[h] = curr_x.copy()

        # Apply physical non-negativity bounds
        traj_phys[:, self.pm25_idx] = np.maximum(0.0, traj_phys[:, self.pm25_idx])

        return traj_phys, u_pert

    def solve(
        self,
        x0_physical: np.ndarray,
        u_sequence_physical: np.ndarray,
        strategy_config: PolicyStrategyConfig,
        horizon: int = 24,
        target_pm25: float = 60.0,
        max_iterations: int = 50
    ) -> Dict[str, Any]:
        """
        Executes constrained SLSQP optimization over sectoral abatement matrix theta.
        """
        H = horizon
        S = self.n_sectors

        constraint_mgr = MPCConstraintManager(self.mapper)
        bounds = constraint_mgr.get_bounds_flat(
            horizon=H,
            strategy_multiplier=strategy_config.feasibility_multiplier
        )

        obj_mgr = MPCObjectiveManager(
            mapper=self.mapper,
            weight_pollution=strategy_config.weight_pollution,
            weight_cost=strategy_config.weight_cost,
            weight_smoothness=strategy_config.weight_smoothness,
            target_pm25=target_pm25
        )

        # Objective function wrapper
        def objective_func(theta_flat: np.ndarray) -> float:
            theta_mat = theta_flat.reshape((H, S))
            traj_phys, _ = self.simulate_controlled_rollout(x0_physical, u_sequence_physical, theta_mat)
            pm25_seq = traj_phys[:, self.pm25_idx]
            cost_eval = obj_mgr.evaluate_cost(pm25_seq, theta_mat)
            return cost_eval["total_loss"]

        # Initial guess: start from modest 5% uniform intervention
        theta_init = np.full(H * S, 0.05, dtype=np.float64)
        # Clip to bounds
        for i, (b_low, b_high) in enumerate(bounds):
            theta_init[i] = np.clip(theta_init[i], b_low, b_high)

        # Run SLSQP optimization
        res = opt.minimize(
            objective_func,
            theta_init,
            method="SLSQP",
            bounds=bounds,
            options={"maxiter": max_iterations, "ftol": 1e-4, "disp": False}
        )

        optimal_theta_mat = res.x.reshape((H, S))

        # Final forward evaluation under optimal controls
        opt_traj_phys, opt_u_phys = self.simulate_controlled_rollout(
            x0_physical, u_sequence_physical, optimal_theta_mat
        )
        base_traj_phys, _ = self.simulate_controlled_rollout(
            x0_physical, u_sequence_physical, np.zeros((H, S))
        )

        cost_breakdown = obj_mgr.evaluate_cost(opt_traj_phys[:, self.pm25_idx], optimal_theta_mat)

        return {
            "success": bool(res.success),
            "status_message": str(res.message),
            "iterations": int(res.nit) if hasattr(res, "nit") else max_iterations,
            "optimal_theta_matrix": optimal_theta_mat,
            "baseline_trajectory": base_traj_phys,
            "optimized_trajectory": opt_traj_phys,
            "optimized_control_sequence": opt_u_phys,
            "cost_breakdown": cost_breakdown
        }
