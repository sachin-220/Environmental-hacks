"""
Copernicus Climate Data Store (CDS) ERA5 Reanalysis Collector
"""
import os
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
import pandas as pd
import numpy as np
from collectors.base import BaseCollector
from config.settings import settings
from config.logging_config import get_logger
from schemas.canonical import ProvenanceCategory

logger = get_logger("collectors.era5")


class ERA5Collector(BaseCollector):
    """
    Ingests surface meteorology and multi-level pressure vertical profiles from ERA5 reanalysis
    via Copernicus Climate Data Store (CDS) API.
    """

    # Copernicus CDS surface dataset and variable identifiers
    SURFACE_DATASET = "reanalysis-era5-single-levels"
    SURFACE_VARIABLES = [
        "2m_temperature",
        "2m_dewpoint_temperature",
        "surface_pressure",
        "10m_u_component_of_wind",
        "10m_v_component_of_wind",
        "total_precipitation",
        "surface_solar_radiation_downwards",
        "total_cloud_cover",
        "boundary_layer_height"
    ]

    # Copernicus CDS pressure-level dataset and variable identifiers
    PRESSURE_DATASET = "reanalysis-era5-pressure-levels"
    PRESSURE_VARIABLES = [
        "temperature",
        "u_component_of_wind",
        "v_component_of_wind",
        "relative_humidity",
        "geopotential"
    ]

    def __init__(self):
        super().__init__(source_name="ERA5_ECMWF", raw_subfolder="era5")

    def validate_credentials(self) -> List[str]:
        missing = []
        # CDS client looks for ~/.cdsapirc or CDS_API_KEY / CDSAPI_KEY / CDSAPI_URL environment vars
        cds_key = os.environ.get("CDSAPI_KEY") or settings.CDS_API_KEY
        cdsapirc = Path.home() / ".cdsapirc"
        if not cdsapirc.exists() and (not cds_key or cds_key.startswith("YOUR_") or cds_key == "demo_cds_key"):
            missing.append("CDS_API_KEY")
        return missing

    def fetch_live(
        self,
        start_date: str = "",
        end_date: str = "",
        request_pressure_levels: bool = True,
        **kwargs
    ) -> pd.DataFrame:
        """
        Request regional ERA5 NetCDF extract via CDS API client.
        CDS Area format: [North, West, South, East]
        """
        try:
            import cdsapi
        except ImportError:
            raise ImportError("The 'cdsapi' package is required for live ERA5 downloads. Run `pip install cdsapi`.")

        bounds = kwargs.get("bounds") or settings.active_domain
        area = [bounds.north, bounds.west, bounds.south, bounds.east] # N, W, S, E
        
        target_date = start_date or pd.Timestamp.now(tz="UTC").strftime("%Y-%m-%d")
        year, month, day = target_date.split("-")[:3]
        
        cds_url = os.environ.get("CDSAPI_URL", "https://cds.climate.copernicus.eu/api")
        cds_key = os.environ.get("CDSAPI_KEY", settings.CDS_API_KEY)
        c = cdsapi.Client(url=cds_url, key=cds_key)
        
        # Download surface variables
        surface_nc_path = self.raw_dir / f"era5_surface_{year}{month}{day}.nc"
        logger.info(f"Submitting CDS job for ERA5 surface levels: date={target_date}, area={area}")
        
        surface_request = {
            "product_type": "reanalysis",
            "format": "netcdf",
            "variable": self.SURFACE_VARIABLES,
            "year": year,
            "month": month,
            "day": day,
            "time": [f"{h:02d}:00" for h in range(24)],
            "area": area,
        }
        c.retrieve(self.SURFACE_DATASET, surface_request, str(surface_nc_path))
        logger.info(f"Downloaded ERA5 surface NetCDF to {surface_nc_path}")

        # Download pressure levels if requested
        if request_pressure_levels:
            pressure_nc_path = self.raw_dir / f"era5_pressure_{year}{month}{day}.nc"
            pressure_request = {
                "product_type": "reanalysis",
                "format": "netcdf",
                "variable": self.PRESSURE_VARIABLES,
                "pressure_level": [str(p) for p in settings.PRESSURE_LEVELS_HPA],
                "year": year,
                "month": month,
                "day": day,
                "time": [f"{h:02d}:00" for h in range(24)],
                "area": area,
            }
            logger.info(f"Submitting CDS job for ERA5 vertical levels: levels={settings.PRESSURE_LEVELS_HPA}")
            c.retrieve(self.PRESSURE_DATASET, pressure_request, str(pressure_nc_path))
            logger.info(f"Downloaded ERA5 pressure NetCDF to {pressure_nc_path}")

        # Parse downloaded NetCDF into DataFrame
        return self._parse_era5_netcdf(surface_nc_path)

    def _parse_era5_netcdf(self, nc_path: Path) -> pd.DataFrame:
        """Parse NetCDF dataset using xarray into canonical tabular format"""
        try:
            import xarray as xr
        except ImportError:
            raise ImportError("xarray is required to parse NetCDF files. Run `pip install xarray netCDF4`.")

        ds = xr.open_dataset(nc_path)
        df = ds.to_dataframe().reset_index()
        ds.close()

        # Rename standard ERA5 variable codes to SAMEER schema
        rename_dict = {
            "valid_time": "timestamp",
            "time": "timestamp",
            "t2m": "temperature_2m",
            "d2m": "dewpoint_2m",
            "sp": "surface_pressure",
            "u10": "u_wind_10m",
            "v10": "v_wind_10m",
            "tp": "precipitation",
            "ssrd": "solar_radiation",
            "tcc": "cloud_cover",
            "blh": "boundary_layer_height"
        }
        df = df.rename(columns={k: v for k, v in rename_dict.items() if k in df.columns})
        
        # Convert units where necessary (Pa -> hPa)
        if "surface_pressure" in df.columns and df["surface_pressure"].mean() > 2000:
            df["surface_pressure"] = df["surface_pressure"] / 100.0

        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True).dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        df["provenance"] = ProvenanceCategory.REANALYSIS.value
        return df

    def load_cached_or_demo(self, **kwargs) -> pd.DataFrame:
        """Load local cached ERA5 NetCDF/CSV files or synthetic demo meteorology"""
        # Check for cached NetCDF files
        cached_nc = sorted(self.raw_dir.glob("era5_surface_*.nc"), reverse=True)
        if cached_nc:
            logger.info(f"Loading local cached ERA5 NetCDF file: {cached_nc[0]}")
            return self._parse_era5_netcdf(cached_nc[0])

        # Otherwise load demo dataset from DATASETS/02_surface_meteorology.csv
        demo_path = settings.DATASETS_SAMPLE_DIR / "02_surface_meteorology.csv"
        if demo_path.exists():
            logger.info(f"Loading synthetic demo surface meteorology from {demo_path}")
            df = pd.read_csv(demo_path)
            return self._normalize_demo_meteorology(df)

        logger.warning("No ERA5 data found in cache or demo folder")
        return pd.DataFrame()

    def _normalize_demo_meteorology(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize demo meteorology dataframe"""
        if df.empty:
            return df

        df_out = df.copy()
        df_out.columns = [c.lower().strip() for c in df_out.columns]

        if "timestamp" in df_out.columns:
            df_out["timestamp"] = pd.to_datetime(df_out["timestamp"], utc=True).dt.strftime("%Y-%m-%dT%H:%M:%SZ")

        # Map common names
        mapping = {
            "temperature_c": "temperature_2m",
            "temperature": "temperature_2m",
            "dew_point_c": "dewpoint_2m",
            "rh_pct": "relative_humidity",
            "wind_speed_ms": "wind_speed_10m",
            "wind_direction_deg": "wind_direction_10m",
            "pressure_hpa": "surface_pressure",
            "pbl_height_m": "boundary_layer_height",
            "solar_radiation_wm2": "solar_radiation",
            "cloud_cover_fraction": "cloud_cover"
        }
        for k, v in mapping.items():
            if k in df_out.columns and v not in df_out.columns:
                df_out[v] = df_out[k]

        # Convert Celsius to Kelvin if in Celsius range
        if "temperature_2m" in df_out.columns and df_out["temperature_2m"].mean() < 100:
            df_out["temperature_2m"] = df_out["temperature_2m"] + 273.15
        if "dewpoint_2m" in df_out.columns and df_out["dewpoint_2m"].mean() < 100:
            df_out["dewpoint_2m"] = df_out["dewpoint_2m"] + 273.15

        # Calculate U and V wind components from speed and direction if missing
        if "u_wind_10m" not in df_out.columns and "wind_speed_10m" in df_out.columns and "wind_direction_10m" in df_out.columns:
            ws = df_out["wind_speed_10m"]
            wd = np.radians(df_out["wind_direction_10m"])
            # In meteorology: u = -ws * sin(wd), v = -ws * cos(wd)
            df_out["u_wind_10m"] = -ws * np.sin(wd)
            df_out["v_wind_10m"] = -ws * np.cos(wd)

        df_out["provenance"] = "SYNTHETIC_DEMO"
        return df_out
