"""
MPC Constraints Engine: Sector Feasibility, Ramp Rates, and Physical Bounding Limits
"""
from typing import Dict, Any, List, Tuple, Optional
import numpy as np
from pydantic import BaseModel, Field

from models.attribution.attribution_schema import ProvenanceType
from models.control.control_variables import MPCControlMapper


class MPCConstraintConfig(BaseModel):
    """Configuration for operational MPC optimization constraints"""
    max_ramp_rate_per_hour: float = Field(
        default=0.15,
        ge=0.01,
        le=0.50,
        description="Maximum fractional change in control allowed per 1 hour (ramp limit)"
    )
    enforce_ramp_constraints: bool = Field(default=True)
    enforce_physical_state_bounds: bool = Field(default=True)
    provenance: ProvenanceType = Field(default=ProvenanceType.SCENARIO)


class MPCConstraintManager:
    """
    Constructs and enforces box bounds and operational constraints for SLSQP optimization:
    1. Lower / upper box bounds: 0.0 <= theta_(s, k) <= max_feasible_reduction_s
    2. Ramp-rate limits: |theta_(s, k) - theta_(s, k-1)| <= max_ramp_rate
    """

    def __init__(
        self,
        mapper: MPCControlMapper,
        config: Optional[MPCConstraintConfig] = None
    ):
        self.mapper = mapper
        self.config = config or MPCConstraintConfig()
        self.sectors = self.mapper.sectors
        self.n_sectors = len(self.sectors)

    def get_bounds_flat(self, horizon: int, strategy_multiplier: float = 1.0) -> List[Tuple[float, float]]:
        """
        Returns list of (lower, upper) bounds for flattened optimization vector
        theta_flat in R^(horizon * n_sectors).
        """
        bounds = []
        for h in range(horizon):
            for sec in self.sectors:
                lever = self.mapper.LEVER_DEFINITIONS[sec]
                max_feas = min(1.0, lever.max_feasible_reduction * strategy_multiplier)
                bounds.append((0.0, max_feas))
        return bounds

    def compute_ramp_penalty(self, theta_matrix: np.ndarray) -> float:
        """
        Evaluates smoothness penalty on rate-of-change across time steps.
        theta_matrix: shape (horizon, n_sectors).
        """
        if len(theta_matrix) < 2:
            return 0.0
        diffs = np.diff(theta_matrix, axis=0)  # (H-1, S)
        return float(np.sum(diffs**2))
