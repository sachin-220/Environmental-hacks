"""
Unit tests for data collectors and offline/demo normalization
"""
import pytest
import pandas as pd
from collectors.firms import FirmsCollector
from collectors.openaq import OpenAQCollector
from collectors.era5 import ERA5Collector
from collectors.cams import CAMSCollector
from collectors.gfas import GFASCollector
from collectors.emissions import EmissionsCollector


def test_firms_collector_normalization():
    collector = FirmsCollector()
    raw_df = pd.DataFrame([
        {
            "latitude": 30.5,
            "longitude": 75.8,
            "acq_date": "2026-10-25",
            "acq_time": "1230",
            "confidence": "h",
            "frp": 45.2,
            "instrument": "VIIRS"
        },
        # Out of bounds
        {
            "latitude": 15.2,
            "longitude": 77.0,
            "acq_date": "2026-10-25",
            "acq_time": "1230",
            "confidence": "n",
            "frp": 12.0,
            "instrument": "VIIRS"
        }
    ])
    
    norm = collector._normalize_firms_dataframe(raw_df, is_live=True)
    assert len(norm) == 1
    assert norm.iloc[0]["latitude"] == 30.5
    assert norm.iloc[0]["confidence"] == 95.0
    assert norm.iloc[0]["timestamp"] == "2026-10-25T12:30:00Z"
    assert norm.iloc[0]["provenance"] == "OBSERVED"


def test_openaq_collector_pivot():
    collector = OpenAQCollector()
    raw_records = pd.DataFrame([
        {"station_id": "LOC_1", "station_name": "ITO", "latitude": 28.62, "longitude": 77.24, "timestamp": "2026-10-25T10:00:00Z", "parameter": "pm25", "value": 150.0},
        {"station_id": "LOC_1", "station_name": "ITO", "latitude": 28.62, "longitude": 77.24, "timestamp": "2026-10-25T10:00:00Z", "parameter": "no2", "value": 45.0},
        {"station_id": "LOC_1", "station_name": "ITO", "latitude": 28.62, "longitude": 77.24, "timestamp": "2026-10-25T10:00:00Z", "parameter": "o3", "value": 30.0}
    ])
    
    pivoted = collector._pivot_station_pollutants(raw_records, is_live=True)
    assert len(pivoted) == 1
    assert pivoted.iloc[0]["pm25"] == 150.0
    assert pivoted.iloc[0]["no2"] == 45.0
    assert pivoted.iloc[0]["o3"] == 30.0
    assert pivoted.iloc[0]["provenance"] == "OBSERVED"


def test_collectors_demo_load():
    # Verify all collectors load offline demo datasets without making live API calls
    firms = FirmsCollector().load_cached_or_demo()
    assert not firms.empty
    
    openaq = OpenAQCollector().load_cached_or_demo()
    assert not openaq.empty
    
    era5 = ERA5Collector().load_cached_or_demo()
    assert not era5.empty
    
    cams = CAMSCollector().load_cached_or_demo()
    assert not cams.empty
    
    gfas = GFASCollector().load_cached_or_demo()
    assert not gfas.empty
    
    emissions = EmissionsCollector().load_cached_or_demo()
    assert not emissions.empty
