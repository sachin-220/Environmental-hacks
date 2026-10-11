"""
Global Fire Assimilation System (GFAS) Biomass Burning Emissions Collector Abstraction
"""
from pathlib import Path
from typing import List, Optional, Dict, Any
import pandas as pd
from collectors.base import BaseCollector
from config.settings import settings
from config.logging_config import get_logger
from schemas.canonical import ProvenanceCategory

logger = get_logger("collectors.gfas")


class GFASCollector(BaseCollector):
    """
    Ingests daily/hourly biomass-burning emissions and fire radiative power from the
    Copernicus Global Fire Assimilation System (GFAS).
    """

    GFAS_DATASET = "cams-global-fire-emissions-gfas"

    VARIABLES = [
        "wildfire_flux_of_biomass_matter",
        "wildfire_flux_of_carbon_monoxide",
        "wildfire_flux_of_nitrogen_oxides",
        "wildfire_flux_of_sulfur_dioxide",
        "wildfire_flux_of_black_carbon",
        "wildfire_flux_of_organic_carbon",
        "mean_fire_radiative_power"
    ]

    def __init__(self):
        super().__init__(source_name="GFAS_Copernicus", raw_subfolder="gfas")

    def validate_credentials(self) -> List[str]:
        missing = []
        cds_key = settings.CDS_API_KEY
        if not cds_key or cds_key.startswith("YOUR_") or cds_key == "demo_cds_key":
            missing.append("CDS_API_KEY")
        return missing

    def fetch_live(
        self,
        start_date: str = "",
        end_date: str = "",
        **kwargs
    ) -> pd.DataFrame:
        """
        Download regional GFAS biomass burning flux estimates from CDS/ADS API.
        """
        try:
            import cdsapi
        except ImportError:
            raise ImportError("The 'cdsapi' package is required for GFAS downloads.")

        bounds = settings.REGIONAL_DOMAIN
        area = [bounds.north, bounds.west, bounds.south, bounds.east]
        target_date = start_date or pd.Timestamp.now(tz="UTC").strftime("%Y-%m-%d")

        nc_path = self.raw_dir / f"gfas_emissions_{target_date}.nc"
        cds_url = os.environ.get("CDSAPI_URL", "https://cds.climate.copernicus.eu/api")
        cds_key = os.environ.get("CDSAPI_KEY", settings.CDS_API_KEY)
        c = cdsapi.Client(url=cds_url, key=cds_key)

        request_payload = {
            "date": target_date,
            "variable": self.VARIABLES,
            "format": "netcdf",
            "area": area,
        }

        logger.info(f"Submitting GFAS request to CDS API for date={target_date}, area={area}")
        c.retrieve(self.GFAS_DATASET, request_payload, str(nc_path))
        logger.info(f"Downloaded GFAS NetCDF to {nc_path}")
        return self._parse_gfas_netcdf(nc_path)

    def _parse_gfas_netcdf(self, nc_path: Path) -> pd.DataFrame:
        """Parse GFAS NetCDF into tabular format"""
        try:
            import xarray as xr
        except ImportError:
            raise ImportError("xarray is required to parse GFAS NetCDF.")

        ds = xr.open_dataset(nc_path)
        df = ds.to_dataframe().reset_index()
        ds.close()

        rename_dict = {
            "valid_time": "timestamp",
            "time": "timestamp",
            "mfrp": "fire_frp",
            "co_flux": "fire_co_flux",
            "nox_flux": "fire_nox_flux",
            "bc_flux": "fire_bc_flux",
            "oc_flux": "fire_oc_flux"
        }
        df = df.rename(columns={k: v for k, v in rename_dict.items() if k in df.columns})
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True).dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        df["provenance"] = ProvenanceCategory.MODELLED.value
        return df

    def load_cached_or_demo(self, **kwargs) -> pd.DataFrame:
        """Load local cached GFAS NetCDF or demo fire emission estimates"""
        cached_nc = sorted(self.raw_dir.glob("gfas_*.nc"), reverse=True)
        if cached_nc:
            logger.info(f"Loading local cached GFAS file: {cached_nc[0]}")
            return self._parse_gfas_netcdf(cached_nc[0])

        demo_path = settings.DATASETS_SAMPLE_DIR / "07_fire_emission_estimates.csv"
        if demo_path.exists():
            logger.info(f"Loading synthetic demo GFAS fire emissions from {demo_path}")
            df = pd.read_csv(demo_path)
            return self._normalize_demo_gfas(df)

        logger.warning("No GFAS data found in cache or demo folder")
        return pd.DataFrame()

    def _normalize_demo_gfas(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize demo GFAS fire emission estimates"""
        if df.empty:
            return df
        df_out = df.copy()
        df_out.columns = [c.lower().strip() for c in df_out.columns]

        if "timestamp" in df_out.columns:
            df_out["timestamp"] = pd.to_datetime(df_out["timestamp"], utc=True).dt.strftime("%Y-%m-%dT%H:%M:%SZ")

        df_out["provenance"] = "SYNTHETIC_DEMO"
        return df_out
