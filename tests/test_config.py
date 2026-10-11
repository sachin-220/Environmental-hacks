"""
Unit tests for SAMEER configuration, domains, and credential validation
"""
import pytest
from config.settings import Settings, settings, DomainBounds


def test_domain_bounds():
    bounds = DomainBounds(west=73.5, south=27.0, east=78.5, north=32.5)
    # Delhi center inside
    assert bounds.contains(28.6139, 77.2090) is True
    # Out of bounds
    assert bounds.contains(19.0, 72.8) is False # Mumbai
    assert bounds.contains(35.0, 77.0) is False # Kashmir


def test_nested_domains_hierarchy():
    assert len(settings.NESTED_DOMAINS) == 3
    d01, d02, d03 = settings.NESTED_DOMAINS
    assert d01.domain_id == "D01"
    assert d01.resolution_km == 27.0
    assert d02.domain_id == "D02"
    assert d02.resolution_km == 9.0
    assert d03.domain_id == "D03"
    assert d03.resolution_km == 3.0


def test_masked_credentials():
    masked = settings.get_masked_credentials()
    assert "FIRMS_MAP_KEY" in masked
    assert "OPENAQ_API_KEY" in masked
    assert "CDS_API_KEY" in masked
    # Ensure sensitive raw strings are not exposed
    assert masked["FIRMS_MAP_KEY"] != "super_secret_actual_key_12345"


def test_validate_credentials_demo_vs_live():
    # In demo mode, no missing errors raised for live running
    test_settings = Settings(SAMEER_MODE="demo")
    missing = test_settings.validate_live_credentials()
    assert len(missing) == 0

    # In live mode with demo keys, should report missing
    test_settings_live = Settings(SAMEER_MODE="live", FIRMS_MAP_KEY="demo_firms_key")
    missing_live = test_settings_live.validate_live_credentials()
    assert "FIRMS_MAP_KEY" in missing_live
