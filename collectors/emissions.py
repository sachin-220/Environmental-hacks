"""
Gridded Anthropogenic Emission Inventory Collector & Remapping Abstraction
"""
from pathlib import Path
from typing import List, Optional, Dict, Any
import pandas as pd
from collectors.base import BaseCollector
from config.settings import settings
from config.logging_config import get_logger
from schemas.canonical import ProvenanceCategory

logger = get_logger("collectors.emissions")


class EmissionsCollector(BaseCollector):
    """
    Ingests and formats gridded multi-sector anthropogenic emission inventories
    (such as CAMS-GLOB-ANT, EDGAR, and local high-resolution Delhi inventories).
    """

    SECTORS = [
        "road_transport",
        "industry",
        "power_plants",
        "residential",
        "agriculture",
        "waste_burning",
        "other"
    ]

    SPECIES = [
        "nox",
        "so2",
        "co",
        "nh3",
        "nmvoc",
        "bc",
        "oc"
    ]

    def __init__(self):
        super().__init__(source_name="Anthropogenic_Emissions", raw_subfolder="emissions")

    def validate_credentials(self) -> List[str]:
        # Emission inventories are typically static NetCDF / GeoTIFF files or ECCAD downloads
        return []

    def fetch_live(self, start_date: str = "", end_date: str = "", **kwargs) -> pd.DataFrame:
        """Fetch emission inventory datasets from local/remote repository"""
        return self.load_cached_or_demo(**kwargs)

    def load_cached_or_demo(self, **kwargs) -> pd.DataFrame:
        """Load gridded emission inventory tables from raw folder or demo pack"""
        cached_csv = sorted(self.raw_dir.glob("emissions_*.csv"), reverse=True)
        if cached_csv:
            logger.info(f"Loading local cached emission inventory file: {cached_csv[0]}")
            df = pd.read_csv(cached_csv[0])
            return self._normalize_emissions_dataframe(df)

        demo_path = settings.DATASETS_SAMPLE_DIR / "09_emission_inventory.csv"
        if demo_path.exists():
            logger.info(f"Loading synthetic demo emission inventory from {demo_path}")
            df = pd.read_csv(demo_path)
            return self._normalize_emissions_dataframe(df, is_demo=True)

        logger.warning("No emission inventory dataset found in cache or demo folder")
        return pd.DataFrame()

    def _normalize_emissions_dataframe(self, df: pd.DataFrame, is_demo: bool = False) -> pd.DataFrame:
        """Standardize emission columns and sectoral breakdown"""
        if df.empty:
            return df
        df_out = df.copy()
        df_out.columns = [c.lower().strip() for c in df_out.columns]

        # Standardize anthro species prefixes if not already present
        mapping = {
            "nox": "anthro_nox",
            "so2": "anthro_so2",
            "co": "anthro_co",
            "nh3": "anthro_nh3",
            "voc": "anthro_voc",
            "nmvoc": "anthro_voc",
            "bc": "anthro_bc",
            "oc": "anthro_oc"
        }
        for k, v in mapping.items():
            if k in df_out.columns and v not in df_out.columns:
                df_out[v] = df_out[k]

        df_out["provenance"] = "SYNTHETIC_DEMO" if is_demo else ProvenanceCategory.ESTIMATED.value
        return df_out
