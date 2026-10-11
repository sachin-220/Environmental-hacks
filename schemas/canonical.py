"""
SAMEER Canonical Hourly Data Schema and Provenance Standards
"""
from enum import Enum
from typing import Optional, Dict, Any, List
import pandas as pd
from pydantic import BaseModel, Field


class ProvenanceCategory(str, Enum):
    """Scientific Data Provenance Categories"""
    OBSERVED = "OBSERVED"           # Direct ground/satellite instrument observation
    REANALYSIS = "REANALYSIS"       # Physically-consistent model assimilation (e.g. ERA5)
    MODELLED = "MODELLED"           # Chemical transport / numerical weather prediction (e.g. CAMS, WRF-Chem)
    ESTIMATED = "ESTIMATED"         # Empirical/diagnostic formulation (e.g. lapse-rate, plume transport score)
    SIMULATED = "SIMULATED"         # Spectral / surrogate forward simulation
    COUNTERFACTUAL = "COUNTERFACTUAL" # Emission-intervention scenario run


class QualityFlag(str, Enum):
    """Observation and Record Quality Flags"""
    VALID = "VALID"                 # Passed all range and consistency filters
    SUSPECT = "SUSPECT"             # Out of normal variance but physically possible
    MISSING = "MISSING"             # Sensor failure, missing observation
    IMPUTED = "IMPUTED"             # Short gap linearly interpolated with no lookahead


class CanonicalHourlyRecord(BaseModel):
    """Single hourly grid-cell observation record conforming to SAMEER Canonical Schema"""
    
    # Spatio-Temporal Coordinates
    timestamp: str = Field(..., description="UTC ISO-8601 Timestamp (e.g. 2026-10-15T12:00:00Z)")
    latitude: float = Field(..., description="Grid cell center latitude (WGS84)")
    longitude: float = Field(..., description="Grid cell center longitude (WGS84)")
    grid_id: str = Field(..., description="Unique grid cell identifier (e.g. D03_R12_C14)")
    
    # Surface Meteorology
    temperature_2m: Optional[float] = Field(None, description="2m Air Temperature [K]")
    dewpoint_2m: Optional[float] = Field(None, description="2m Dew Point Temperature [K]")
    surface_pressure: Optional[float] = Field(None, description="Surface Atmospheric Pressure [hPa]")
    relative_humidity: Optional[float] = Field(None, description="2m Relative Humidity [%]")
    precipitation: Optional[float] = Field(None, description="Precipitation rate [mm/h]")
    solar_radiation: Optional[float] = Field(None, description="Surface Downward Solar Radiation [W/m2]")
    cloud_cover: Optional[float] = Field(None, description="Total Cloud Cover fraction [0.0 - 1.0]")
    
    # Atmospheric Dynamics & Vertical Profile Diagnostics
    u_wind_10m: Optional[float] = Field(None, description="10m U-component of Wind (Zonal, Eastward) [m/s]")
    v_wind_10m: Optional[float] = Field(None, description="10m V-component of Wind (Meridional, Northward) [m/s]")
    wind_speed_10m: Optional[float] = Field(None, description="10m Wind Speed magnitude [m/s]")
    wind_direction_10m: Optional[float] = Field(None, description="10m Wind Direction [degrees clockwise from North]")
    boundary_layer_height: Optional[float] = Field(None, description="Planetary Boundary Layer (PBL) Height [m]")
    inversion_strength: Optional[float] = Field(None, description="Temperature Inversion Strength (Delta T across layer) [K]")
    inversion_height: Optional[float] = Field(None, description="Base height of atmospheric temperature inversion [m]")
    inversion_top: Optional[float] = Field(None, description="Top height of atmospheric temperature inversion [m]")
    inversion_presence: Optional[int] = Field(0, description="Binary flag: 1 if inversion active, 0 otherwise")
    vertical_temperature_gradient: Optional[float] = Field(None, description="Environmental lapse rate dT/dz [K/km]")
    wind_shear: Optional[float] = Field(None, description="Vertical wind shear du/dz [s^-1]")
    stability_index: Optional[str] = Field("NEUTRAL", description="Bulk Atmospheric Stability: UNSTABLE, NEUTRAL, STABLE, VERY_STABLE")
    
    # Ground Air Quality Measurements
    pm25: Optional[float] = Field(None, description="Fine particulate matter PM2.5 [ug/m3]")
    pm10: Optional[float] = Field(None, description="Coarse particulate matter PM10 [ug/m3]")
    o3: Optional[float] = Field(None, description="Surface Ozone O3 [ug/m3]")
    no2: Optional[float] = Field(None, description="Nitrogen Dioxide NO2 [ug/m3]")
    so2: Optional[float] = Field(None, description="Sulfur Dioxide SO2 [ug/m3]")
    co: Optional[float] = Field(None, description="Carbon Monoxide CO [mg/m3]")
    
    # Satellite Active Fire & Biomass Burning Inflow
    fire_count: Optional[int] = Field(0, description="Active fire hotspots count in surrounding radius")
    fire_frp: Optional[float] = Field(0.0, description="Total Fire Radiative Power [MW]")
    fire_confidence: Optional[float] = Field(None, description="Mean active fire detection confidence [%]")
    nearest_fire_distance: Optional[float] = Field(None, description="Distance to nearest detected fire hotspot [km]")
    upwind_fire_count: Optional[int] = Field(0, description="Active fires located in the upwind wind-sector")
    upwind_fire_frp: Optional[float] = Field(0.0, description="Total FRP in the upwind sector [MW]")
    upwind_fire_distance: Optional[float] = Field(None, description="Mean distance of upwind fires to grid cell [km]")
    wind_fire_angle: Optional[float] = Field(None, description="Angle between wind vector and fire bearing [degrees]")
    plume_transport_score: Optional[float] = Field(0.0, description="Physical plume transport index [0.0 - 100.0]")
    
    # Copernicus CAMS Chemical Model Fields
    cams_pm25: Optional[float] = Field(None, description="CAMS Regional/Global Forecast PM2.5 [ug/m3]")
    cams_o3: Optional[float] = Field(None, description="CAMS Ozone [ug/m3]")
    cams_no2: Optional[float] = Field(None, description="CAMS NO2 [ug/m3]")
    cams_co: Optional[float] = Field(None, description="CAMS CO [mg/m3]")
    cams_aerosol: Optional[float] = Field(None, description="CAMS Aerosol Optical Depth 550nm")
    
    # Anthropogenic Emissions Inventory
    anthro_nox: Optional[float] = Field(0.0, description="Gridded Anthropogenic NOx Emission [kg/h/km2]")
    anthro_so2: Optional[float] = Field(0.0, description="Gridded Anthropogenic SO2 Emission [kg/h/km2]")
    anthro_co: Optional[float] = Field(0.0, description="Gridded Anthropogenic CO Emission [kg/h/km2]")
    anthro_nh3: Optional[float] = Field(0.0, description="Gridded Anthropogenic NH3 Emission [kg/h/km2]")
    anthro_voc: Optional[float] = Field(0.0, description="Gridded Anthropogenic NMVOC Emission [kg/h/km2]")
    anthro_bc: Optional[float] = Field(0.0, description="Gridded Anthropogenic Black Carbon Emission [kg/h/km2]")
    anthro_oc: Optional[float] = Field(0.0, description="Gridded Anthropogenic Organic Carbon Emission [kg/h/km2]")
    
    # Provenance & Quality Flags
    provenance: str = Field(ProvenanceCategory.OBSERVED.value, description="Data provenance classification")
    quality_flag: str = Field(QualityFlag.VALID.value, description="Data quality control flag")


