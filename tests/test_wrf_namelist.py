"""
Unit tests for WPS and WRF namelist construction and Fortran formatting
"""
from pathlib import Path
import pytest
from models.wrfchem.wps_builder import WPSNamelistBuilder
from models.wrfchem.wrf_namelist_builder import WRFNamelistBuilder


def test_wps_namelist_generation(tmp_path: Path):
    builder = WPSNamelistBuilder()
    content = builder.generate_namelist_content(
        start_date="2023-11-01_00:00:00",
        end_date="2023-11-04_00:00:00"
    )
    assert "&share" in content
    assert "&geogrid" in content
    assert "&ungrib" in content
    assert "&metgrid" in content
    assert "max_dom = 3" in content
    assert "dx = 27000" in content
    assert "map_proj = 'lambert'" in content

    # Test file writing
    out_file = tmp_path / "namelist.wps"
    builder.write_namelist_file(out_file)
    assert out_file.exists()


def test_wrf_namelist_generation(tmp_path: Path):
    builder = WRFNamelistBuilder()
    
    # Coupled namelist (aer_ra_feedback = 1)
    coupled = builder.generate_namelist_content(is_coupled=True)
    assert "&time_control" in coupled
    assert "&domains" in coupled
    assert "&physics" in coupled
    assert "&chem" in coupled
    assert "aer_ra_feedback                     = 1, 1, 1" in coupled
    assert "ra_lw_physics                       = 4, 4, 4" in coupled # RRTMG
    assert "ra_sw_physics                       = 4, 4, 4" in coupled # RRTMG
    assert "mp_physics                          = 10, 10, 10" in coupled # Morrison

    # Control namelist (aer_ra_feedback = 0)
    control = builder.generate_namelist_content(is_coupled=False)
    assert "aer_ra_feedback                     = 0, 0, 0" in control

    # File output test
    out_coupled = tmp_path / "namelist.input"
    builder.write_coupled_namelist(out_coupled)
    assert out_coupled.exists()
