"""
Unit tests for anthropogenic emissions and biomass burning plume mappings
"""
import pytest
from models.wrfchem.emissions_mapping import WRFChemEmissionMapper


def test_anthropogenic_emissions_mapping():
    anthro = {
        "anthro_nox": 30.0,
        "anthro_so2": 15.0,
        "anthro_co": 80.0,
        "anthro_nh3": 5.0,
        "anthro_voc": 40.0,
        "anthro_bc": 2.5,
        "anthro_oc": 6.0
    }
    mapped = WRFChemEmissionMapper.map_anthropogenic_emissions(anthro)
    
    assert mapped["E_NO"] == 27.0 # 90% of NOx
    assert mapped["E_NO2"] == 3.0 # 10% of NOx
    assert mapped["E_SO2"] == 15.0
    assert mapped["E_CO"] == 80.0
    assert "E_TOLUENE" in mapped
    assert "E_HCHO" in mapped
    assert mapped["E_TOLUENE"] == 8.0 # 20% of VOC


def test_biomass_burning_plume_mapping():
    fire = {
        "latitude": 30.5,
        "longitude": 75.8,
        "frp": 150.0
    }
    plume = WRFChemEmissionMapper.map_biomass_burning_plume(fire)
    
    assert plume["fire_frp"] == 150.0
    assert plume["plume_top_height_m"] > 500.0 # Elevated injection height
    assert plume["fire_pm25_flux_g_s"] > 0.0
    assert plume["fire_co_flux_g_s"] > 0.0
    assert plume["fire_bc_flux_g_s"] > 0.0
