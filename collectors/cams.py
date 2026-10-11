"""
Copernicus Atmosphere Monitoring Service (CAMS) Collector Abstraction
"""
from pathlib import Path
from typing import List, Optional, Dict, Any
import pandas as pd
from collectors.base import BaseCollector
from config.settings import settings
from config.logging_config import get_logger
from schemas.canonical import ProvenanceCategory

logger = get_logger("collectors.cams")


class CAMSCollector(BaseCollector):
    """
    Ingests global atmospheric composition forecasts and reanalysis fields
    from the Copernicus Atmosphere Monitoring Service (CAMS).
    """

    # Official Copernicus ADS dataset identifiers
    DATASET_FORECAST = "cams-global-atmospheric-composition-forecasts"
    DATASET_REANALYSIS = "cams-global-reanalysis-eac4"

    VARIABLES = [
        "particulate_matter_2.5um",
        "particulate_matter_10um",
        "nitrogen_dioxide",
        "ozone",
        "carbon_monoxide",
        "total_aerosol_optical_depth_550nm"
    ]

    def __init__(self):
        super().__init__(source_name="CAMS_Copernicus", raw_subfolder="cams")

    def validate_credentials(self) -> List[str]:
        missing = []
        # CAMS uses Copernicus Atmosphere Data Store (ADS) / CDS credentials
        cds_key = settings.CDS_API_KEY
        if not cds_key or cds_key.startswith("YOUR_") or cds_key == "demo_cds_key":
            missing.append("CDS_API_KEY (or ADS API Key)")
        return missing

    def fetch_live(
        self,
        start_date: str = "",
        end_date: str = "",
        dataset: str = DATASET_FORECAST,
        **kwargs
    ) -> pd.DataFrame:
        """
        Download CAMS gridded composition fields for the regional domain.
        Note: Requires an active Copernicus Atmosphere Data Store (ADS/CDS) account.
        """
        try:
            import cdsapi
        except ImportError:
            raise ImportError("The 'cdsapi' package is required for CAMS retrieval.")

        bounds = kwargs.get("bounds") or settings.active_domain
        area = [bounds.north, bounds.west, bounds.south, bounds.east]
        target_date = start_date or pd.Timestamp.now(tz="UTC").strftime("%Y-%m-%d")
        
        nc_path = self.raw_dir / f"cams_{dataset}_{target_date}.nc"
        cds_url = os.environ.get("CDSAPI_URL", "https://cds.climate.copernicus.eu/api")
        cds_key = os.environ.get("CDSAPI_KEY", settings.CDS_API_KEY)
        c = cdsapi.Client(url=cds_url, key=cds_key)

        request_payload = {
            "variable": self.VARIABLES,
            "date": target_date,
            "time": ["00:00", "12:00"],
            "leadtime_hour": ["0", "6", "12", "18", "24", "48", "72"],
            "type": "forecast",
            "format": "netcdf",
            "area": area,
        }

        logger.info(f"Submitting CAMS retrieval request for {dataset} to CDS/ADS API")
        c.retrieve(dataset, request_payload, str(nc_path))
        logger.info(f"Downloaded CAMS composition NetCDF to {nc_path}")
        return self._parse_cams_netcdf(nc_path)

    def _parse_cams_netcdf(self, nc_path: Path) -> pd.DataFrame:
        """Extract CAMS chemical fields from NetCDF into canonical table"""
        try:
            import xarray as xr
        except ImportError:
            raise ImportError("xarray is required to parse CAMS NetCDF.")

        ds = xr.open_dataset(nc_path)
        df = ds.to_dataframe().reset_index()
        ds.close()

        rename_dict = {
            "valid_time": "timestamp",
            "time": "timestamp",
            "pm2p5": "cams_pm25",
            "pm10": "cams_pm10",
            "no2": "cams_no2",
            "go3": "cams_o3",
            "co": "cams_co",
            "aod550": "cams_aerosol"
        }
        df = df.rename(columns={k: v for k, v in rename_dict.items() if k in df.columns})
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True).dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        df["provenance"] = ProvenanceCategory.MODELLED.value
        return df

    def load_cached_or_demo(self, **kwargs) -> pd.DataFrame:
        """Load local cached CAMS NetCDF/CSV files or fallback to demo AOD dataset"""
        cached_nc = sorted(self.raw_dir.glob("cams_*.nc"), reverse=True)
        if cached_nc:
            logger.info(f"Loading local cached CAMS NetCDF file: {cached_nc[0]}")
            return self._parse_cams_netcdf(cached_nc[0])

        demo_path = settings.DATASETS_SAMPLE_DIR / "08_satellite_aod.csv"
        if demo_path.exists():
            logger.info(f"Loading synthetic demo CAMS/AOD dataset from {demo_path}")
            df = pd.read_csv(demo_path)
            return self._normalize_demo_cams(df)

        logger.warning("No CAMS data found in cache or demo folder")
        return pd.DataFrame()

    def _normalize_demo_cams(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize demo CAMS/AOD dataframe"""
        if df.empty:
            return df
        df_out = df.copy()
        df_out.columns = [c.lower().strip() for c in df_out.columns]

        if "timestamp" in df_out.columns:
            df_out["timestamp"] = pd.to_datetime(df_out["timestamp"], utc=True).dt.strftime("%Y-%m-%dT%H:%M:%SZ")

        if "aod_550nm" in df_out.columns and "cams_aerosol" not in df_out.columns:
            df_out["cams_aerosol"] = df_out["aod_550nm"]

        df_out["provenance"] = "SYNTHETIC_DEMO"
        return df_out