CANONICAL_COLUMNS: List[str] = list(CanonicalHourlyRecord.model_fields.keys())

CANONICAL_DTYPES: Dict[str, str] = {
    "timestamp": "string",
    "latitude": "float64",
    "longitude": "float64",
    "grid_id": "string",
    "temperature_2m": "float64",
    "dewpoint_2m": "float64",
    "surface_pressure": "float64",
    "relative_humidity": "float64",
    "precipitation": "float64",
    "solar_radiation": "float64",
    "cloud_cover": "float64",
    "u_wind_10m": "float64",
    "v_wind_10m": "float64",
    "wind_speed_10m": "float64",
    "wind_direction_10m": "float64",
    "boundary_layer_height": "float64",
    "inversion_strength": "float64",
    "inversion_height": "float64",
    "inversion_top": "float64",
    "inversion_presence": "int64",
    "vertical_temperature_gradient": "float64",
    "wind_shear": "float64",
    "stability_index": "string",
    "pm25": "float64",
    "pm10": "float64",
    "o3": "float64",
    "no2": "float64",
    "so2": "float64",
    "co": "float64",
    "fire_count": "int64",
    "fire_frp": "float64",
    "fire_confidence": "float64",
    "nearest_fire_distance": "float64",
    "upwind_fire_count": "int64",
    "upwind_fire_frp": "float64",
    "upwind_fire_distance": "float64",
    "wind_fire_angle": "float64",
    "plume_transport_score": "float64",
    "cams_pm25": "float64",
    "cams_o3": "float64",
    "cams_no2": "float64",
    "cams_co": "float64",
    "cams_aerosol": "float64",
    "anthro_nox": "float64",
    "anthro_so2": "float64",
    "anthro_co": "float64",
    "anthro_nh3": "float64",
    "anthro_voc": "float64",
    "anthro_bc": "float64",
    "anthro_oc": "float64",
    "provenance": "string",
    "quality_flag": "string"
}


class CanonicalHourlySchema:
    """Schema validator and empty DataFrame generator for SAMEER"""
    
    @classmethod
    def create_empty_dataframe(cls) -> pd.DataFrame:
        """Create an empty Pandas DataFrame formatted with exact canonical columns and types"""
        df = pd.DataFrame({col: pd.Series(dtype=dt) for col, dt in CANONICAL_DTYPES.items()})
        return df

    @classmethod
    def validate_dataframe(cls, df: pd.DataFrame) -> List[str]:
        """Validate if a DataFrame strictly conforms to the Canonical Schema"""
        errors = []
        for col in CANONICAL_COLUMNS:
            if col not in df.columns:
                errors.append(f"Missing required canonical column: '{col}'")
        return errors
