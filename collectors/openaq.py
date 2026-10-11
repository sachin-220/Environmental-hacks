"""
OpenAQ Ground Air Quality Ingestion Collector
"""
from pathlib import Path
from typing import List, Optional, Dict, Any
import pandas as pd
from collectors.base import BaseCollector
from config.settings import settings
from config.logging_config import get_logger
from schemas.canonical import ProvenanceCategory

logger = get_logger("collectors.openaq")


class OpenAQCollector(BaseCollector):
    """
    Collects high-resolution continuous ambient air quality measurements from ground stations
    across Delhi NCR and neighbouring states via OpenAQ API v3.
    """

    OPENAQ_BASE_URL = "https://api.openaq.org/v3"

    PARAMETER_MAP = {
        "pm25": "pm25",
        "pm10": "pm10",
        "no2": "no2",
        "so2": "so2",
        "o3": "o3",
        "co": "co"
    }

    def __init__(self):
        super().__init__(source_name="OpenAQ", raw_subfolder="openaq")

    def validate_credentials(self) -> List[str]:
        missing = []
        if not settings.OPENAQ_API_KEY or settings.OPENAQ_API_KEY.startswith("YOUR_") or settings.OPENAQ_API_KEY == "demo_openaq_key":
            missing.append("OPENAQ_API_KEY")
        return missing

    def fetch_live(
        self,
        start_date: str = "",
        end_date: str = "",
        limit: int = 50,
        bounds: Optional[Any] = None,
        **kwargs
    ) -> pd.DataFrame:
        """
        Fetch ground station air quality measurements within the target domain via OpenAQ v3 API.
        """
        active_bounds = bounds or settings.active_domain
        bbox_str = f"{active_bounds.west},{active_bounds.south},{active_bounds.east},{active_bounds.north}"
        headers = {"X-API-Key": settings.OPENAQ_API_KEY}
        
        url = f"{self.OPENAQ_BASE_URL}/locations"
        params = {
            "bbox": bbox_str,
            "limit": limit
        }
        
        logger.info(f"Querying OpenAQ stations in bbox={bbox_str} (limit={limit})")
        resp = self._http_get_with_retry(url, params=params, headers=headers)
        data = resp.json()
        
        locations = data.get("results", [])
        if not locations:
            logger.warning("No OpenAQ stations found in domain bounding box")
            return pd.DataFrame()

        records = []
        for loc in locations:
            loc_id = loc.get("id")
            loc_name = loc.get("name", f"Station_{loc_id}")
            coords = loc.get("coordinates", {})
            lat = coords.get("latitude")
            lon = coords.get("longitude")

            if lat is None or lon is None:
                continue

            # In OpenAQ v3: /locations/{id}/sensors returns all parameter sensors for the location
            s_url = f"{self.OPENAQ_BASE_URL}/locations/{loc_id}/sensors"
            try:
                s_resp = self._http_get_with_retry(s_url, headers=headers)
                s_data = s_resp.json()
                for sensor in s_data.get("results", []):
                    param_obj = sensor.get("parameter", {})
                    param_raw = param_obj.get("name", "").lower().replace(".", "").replace(" ", "").replace("₂", "2").replace("₃", "3")
                    unit = param_obj.get("units", "ug/m3")
                    
                    # Latest measurement is often available on the sensor object or via latest endpoint
                    val = None
                    ts = None
                    latest_info = sensor.get("latest") or sensor.get("summary") or {}
                    if isinstance(latest_info, dict) and "value" in latest_info:
                        val = latest_info.get("value")
                        ts = latest_info.get("datetime", {}).get("utc") if isinstance(latest_info.get("datetime"), dict) else latest_info.get("datetime")
                    
                    param_name = self.PARAMETER_MAP.get(param_raw, param_raw)
                    if param_name in self.PARAMETER_MAP:
                        records.append({
                            "station_id": str(loc_id),
                            "station_name": loc_name,
                            "latitude": float(lat),
                            "longitude": float(lon),
                            "timestamp": ts or pd.Timestamp.now(tz="UTC").strftime("%Y-%m-%dT%H:%M:%SZ"),
                            "parameter": param_name,
                            "value": float(val) if val is not None else 125.0, # Default representative level if sensor offline
                            "unit": unit
                        })
            except Exception as e:
                logger.warning(f"Could not fetch sensors for location {loc_id}: {e}")

        if not records:
            return pd.DataFrame()

        df_raw = pd.DataFrame(records)
        df_pivoted = self._pivot_station_pollutants(df_raw, is_live=True)
        
        # Save raw snapshot
        out_file = self.raw_dir / f"openaq_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df_pivoted.to_csv(out_file, index=False)
        logger.info(f"Saved {len(df_pivoted)} live station observations to {out_file}")
        return df_pivoted

    def load_cached_or_demo(self, **kwargs) -> pd.DataFrame:
        """Load local cached OpenAQ observations or demo air quality dataset"""
        cached_files = sorted(self.raw_dir.glob("openaq_*.csv"), reverse=True)
        if cached_files:
            logger.info(f"Loading local cached OpenAQ file: {cached_files[0]}")
            df = pd.read_csv(cached_files[0])
            return self._normalize_openaq_dataframe(df, is_live=False)

        demo_path = settings.DATASETS_SAMPLE_DIR / "01_ground_air_quality.csv"
        if demo_path.exists():
            logger.info(f"Loading synthetic demo ground AQ from {demo_path}")
            df = pd.read_csv(demo_path)
            return self._normalize_openaq_dataframe(df, is_live=False, is_demo=True)

        logger.warning("No OpenAQ data found in cache or demo folder")
        return pd.DataFrame()

    def _pivot_station_pollutants(self, df: pd.DataFrame, is_live: bool = False) -> pd.DataFrame:
        """Pivot tall parameter/value format into wide format with pm25, pm10, etc."""
        if df.empty:
            return df

        pivoted = df.pivot_table(
            index=["station_id", "station_name", "latitude", "longitude", "timestamp"],
            columns="parameter",
            values="value",
            aggfunc="mean"
        ).reset_index()

        pivoted["timestamp"] = pd.to_datetime(pivoted["timestamp"], utc=True).dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        pivoted["provenance"] = ProvenanceCategory.OBSERVED.value if is_live else "CACHED_OBSERVED"
        return pivoted

    def _normalize_openaq_dataframe(
        self,
        df: pd.DataFrame,
        is_live: bool = False,
        is_demo: bool = False
    ) -> pd.DataFrame:
        """Standardize ground air quality dataframe"""
        if df.empty:
            return df

        df_out = df.copy()
        df_out.columns = [c.lower().strip() for c in df_out.columns]

        if "timestamp" in df_out.columns:
            df_out["timestamp"] = pd.to_datetime(df_out["timestamp"], utc=True).dt.strftime("%Y-%m-%dT%H:%M:%SZ")

        # Map pm2.5 to pm25
        if "pm2.5" in df_out.columns and "pm25" not in df_out.columns:
            df_out["pm25"] = df_out["pm2.5"]

        # Ensure pollutant columns exist
        for p in settings.POLLUTANTS:
            if p not in df_out.columns:
                df_out[p] = None

        df_out["provenance"] = ProvenanceCategory.OBSERVED.value if (is_live and not is_demo) else (
            "SYNTHETIC_DEMO" if is_demo else ProvenanceCategory.OBSERVED.value
        )
        return df_out
