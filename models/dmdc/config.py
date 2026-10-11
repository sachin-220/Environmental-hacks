"""
DMDc and Koopman Spectral Emulator Configuration and Feature Specifications
"""
from pathlib import Path
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from config.settings import settings


class DMDcFeatureConfig:
    """
    Defines explicit state, control, and target feature sets derived directly from Phase 2 trajectories.
    """

    # Physical coupled state vector x(t) in R^15
    STATE_VARIABLES: List[str] = [
        "boundary_layer_height",
        "temperature_2m",
        "u_wind_10m",
        "v_wind_10m",
        "wind_speed_10m",
        "relative_humidity",
        "surface_pressure",
        "inversion_strength",
        "pm25",
        "pm10",
        "o3",
        "no2",
        "so2",
        "co",
        "cams_aerosol"
    ]

    # Exogenous control / forcing input vector u(t) in R^8
    CONTROL_VARIABLES: List[str] = [
        "anthro_nox",
        "anthro_so2",
        "anthro_co",
        "anthro_voc",
        "fire_frp",
        "plume_transport_score",
        "solar_radiation",
        "precipitation"
    ]

    # Primary air quality forecast target pollutants
    TARGET_POLLUTANTS: List[str] = [
        "pm25",
        "pm10",
        "o3",
        "no2",
        "so2",
        "co"
    ]

    # Meteorological state variables in x(t)
    MET_VARIABLES: List[str] = [
        "boundary_layer_height",
        "temperature_2m",
        "u_wind_10m",
        "v_wind_10m",
        "wind_speed_10m",
        "relative_humidity",
        "surface_pressure",
        "inversion_strength"
    ]

    # Physical bounding limits for sanity checks and consistency validation
    PHYSICAL_BOUNDS: Dict[str, Dict[str, float]] = {
        "pm25": {"min": 0.0, "max": 1500.0},
        "pm10": {"min": 0.0, "max": 2500.0},
        "o3": {"min": 0.0, "max": 500.0},
        "no2": {"min": 0.0, "max": 600.0},
        "so2": {"min": 0.0, "max": 500.0},
        "co": {"min": 0.0, "max": 50.0},
        "cams_aerosol": {"min": 0.0, "max": 10.0},
        "boundary_layer_height": {"min": 50.0, "max": 4500.0},
        "temperature_2m": {"min": 250.0, "max": 335.0},
        "surface_pressure": {"min": 85000.0, "max": 105000.0},
        "relative_humidity": {"min": 0.0, "max": 100.0},
        "wind_speed_10m": {"min": 0.0, "max": 50.0},
        "inversion_strength": {"min": 0.0, "max": 25.0}
    }


class DMDcModelConfig(BaseModel):
    """Configuration hyperparameters for DMDc model fitting and evaluation"""
    state_dim: int = 15
    control_dim: int = 8
    default_horizon: int = 72
    evaluation_horizons: List[int] = Field(default_factory=lambda: [1, 6, 12, 24, 48, 72])
    
    # Rank selection options: 'validation_error', 'energy_threshold', 'fixed'
    rank_selection_method: str = "validation_error"
    energy_threshold: float = 0.999
    max_rank: int = 23  # state_dim + control_dim = 15 + 8
    candidate_ranks: List[int] = Field(default_factory=lambda: list(range(4, 24)))
    
    # Regularization candidates
    candidate_lambdas: List[float] = Field(
        default_factory=lambda: [0.0, 1e-6, 1e-4, 1e-2, 0.1, 1.0, 10.0]
    )
    
    # Stabilization
    allow_stabilization: bool = False
    spectral_radius_limit: float = 1.005

    # Storage paths
    artifact_dir: Path = Field(
        default_factory=lambda: settings.BASE_DIR / "models" / "artifacts" / "dmdc"
    )
    reports_dir: Path = Field(
        default_factory=lambda: settings.BASE_DIR / "reports" / "dmdc"
    )
    trajectories_dir: Path = Field(
        default_factory=lambda: settings.DATA_FINAL_DIR / "wrfchem_trajectories"
    )
