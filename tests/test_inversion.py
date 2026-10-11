"""
Unit tests for atmospheric inversion engine and stability classification
"""
import pytest
from processing.inversion import AtmosphericInversionEngine, pressure_to_altitude_hypsometric


def test_hypsometric_equation():
    # 1000 hPa to 850 hPa at ~290 K should be ~1400m
    z = pressure_to_altitude_hypsometric(850.0, 290.0, 1000.0)
    assert 1200.0 < z < 1600.0


def test_inversion_detection_true():
    # Sounding with surface temperature inversion:
    # 1000 hPa (110m): 285 K
    # 950 hPa (540m): 292 K (+7 K inversion!)
    # 900 hPa (1000m): 290 K
    levels = [1000, 950, 900]
    temps = [285.0, 292.0, 290.0]
    winds = [2.0, 4.0, 6.0]
    
    diag = AtmosphericInversionEngine.compute_inversion_profile(levels, temps, winds, pbl_height_m=250.0)
    assert diag["inversion_presence"] == 1
    assert diag["inversion_strength"] == 7.0
    assert diag["inversion_height"] == 110.0
    assert diag["inversion_top"] == 540.0
    assert diag["stability_index"] in ["STABLE", "VERY_STABLE"]
    assert diag["boundary_layer_height"] == 250.0


def test_inversion_detection_false_normal_lapse():
    # Normal decreasing temperature profile (Standard atmosphere)
    # 1000 hPa (110m): 300 K
    # 950 hPa (540m): 296 K
    # 900 hPa (1000m): 292 K
    levels = [1000, 950, 900]
    temps = [300.0, 296.0, 292.0]
    
    diag = AtmosphericInversionEngine.compute_inversion_profile(levels, temps)
    assert diag["inversion_presence"] == 0
    assert diag["inversion_strength"] == 0.0
    assert diag["stability_index"] in ["NEUTRAL", "UNSTABLE"]
