"""
Temporal Alignment and Multi-Source Timestamp Normalization Engine
"""
from typing import Optional, List, Dict, Any
import pandas as pd
import numpy as np
from schemas.canonical import QualityFlag
from config.logging_config import get_logger

logger = get_logger("processing.temporal_alignment")


class TemporalAligner:
    """Standardizes multi-cadence temporal streams to regular hourly UTC intervals"""

    @classmethod
    def to_utc_iso(cls, dt_series: pd.Series) -> pd.Series:
        """Parse diverse datetime formats and convert to UTC ISO-8601 string"""
        def parse_single(val):
            if pd.isna(val):
                return None
            try:
                dt = pd.to_datetime(val, utc=True)
                return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
            except Exception:
                return None
                
        return dt_series.apply(parse_single)

    @classmethod
    def aggregate_to_hourly(
        cls,
        df: pd.DataFrame,
        time_col: str = "timestamp",
        group_cols: Optional[List[str]] = None,
        agg_methods: Optional[Dict[str, str]] = None
    ) -> pd.DataFrame:
        """
        Aggregate sub-hourly or irregular observations to exact top-of-the-hour buckets.
        Calculates arithmetic mean for numeric columns and preserves station/grid keys.
        """
        if df.empty or time_col not in df.columns:
            return df

        df_work = df.copy()
        df_work["dt_utc"] = pd.to_datetime(df_work[time_col], utc=True, errors="coerce")
        df_work = df_work.dropna(subset=["dt_utc"])
        
        # Floor to nearest hour (e.g. 10:15 -> 10:00)
        df_work["hour_utc"] = df_work["dt_utc"].dt.floor("h")

        group_keys = ["hour_utc"]
        if group_cols:
            for gc in group_cols:
                if gc in df_work.columns:
                    group_keys.append(gc)

        numeric_cols = df_work.select_dtypes(include=[np.number]).columns.tolist()
        # Exclude key columns
        numeric_cols = [c for c in numeric_cols if c not in group_keys]

        default_agg = {col: "mean" for col in numeric_cols}
        if agg_methods:
            default_agg.update(agg_methods)

        # Non-numeric columns: take first
        non_numeric = [c for c in df_work.columns if c not in numeric_cols and c not in group_keys and c != "dt_utc"]
        for c in non_numeric:
            default_agg[c] = "first"

        agg_df = df_work.groupby(group_keys, as_index=False).agg(default_agg)
        agg_df["original_timestamp"] = agg_df["hour_utc"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        agg_df["timestamp"] = agg_df["original_timestamp"]
        agg_df["processed_timestamp"] = pd.Timestamp.now(tz="UTC").strftime("%Y-%m-%dT%H:%M:%SZ")
        agg_df["processing_method"] = "HOURLY_MEAN_AGGREGATION"

        logger.info(f"Aggregated {len(df)} raw records into {len(agg_df)} hourly buckets")
        return agg_df

    @classmethod
    def interpolate_short_gaps(
        cls,
        df: pd.DataFrame,
        value_cols: List[str],
        max_gap_hours: int = 2,
        time_col: str = "timestamp"
    ) -> pd.DataFrame:
        """
        Linearly interpolate small missing gaps (<= max_gap_hours) strictly forward in time.
        Avoids future-data leakage by setting a limit and annotating quality_flag as IMPUTED.
        """
        if df.empty or time_col not in df.columns:
            return df

        df_sorted = df.sort_values(by=time_col).copy()
        
        for col in value_cols:
            if col in df_sorted.columns:
                was_na = df_sorted[col].isna()
                # Interpolate only up to max_gap_hours forward
                df_sorted[col] = df_sorted[col].interpolate(method="linear", limit=max_gap_hours, limit_direction="forward")
                now_filled = was_na & df_sorted[col].notna()
                if "quality_flag" in df_sorted.columns and now_filled.any():
                    df_sorted.loc[now_filled, "quality_flag"] = QualityFlag.IMPUTED.value

        return df_sorted
