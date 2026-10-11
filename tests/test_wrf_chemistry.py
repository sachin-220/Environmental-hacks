"""
Unit tests for WRF-Chem chemical mechanisms, species mapping, and gas-aerosol conversions
"""
import pytest
from models.wrfchem.chemistry_config import (
    MECHANISM_MOZART_MOSAIC,
    MECHANISM_RADM2_MADE,
    WRFChemCoupledConfig
)
from models.wrfchem.emissions_mapping import WRFChemEmissionMapper


def test_chemistry_mechanisms():
    assert MECHANISM_MOZART_MOSAIC.chem_opt == 108
    assert MECHANISM_MOZART_MOSAIC.feedback_supported is True
    assert MECHANISM_RADM2_MADE.chem_opt == 202
    assert MECHANISM_RADM2_MADE.feedback_supported is True

    cfg = WRFChemCoupledConfig()
    assert cfg.aer_ra_feedback == 1
    assert cfg.phot_opt == 2 # Fast-J


def test_cams_to_wrfchem_mapping():
    cams_data = {
        "cams_o3": 60.0,    # ug/m3
        "cams_no2": 45.0,   # ug/m3
        "cams_co": 1.5,     # mg/m3
        "cams_pm25": 180.0  # ug/m3
    }
    mapped = WRFChemEmissionMapper.map_cams_to_wrfchem(cams_data, pressure_hpa=1013.25, temp_k=298.15)
    
    assert "o3" in mapped and mapped["o3"] > 0.0
    assert "no2" in mapped and mapped["no2"] > 0.0
    assert "no" in mapped and mapped["no"] > 0.0
    assert "co" in mapped and mapped["co"] > 0.0
    assert "pm2_5_dry" in mapped and mapped["pm2_5_dry"] == 180.0
    assert "so4_a01" in mapped
    assert "bc_a01" in mapped
    assert "oc_a01" in mapped
