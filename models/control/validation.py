"""
Algorithmic Validation Suite for Model Predictive Control (MPC) Optimization
"""
from typing import Dict, Any
import numpy as np


class MPCValidator:
    """
    Validates MPC mathematical properties and constraint enforcement:
    1. Zero-action equivalence: theta = 0 must exactly equal baseline trajectory
    2. Constraint compliance: theta must strictly satisfy 0 <= theta <= theta_max
    3. Cost monotonicity: higher abatement must produce greater or equal intervention cost
    4. Model linear propagation: predicted states must originate from A x + B u
    """

    @staticmethod
    def test_zero_action_equivalence(base_traj: np.ndarray, zero_action_traj: np.ndarray) -> Dict[str, Any]:
        """Verifies that applying zero abatement produces exactly the baseline forecast."""
        diff = float(np.max(np.abs(base_traj - zero_action_traj)))
        passed = diff < 1e-6
        return {
            "test_name": "zero_action_equivalence",
            "passed": bool(passed),
            "max_absolute_difference": diff
        }

    @staticmethod
    def test_constraint_compliance(theta_matrix: np.ndarray, bounds: list) -> Dict[str, Any]:
        """Verifies that all optimal theta values strictly adhere to box bounds."""
        H, S = theta_matrix.shape
        flat = theta_matrix.flatten()
        
        violations = 0
        for i, val in enumerate(flat):
            low, high = bounds[i]
            if val < (low - 1e-5) or val > (high + 1e-5):
                violations += 1

        passed = (violations == 0)
        return {
            "test_name": "constraint_compliance",
            "passed": bool(passed),
            "violations_count": violations
        }

    @staticmethod
    def test_cost_monotonicity(theta_small: np.ndarray, theta_large: np.ndarray, cost_weights: np.ndarray) -> Dict[str, Any]:
        """Verifies that greater abatement yields strictly greater intervention cost."""
        cost_small = float(np.sum(theta_small @ cost_weights))
        cost_large = float(np.sum(theta_large @ cost_weights))
        passed = (cost_large >= cost_small)

        return {
            "test_name": "cost_monotonicity",
            "passed": bool(passed),
            "cost_small": cost_small,
            "cost_large": cost_large
        }
