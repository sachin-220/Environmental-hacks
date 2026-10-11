"""
Unit tests for data quality validation, range limits, and quality flags
"""
import pytest
import pandas as pd
from processing.quality import QualityControlValidator
from schemas.canonical import QualityFlag


def test_validate_record_valid():
    rec = {
        "timestamp": "2026-10-15T12:00:00Z",
        "latitude": 28.61,
        "longitude": 77.21,
        "temperature_2m": 298.15,
        "dewpoint_2m": 290.15,
        "pm25": 120.0,
        "pm10": 200.0,
        "surface_pressure": 1005.0
    }
    flag, issues = QualityControlValidator.validate_record(rec)
    assert flag == QualityFlag.VALID
    assert len(issues) == 0


def test_validate_record_suspect_dewpoint():
    rec = {
        "timestamp": "2026-10-15T12:00:00Z",
        "latitude": 28.61,
        "longitude": 77.21,
        "temperature_2m": 290.0,
        "dewpoint_2m": 305.0, # Dewpoint exceeds ambient temperature!
        "pm25": 100.0,
        "pm10": 150.0
    }
    flag, issues = QualityControlValidator.validate_record(rec)
    assert flag == QualityFlag.SUSPECT
    assert any("Dewpoint" in iss for iss in issues)


def test_validate_record_pm25_exceeds_pm10():
    rec = {
        "timestamp": "2026-10-15T12:00:00Z",
        "latitude": 28.61,
        "longitude": 77.21,
        "pm25": 350.0, # PM2.5 > PM10
        "pm10": 100.0
    }
    flag, issues = QualityControlValidator.validate_record(rec)
    assert flag == QualityFlag.SUSPECT
    assert any("exceeds PM10" in iss for iss in issues)


def test_clean_dataframe_duplicates():
    df = pd.DataFrame([
        {"timestamp": "2026-10-15T12:00:00Z", "latitude": 28.61, "longitude": 77.21, "grid_id": "G1", "pm25": 100.0},
        {"timestamp": "2026-10-15T12:00:00Z", "latitude": 28.61, "longitude": 77.21, "grid_id": "G1", "pm25": 100.0} # Exact duplicate
    ])
    cleaned, report = QualityControlValidator.clean_dataframe(df)
    assert len(cleaned) == 1
    assert report["duplicates_removed"] == 1
