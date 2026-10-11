"""
Unit tests for two-way aerosol-radiation feedback diagnostics and differential metrics
"""
import pytest
import pandas as pd
import numpy as np
from models.wrfchem.feedback_diagnostics import TwoWayFeedbackDiagnostics


def test_feedback_comparison_differential():
    # Construct coupled and control tables showing physical feedback responses
    # Coupled: Dimming (lower SW, lower T2), shallower PBL, higher trapped PM2.5
    timestamps = ["2023-11-01T12:00:00Z", "2023-11-01T13:00:00Z"]
    
    coupled_df = pd.DataFrame([
        {"timestamp": timestamps[0], "grid_id": "D03_R10_C10", "temperature_2m": 296.0, "boundary_layer_height": 450.0, "solar_radiation": 580.0, "wind_speed_10m": 2.1, "pm25": 240.0, "o3": 38.0},
        {"timestamp": timestamps[1], "grid_id": "D03_R10_C10", "temperature_2m": 296.5, "boundary_layer_height": 500.0, "solar_radiation": 620.0, "wind_speed_10m": 2.3, "pm25": 230.0, "o3": 42.0}
    ])

    control_df = pd.DataFrame([
        {"timestamp": timestamps[0], "grid_id": "D03_R10_C10", "temperature_2m": 297.5, "boundary_layer_height": 600.0, "solar_radiation": 720.0, "wind_speed_10m": 2.5, "pm25": 190.0, "o3": 46.0},
        {"timestamp": timestamps[1], "grid_id": "D03_R10_C10", "temperature_2m": 298.0, "boundary_layer_height": 680.0, "solar_radiation": 780.0, "wind_speed_10m": 2.8, "pm25": 180.0, "o3": 50.0}
    ])

    res = TwoWayFeedbackDiagnostics.compare_coupled_vs_control(coupled_df, control_df)
    summary = res["summary"]

    assert summary["mean_delta_temperature_k"] < 0.0 # Surface cooling
    assert summary["mean_delta_solar_radiation_wm2"] < 0.0 # Radiative dimming
    assert summary["mean_delta_pbl_height_m"] < 0.0 # PBL suppression
    assert summary["mean_delta_pm25_ug_m3"] > 0.0 # Trapping amplification
    assert summary["pm25_coupling_enhancement_percent"] > 20.0 # ~+26% PM2.5 increase
    assert summary["coupling_strength_index"] > 50.0
    assert summary["feedback_verification_status"] == "CONFIRMED_PHYSICAL_COUPLING"
