"""
Data Quality Validation and Quality Flagging Pipeline
"""
from typing import Dict, Any, List, Tuple
import numpy as np
import pandas as pd
from schemas.canonical import QualityFlag
from config.logging_config import get_logger

logger = get_logger("processing.quality")

PHYSICAL_LIMITS: Dict[str, Tuple[float, float]] = {
    "temperature_2m": (220.0, 335.0),       # Kelvin
    "dewpoint_2m": (200.0, 320.0),          # Kelvin
    "surface_pressure": (800.0, 1100.0),    # hPa
    "relative_humidity": (0.0, 100.0),      # %
    "precipitation": (0.0, 300.0),          # mm/h
    "solar_radiation": (0.0, 1400.0),       # W/m2
    "cloud_cover": (0.0, 1.0),              # fraction
    "wind_speed_10m": (0.0, 75.0),          # m/s
    "boundary_layer_height": (10.0, 6000.0), # meters
    "inversion_strength": (0.0, 35.0),      # Kelvin
    "pm25": (0.0, 1500.0),                  # ug/m3
    "pm10": (0.0, 3000.0),                  # ug/m3
    "o3": (0.0, 600.0),                     # ug/m3
    "no2": (0.0, 800.0),                    # ug/m3
    "so2": (0.0, 1000.0),                   # ug/m3
    "co": (0.0, 100.0),                     # mg/m3
    "fire_frp": (0.0, 10000.0),             # MW
    "latitude": (25.0, 35.0),               # Regional lat degrees
    "longitude": (70.0, 82.0),              # Regional lon degrees
}


class QualityControlValidator:
    """Rigorous physical range validation and quality classification"""

    @classmethod
    def validate_record(cls, record: Dict[str, Any]) -> Tuple[QualityFlag, List[str]]:
        """Validate an individual record dictionary against physical bounds"""
        issues = []
        is_suspect = False
        
        # Check required fields
        if not record.get("timestamp"):
            issues.append("Missing timestamp")
            return QualityFlag.MISSING, issues
            
        lat = record.get("latitude")
        lon = record.get("longitude")
        if lat is None or lon is None or np.isnan(lat) or np.isnan(lon):
            issues.append("Invalid or missing coordinates")
            return QualityFlag.MISSING, issues

        if not (PHYSICAL_LIMITS["latitude"][0] <= lat <= PHYSICAL_LIMITS["latitude"][1]):
            issues.append(f"Latitude {lat} out of study domain bounds")
            is_suspect = True

        if not (PHYSICAL_LIMITS["longitude"][0] <= lon <= PHYSICAL_LIMITS["longitude"][1]):
            issues.append(f"Longitude {lon} out of study domain bounds")
            is_suspect = True

        for var, (low, high) in PHYSICAL_LIMITS.items():
            val = record.get(var)
            if val is not None and not (isinstance(val, (int, float)) and np.isnan(val)):
                if val < low or val > high:
                    issues.append(f"Variable '{var}' value {val} outside physical bounds [{low}, {high}]")
                    is_suspect = True

        # Logical consistency checks
        t2m = record.get("temperature_2m")
        d2m = record.get("dewpoint_2m")
        if t2m is not None and d2m is not None and not (np.isnan(t2m) or np.isnan(d2m)):
            if d2m > (t2m + 0.5): # Dewpoint cannot physically exceed ambient temperature
                issues.append(f"Dewpoint ({d2m}K) exceeds ambient temperature ({t2m}K)")
                is_suspect = True

        pm25 = record.get("pm25")
        pm10 = record.get("pm10")
        if pm25 is not None and pm10 is not None and not (np.isnan(pm25) or np.isnan(pm10)):
            if pm25 > (pm10 + 5.0): # PM2.5 is a physical sub-fraction of PM10
                issues.append(f"PM2.5 ({pm25}) exceeds PM10 ({pm10}) beyond measurement tolerance")
                is_suspect = True

        flag = QualityFlag.SUSPECT if is_suspect else QualityFlag.VALID
        return flag, issues

    @classmethod
    def clean_dataframe(cls, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Validate and annotate a DataFrame with quality flags without silently destroying records.
        """
        if df.empty:
            return df, {"total_rows": 0, "valid": 0, "suspect": 0, "missing": 0}

        report = {
            "total_rows": len(df),
            "duplicates_removed": 0,
            "suspect_count": 0,
            "valid_count": 0,
            "issues": []
        }

        # Deduplicate on timestamp + grid_id/station_id
        subset_cols = [c for c in ["timestamp", "grid_id", "station_id", "latitude", "longitude"] if c in df.columns]
        initial_len = len(df)
        df_clean = df.drop_duplicates(subset=subset_cols).copy()
        report["duplicates_removed"] = initial_len - len(df_clean)

        if "quality_flag" not in df_clean.columns:
            df_clean["quality_flag"] = QualityFlag.VALID.value

        flags = []
        for idx, row in df_clean.iterrows():
            flag, issues = cls.validate_record(row.to_dict())
            flags.append(flag.value)
            if issues:
                report["issues"].append(f"Row {idx}: {', '.join(issues)}")

        df_clean["quality_flag"] = flags
        report["suspect_count"] = int((df_clean["quality_flag"] == QualityFlag.SUSPECT.value).sum())
        report["valid_count"] = int((df_clean["quality_flag"] == QualityFlag.VALID.value).sum())

        logger.info(
            f"Quality control complete: {report['valid_count']} valid, "
            f"{report['suspect_count']} suspect, {report['duplicates_removed']} duplicates removed"
        )
        return df_clean, report
