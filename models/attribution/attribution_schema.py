"""
Schema definitions and data containers for Source Attribution and Counterfactual Intelligence.
"""
from typing import Dict, Any, List, Optional
from enum import Enum
from pydantic import BaseModel, Field


class ProvenanceType(str, Enum):
    """Data and calculation provenance standard for SAMEER Phase 4"""
    MODELLED = "MODELLED"
    COUNTERFACTUAL = "COUNTERFACTUAL"
    OBSERVED = "OBSERVED"
    INFERRED = "INFERRED"
    BENCHMARKED = "BENCHMARKED"
    SCENARIO = "SCENARIO"
    NOT_AVAILABLE = "NOT AVAILABLE"


class AttributionSector(str, Enum):
    """Standard emission sectors resolved in SAMEER inventory and controls"""
    ROAD_TRANSPORT = "road_transport"
    INDUSTRY = "industry"
    POWER_PLANTS = "power_plants"
    RESIDENTIAL = "residential"
    AGRICULTURE = "agriculture"
    WASTE_BURNING = "waste_burning"
    CONSTRUCTION_PROXY = "construction_proxy"
    BACKGROUND = "background"
    OTHER = "other"


class SourcePerturbation(BaseModel):
    """
    Defines a fractional or absolute emission perturbation for counterfactual simulation.
    """
    sector: str = Field(..., description="Target emission sector")
    species: Optional[str] = Field(None, description="Specific chemical species or 'all'")
    baseline_value: float = Field(..., description="Baseline control/emission rate")
    perturbation_fraction: float = Field(
        ...,
        ge=-1.0,
        le=1.0,
        description="Fractional change: -0.20 for 20% reduction, +0.10 for 10% increase"
    )
    perturbed_value: float = Field(..., description="Perturbed control/emission rate")
    provenance: ProvenanceType = Field(default=ProvenanceType.SCENARIO)


class FireCluster(BaseModel):
    """
    Aggregated active biomass burning cluster from FIRMS / GFAS satellite observations.
    """
    cluster_id: str
    latitude: float
    longitude: float
    total_frp: float
    fire_count: int
    mean_confidence: float
    timestamp: str
    provenance: ProvenanceType = Field(default=ProvenanceType.OBSERVED)


class PlumeArrivalEstimate(BaseModel):
    """
    Dynamic plume clock tracking agricultural burning transport into Delhi NCR.
    """
    fire_cluster_id: str
    source_region: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    fire_count: int = 1
    fire_timestamp: str
    total_frp: float
    wind_speed_ms: float
    wind_direction_from_deg: float
    estimated_distance_km: float
    estimated_transport_time_hours: float
    estimated_arrival_time: str
    transport_confidence: float
    is_upwind: bool
    status: str = Field(default="Estimated plume arrival")
    provenance: ProvenanceType = Field(default=ProvenanceType.INFERRED)


class SectorContribution(BaseModel):
    """
    Modelled counterfactual contribution of a specific emission sector to air quality.
    """
    sector: str
    delta_pm25: float = Field(..., description="Absolute PM2.5 reduction if sector removed (ug/m3)")
    delta_pm10: float = Field(default=0.0, description="Absolute PM10 reduction (ug/m3)")
    delta_o3: float = Field(default=0.0, description="Absolute O3 change (ug/m3)")
    delta_no2: float = Field(default=0.0, description="Absolute NO2 reduction (ug/m3)")
    percentage_pm25: float = Field(..., description="Relative contribution to total controllable PM2.5 (%)")
    method: str = Field(default="MODELLED COUNTERFACTUAL ZERO-OUT")
    provenance: ProvenanceType = Field(default=ProvenanceType.COUNTERFACTUAL)


class RegionalAttribution(BaseModel):
    """
    Disaggregation of air pollutant concentrations across spatial scales.
    """
    local_pm25: float = Field(..., description="Local urban source contribution (ug/m3)")
    regional_pm25: float = Field(..., description="Regional advection / upwind plume contribution (ug/m3)")
    background_pm25: float = Field(..., description="Natural / regional baseline inflow (ug/m3)")
    local_percentage: float = Field(..., description="Local percentage (%)")
    regional_percentage: float = Field(..., description="Regional percentage (%)")
    background_percentage: float = Field(..., description="Background percentage (%)")
    provenance: ProvenanceType = Field(default=ProvenanceType.INFERRED)


class AttributionResult(BaseModel):
    """
    Comprehensive source attribution and counterfactual intelligence output schema.
    """
    timestamp: str
    target_cell: str
    target_region: str
    horizon_hours: int
    baseline_pm25: float
    counterfactual_pm25: float
    sector_contributions: Dict[str, SectorContribution]
    regional_breakdown: RegionalAttribution
    plume_estimates: List[PlumeArrivalEstimate] = Field(default_factory=list)
    interaction_residual_pm25: float = Field(
        default=0.0,
        description="Non-linear interaction residual: baseline - (zero_all + sum(deltas))"
    )
    dominant_sector: str
    dominant_sector_percentage: float
    confidence_level: float = Field(default=0.95)
    provenance: ProvenanceType = Field(default=ProvenanceType.COUNTERFACTUAL)
