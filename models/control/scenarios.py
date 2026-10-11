"""
Policy Strategies and Scenario Configuration for Model Predictive Control
"""
from enum import Enum
from typing import Dict, Any
from pydantic import BaseModel, Field

from models.attribution.attribution_schema import ProvenanceType


class PolicyStrategy(str, Enum):
    """Three standard policy strategies required by SAMEER Phase 4"""
    LOW_COST = "LOW_COST"
    BALANCED = "BALANCED"
    AGGRESSIVE = "AGGRESSIVE"


class PolicyStrategyConfig(BaseModel):
    """Mathematical optimization weights and feasibility parameters for a policy strategy"""
    strategy_name: PolicyStrategy
    display_title: str
    description: str
    weight_pollution: float
    weight_cost: float
    weight_smoothness: float
    feasibility_multiplier: float = Field(
        ...,
        description="Scales the maximum allowed sector reduction bounds (e.g. 0.5x for Low-Cost, 1.25x for Aggressive)"
    )
    provenance: ProvenanceType = Field(default=ProvenanceType.SCENARIO)


class MPCScenarioManager:
    """
    Supplies mathematically distinct optimization parameter sets for the three strategies.
    Ensures that strategies are genuine optimization reconfigurations, NOT hard-coded outputs.
    """

    STRATEGIES: Dict[PolicyStrategy, PolicyStrategyConfig] = {
        PolicyStrategy.LOW_COST: PolicyStrategyConfig(
            strategy_name=PolicyStrategy.LOW_COST,
            display_title="Low-Cost / Minimal Disruption Policy",
            description="High cost penalty (w_cost=5.0). Prioritizes lowest-cost municipal curbs (waste patrols, high-emitter transport) while capping economic interventions.",
            weight_pollution=0.5,
            weight_cost=5.0,
            weight_smoothness=1.0,
            feasibility_multiplier=0.50
        ),
        PolicyStrategy.BALANCED: PolicyStrategyConfig(
            strategy_name=PolicyStrategy.BALANCED,
            display_title="Balanced Regulatory Policy (Standard GRAP)",
            description="Balanced multi-objective (w_poll=2.0, w_cost=1.0). Combines moderate traffic restrictions, scheduled industrial curbs, and active stubble suppression.",
            weight_pollution=2.0,
            weight_cost=1.0,
            weight_smoothness=0.5,
            feasibility_multiplier=1.00
        ),
        PolicyStrategy.AGGRESSIVE: PolicyStrategyConfig(
            strategy_name=PolicyStrategy.AGGRESSIVE,
            display_title="Aggressive Emergency Curtailment (GRAP Stage IV)",
            description="Dominant health protection (w_poll=10.0, w_cost=0.2). Enforces maximum feasible emergency shutdowns across all sectors to prevent catastrophic AQI spikes.",
            weight_pollution=10.0,
            weight_cost=0.2,
            weight_smoothness=0.1,
            feasibility_multiplier=1.25
        )
    }

    @classmethod
    def get_config(cls, strategy: PolicyStrategy) -> PolicyStrategyConfig:
        return cls.STRATEGIES[strategy]
