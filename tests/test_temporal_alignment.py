"""
Unit tests for temporal alignment and hourly aggregation
"""
import pytest
import pandas as pd
from processing.temporal_alignment import TemporalAligner


def test_to_utc_iso():
    s = pd.Series(["2026-10-15 14:30:00", "2026-10-15T14:30:00+05:30"])
    iso = TemporalAligner.to_utc_iso(s)
    assert iso.iloc[0] == "2026-10-15T14:30:00Z"
    assert iso.iloc[1] == "2026-10-15T09:00:00Z"


def test_aggregate_to_hourly():
    # 3 observations within the 10:00 - 10:59 hour
    df = pd.DataFrame([
        {"timestamp": "2026-10-15T10:10:00Z", "station_id": "S1", "pm25": 100.0, "temp": 20.0},
        {"timestamp": "2026-10-15T10:30:00Z", "station_id": "S1", "pm25": 120.0, "temp": 22.0},
        {"timestamp": "2026-10-15T10:50:00Z", "station_id": "S1", "pm25": 140.0, "temp": 24.0}
    ])
    
    hourly = TemporalAligner.aggregate_to_hourly(df, group_cols=["station_id"])
    assert len(hourly) == 1
    assert hourly.iloc[0]["pm25"] == 120.0 # Mean of 100, 120, 140
    assert hourly.iloc[0]["temp"] == 22.0
    assert hourly.iloc[0]["timestamp"] == "2026-10-15T10:00:00Z"


def test_interpolate_short_gaps():
    df = pd.DataFrame([
        {"timestamp": "2026-10-15T10:00:00Z", "pm25": 100.0, "quality_flag": "VALID"},
        {"timestamp": "2026-10-15T11:00:00Z", "pm25": None, "quality_flag": "MISSING"},
        {"timestamp": "2026-10-15T12:00:00Z", "pm25": 120.0, "quality_flag": "VALID"}
    ])
    
    filled = TemporalAligner.interpolate_short_gaps(df, value_cols=["pm25"], max_gap_hours=2)
    assert filled.iloc[1]["pm25"] == 110.0
    assert filled.iloc[1]["quality_flag"] == "IMPUTED"
