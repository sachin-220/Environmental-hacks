"""
SAMEER Processing and Diagnostic Package
"""
from processing.quality import QualityControlValidator, PHYSICAL_LIMITS
from processing.spatial_grid import (
    SpatialGridManager,
    d03_grid_manager,
    d01_grid_manager,
    haversine_distance_km,
    calculate_bearing_degrees
)
from processing.temporal_alignment import TemporalAligner
from processing.inversion import AtmosphericInversionEngine, pressure_to_altitude_hypsometric
from processing.plume import FirePlumeTransportEngine, calculate_wind_speed_direction, circular_angular_difference
from processing.feature_fusion import FeatureFusionPipeline

__all__ = [
    "QualityControlValidator",
    "PHYSICAL_LIMITS",
    "SpatialGridManager",
    "d03_grid_manager",
    "d01_grid_manager",
    "haversine_distance_km",
    "calculate_bearing_degrees",
    "TemporalAligner",
    "AtmosphericInversionEngine",
    "pressure_to_altitude_hypsometric",
    "FirePlumeTransportEngine",
    "calculate_wind_speed_direction",
    "circular_angular_difference",
    "FeatureFusionPipeline"
]
