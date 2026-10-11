"""
NASA FIRMS (Fire Information for Resource Management System) Collector
"""
import io
from pathlib import Path
from typing import List, Optional, Dict, Any
import pandas as pd
from collectors.base import BaseCollector
from config.settings import settings
from config.logging_config import get_logger
from schemas.canonical import ProvenanceCategory

logger = get_logger("collectors.firms")


class FirmsCollector(BaseCollector):
    """
    Ingests active thermal anomalies and fire radiative power (FRP) from NASA FIRMS.
    Supports MODIS and VIIRS satellite instruments across the regional agricultural fire belt.
    """

    FIRMS_BASE_URL = "https://firms.modaps.eosdis.nasa.gov/api/area/csv"

    def __init__(self):
        super().__init__(source_name="NASA_FIRMS", raw_subfolder="firms")

    def validate_credentials(self) -> List[str]:
        missing = []
        if not settings.FIRMS_MAP_KEY or settings.FIRMS_MAP_KEY.startswith("YOUR_") or settings.FIRMS_MAP_KEY == "demo_firms_key":
            missing.append("FIRMS_MAP_KEY")
        return missing

    def fetch_live(
        self,
        start_date: str = "",
        end_date: str = "",
        source: str = "VIIRS_SNPP_NRT",
        days: int = 1,
        bounds: Optional[Any] = None,
        **kwargs
    ) -> pd.DataFrame:
        """
        Download real-time active fire hotspots from NASA FIRMS API for the study domain.
        Area coordinates: W,S,E,N (e.g. 76.8,28.2,77.6,28.9 for Delhi NCR)
        """
        active_bounds = bounds or settings.active_domain
        area_str = f"{active_bounds.west},{active_bounds.south},{active_bounds.east},{active_bounds.north}"
        map_key = settings.FIRMS_MAP_KEY
        
        url = f"{self.FIRMS_BASE_URL}/{map_key}/{source}/{area_str}/{days}"
        if start_date:
            url += f"/{start_date}"

        logger.info(f"Querying NASA FIRMS API: source={source}, area={area_str}, days={days}")
        resp = self._http_get_with_retry(url)
        
        # Check for error text in body
        text = resp.text.strip()
        if "Invalid Map Key" in text or "Bad Request" in text or "error" in text.lower():
            raise ValueError(f"NASA FIRMS API Error: {text}")

        df = pd.read_csv(io.StringIO(text))
        if df.empty:
            logger.info("NASA FIRMS returned 0 active fire hotspots in domain")
            return pd.DataFrame()

        processed_df = self._normalize_firms_dataframe(df, source=source, is_live=True)
        
        # Cache raw CSV
        out_file = self.raw_dir / f"firms_{source}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv"
        processed_df.to_csv(out_file, index=False)
        logger.info(f"Saved {len(processed_df)} live FIRMS hotspots to {out_file}")
        return processed_df

    def load_cached_or_demo(self, **kwargs) -> pd.DataFrame:
        """Load local cached FIRMS observations or demo hotspot dataset"""
        # First check if any recent cached file exists in data/raw/firms/
        cached_files = sorted(self.raw_dir.glob("firms_*.csv"), reverse=True)
        if cached_files:
            logger.info(f"Loading local cached FIRMS file: {cached_files[0]}")
            df = pd.read_csv(cached_files[0])
            return self._normalize_firms_dataframe(df, is_live=False)

        # Otherwise load demo dataset from DATASETS/06_fire_hotspots.csv
        demo_path = settings.DATASETS_SAMPLE_DIR / "06_fire_hotspots.csv"
        if demo_path.exists():
            logger.info(f"Loading synthetic demo fire hotspots from {demo_path}")
            df = pd.read_csv(demo_path)
            return self._normalize_firms_dataframe(df, is_live=False, is_demo=True)

        logger.warning("No FIRMS data found in cache or demo folder")
        return pd.DataFrame()

    def _normalize_firms_dataframe(
        self,
        df: pd.DataFrame,
        source: str = "VIIRS",
        is_live: bool = False,
        is_demo: bool = False
    ) -> pd.DataFrame:
        """Standardize column names, parse timestamps, deduplicate, and attach provenance"""
        if df.empty:
            return df

        df_out = df.copy()
        
        # Standardize column naming
        df_out.columns = [c.lower().strip() for c in df_out.columns]
        
        # Build UTC timestamp
        if "acq_date" in df_out.columns and "acq_time" in df_out.columns:
            # acq_time format is often HHMM integer or string
            def parse_time(row):
                d = str(row["acq_date"])
                t = str(row["acq_time"]).zfill(4)
                return f"{d} {t[:2]}:{t[2:]}:00"
            df_out["timestamp"] = pd.to_datetime(df_out.apply(parse_time, axis=1), utc=True).dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        elif "timestamp" in df_out.columns:
            df_out["timestamp"] = pd.to_datetime(df_out["timestamp"], utc=True).dt.strftime("%Y-%m-%dT%H:%M:%SZ")

        # Standardize FRP
        if "frp" not in df_out.columns:
            df_out["frp"] = 0.0

        # Standardize confidence
        if "confidence" in df_out.columns:
            # Handle categorical confidence 'l', 'n', 'h' from VIIRS
            conf_map = {"l": 30.0, "n": 65.0, "h": 95.0, "low": 30.0, "nominal": 65.0, "high": 95.0}
            df_out["confidence"] = df_out["confidence"].astype(str).str.lower().map(lambda x: conf_map.get(x, x))
            df_out["confidence"] = pd.to_numeric(df_out["confidence"], errors="coerce").fillna(50.0)
        else:
            df_out["confidence"] = 75.0

        # Filter to regional bounding box
        bounds = settings.REGIONAL_DOMAIN
        mask = (
            (df_out["latitude"] >= bounds.south) &
            (df_out["latitude"] <= bounds.north) &
            (df_out["longitude"] >= bounds.west) &
            (df_out["longitude"] <= bounds.east)
        )
        df_out = df_out[mask].copy()

        # Deduplicate identical spatial detections within 1 hour
        df_out = df_out.drop_duplicates(subset=["latitude", "longitude", "timestamp"])

        df_out["source_instrument"] = df_out.get("instrument", source)
        df_out["provenance"] = ProvenanceCategory.OBSERVED.value if (is_live and not is_demo) else (
            "SYNTHETIC_DEMO" if is_demo else ProvenanceCategory.OBSERVED.value
        )
        return df_out
