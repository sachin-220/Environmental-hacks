"""
Unit tests for WRF-Chem NetCDF state extraction and Phase 1 Inversion Engine integration
"""
from pathlib import Path
import pytest
from models.wrfchem.coupled_runner import WRFChemWorkflowRunner
from models.wrfchem.extractor import WRFChemStateExtractor
from schemas.canonical import CanonicalHourlySchema, CANONICAL_COLUMNS


def test_wrfout_netcdf_extraction(tmp_path: Path):
    runner = WRFChemWorkflowRunner()
    test_nc = tmp_path / "wrfout_test.nc"
    runner.generate_synthetic_wrfout_fixture(test_nc, start_date="2023-11-01_00:00:00", hours=3, is_control=False)
    
    assert test_nc.exists()

    df = WRFChemStateExtractor.extract_from_wrfout(test_nc, domain_id="D03")
    assert not df.empty
    assert len(df) > 0

    # Verify canonical columns presence
    assert "timestamp" in df.columns
    assert "grid_id" in df.columns
    assert "temperature_2m" in df.columns
    assert "boundary_layer_height" in df.columns
    assert "inversion_strength" in df.columns
    assert "stability_index" in df.columns
    assert "pm25" in df.columns
    assert "pm10" in df.columns
    assert "o3" in df.columns
    assert "no2" in df.columns
    assert "so2" in df.columns
    assert "co" in df.columns
    assert "provenance" in df.columns
    assert df.iloc[0]["provenance"] == "MODELLED"
