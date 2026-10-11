"""
Control Levers and Emission-to-Control Mapping Matrix for Model Predictive Control
"""
from typing import Dict, Any, List, Optional
from enum import Enum
import numpy as np
from pydantic import BaseModel, Field

from models.attribution.attribution_schema import ProvenanceType


class ControlSector(str, Enum):
    """Controllable emission sectors exposed to MPC optimization"""
    ROAD_TRANSPORT = "road_transport"
    INDUSTRY = "industry"
    POWER_PLANTS = "power_plants"
    AGRICULTURE = "agriculture"
    WASTE_BURNING = "waste_burning"
    RESIDENTIAL = "residential"


class ControlLeverDefinition(BaseModel):
    """Defines a single policy abatement lever and its affected control species"""
    sector: ControlSector
    display_name: str
    description: str
    max_feasible_reduction: float = Field(..., ge=0.0, le=1.0, description="Max realistic abatement fraction")
    relative_cost_weight: float = Field(..., gt=0.0, description="Normalized economic / societal cost per unit abatement")
    affected_species: List[str]
    provenance: ProvenanceType = Field(default=ProvenanceType.SCENARIO)


class MPCControlMapper:
    """
    Constructs the linear mapping matrix M in R^(m x S) translating sectoral
    abatement fractions theta in [0, 1]^S into physical control perturbations delta_u in R^m:
        u_k = u_baseline,k - M(u_baseline,k) * theta_k
    """

    # Sector policy feasibility definitions
    LEVER_DEFINITIONS: Dict[str, ControlLeverDefinition] = {
        ControlSector.ROAD_TRANSPORT.value: ControlLeverDefinition(
            sector=ControlSector.ROAD_TRANSPORT,
            display_name="Traffic Abatement (GRAP Odd-Even / EV Transit)",
            description="Vehicle restriction, public transit subsidization, zero-emission commercial entry",
            max_feasible_reduction=0.40,  # 40% max realistic reduction
            relative_cost_weight=1.0,     # Reference unit cost
            affected_species=["anthro_nox", "anthro_voc", "anthro_co", "anthro_so2"]
        ),
        ControlSector.INDUSTRY.value: ControlLeverDefinition(
            sector=ControlSector.INDUSTRY,
            display_name="Industrial Fuel Switching & Production Curbs",
            description="Shift to piped natural gas (PNG), temporary boiler throttling in industrial clusters",
            max_feasible_reduction=0.50,  # 50% max reduction
            relative_cost_weight=1.5,     # Higher economic impact per ton
            affected_species=["anthro_so2", "anthro_nox", "anthro_voc", "anthro_co"]
        ),
        ControlSector.POWER_PLANTS.value: ControlLeverDefinition(
            sector=ControlSector.POWER_PLANTS,
            display_name="Power Generation Re-dispatch / FGD Operation",
            description="Re-dispatch coal generation away from upwind NCR plants to hydro/renewables",
            max_feasible_reduction=0.35,  # 35% max grid re-dispatch
            relative_cost_weight=2.0,     # High cost for grid re-dispatch
            affected_species=["anthro_so2", "anthro_nox"]
        ),
        ControlSector.AGRICULTURE.value: ControlLeverDefinition(
            sector=ControlSector.AGRICULTURE,
            display_name="Stubble Fire In-Situ Mulching & Mechanized Suppression",
            description="Active enforcement and ex-situ biomass collection incentives in Punjab/Haryana",
            max_feasible_reduction=0.75,  # 75% max suppression with active flying squads
            relative_cost_weight=0.8,     # Relatively cost-effective per PM reduction
            affected_species=["fire_frp", "plume_transport_score"]
        ),
        ControlSector.WASTE_BURNING.value: ControlLeverDefinition(
            sector=ControlSector.WASTE_BURNING,
            display_name="Municipal Solid Waste Open Burning Night Patrols",
            description="Strict fire prevention at landfill sites (Ghazipur, Bhalswa, Okhla)",
            max_feasible_reduction=0.60,  # 60% open fire reduction
            relative_cost_weight=0.5,     # Low cost municipal enforcement
            affected_species=["anthro_co", "anthro_voc"]
        ),
        ControlSector.RESIDENTIAL.value: ControlLeverDefinition(
            sector=ControlSector.RESIDENTIAL,
            display_name="Residential Clean Cooking & Space Heating Fuel Subsidy",
            description="LPG cylinder distribution and electric heater provision for slum clusters",
            max_feasible_reduction=0.30,  # 30% reduction
            relative_cost_weight=0.7,     # Moderate subsidy cost
            affected_species=["anthro_co", "anthro_voc"]
        )
    }

    def __init__(self, control_vars: List[str]):
        self.control_vars = control_vars
        self.sectors = list(self.LEVER_DEFINITIONS.keys())
        self.n_controls = len(self.control_vars)
        self.n_sectors = len(self.sectors)

    def compute_control_perturbation(
        self,
        theta_vector: np.ndarray,
        baseline_u: np.ndarray
    ) -> np.ndarray:
        """
        Translates sector abatement vector theta in R^S into physical control reduction delta_u in R^m.
        delta_u_j = sum_s [ share(s, j) * baseline_u_j * theta_s ]
        """
        delta_u = np.zeros(self.n_controls, dtype=np.float64)

        for s_idx, sec_name in enumerate(self.sectors):
            theta_s = float(np.clip(theta_vector[s_idx], 0.0, 1.0))
            if theta_s <= 0.0:
                continue

            lever = self.LEVER_DEFINITIONS[sec_name]

            # Special case: Agricultural biomass burning controls
            if sec_name == ControlSector.AGRICULTURE.value:
                for var_name in ["fire_frp", "plume_transport_score"]:
                    if var_name in self.control_vars:
                        c_idx = self.control_vars.index(var_name)
                        delta_u[c_idx] += baseline_u[c_idx] * theta_s
                continue

            # Anthropogenic emission species shares
            for spec in lever.affected_species:
                if spec in self.control_vars:
                    c_idx = self.control_vars.index(spec)
                    # Use fractional weighting (e.g. transport is 42% NOx, 48% CO, etc.)
                    share = 0.35  # default baseline share
                    if spec == "anthro_nox" and sec_name == ControlSector.ROAD_TRANSPORT.value:
                        share = 0.42
                    elif spec == "anthro_so2" and sec_name == ControlSector.POWER_PLANTS.value:
                        share = 0.65
                    elif spec == "anthro_so2" and sec_name == ControlSector.INDUSTRY.value:
                        share = 0.28
                    elif spec == "anthro_co" and sec_name == ControlSector.ROAD_TRANSPORT.value:
                        share = 0.48
                    elif spec == "anthro_voc" and sec_name == ControlSector.ROAD_TRANSPORT.value:
                        share = 0.45

                    delta_u[c_idx] += baseline_u[c_idx] * share * theta_s

        # Bound delta_u so control cannot become negative
        return np.minimum(baseline_u, delta_u)
