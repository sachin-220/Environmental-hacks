"""
Unit tests for fire-to-wind transport diagnostics and plume scoring
"""
import pytest
import pandas as pd
from processing.plume import (
    FirePlumeTransportEngine,
    calculate_wind_speed_direction,
    circular_angular_difference
)


def test_wind_speed_direction():
    # Northerly wind (blowing from North towards South): u=0, v=-5 -> direction=360/0
    ws, wd = calculate_wind_speed_direction(0.0, -5.0)
    assert ws == 5.0
    assert wd == 0.0 or wd == 360.0

    # North-westerly wind (blowing from NW towards SE): u=3.53, v=-3.53 -> direction=315
    ws, wd = calculate_wind_speed_direction(3.5355, -3.5355)
    assert 4.9 < ws < 5.1
    assert 314.0 < wd < 316.0


def test_angular_difference():
    assert circular_angular_difference(10.0, 350.0) == 20.0
    assert circular_angular_difference(0.0, 180.0) == 180.0
    assert circular_angular_difference(90.0, 100.0) == 10.0


def test_fire_upwind_transport_evaluation():
    # Target: Central Delhi (28.61, 77.21)
    # Fire in Punjab: Ludhiana area (30.90, 75.85) -> North-West of Delhi (~285 km away, bearing ~145 deg towards Delhi)
    # Wind: From NW blowing towards SE (u=3.0, v=-3.0) -> wind blows directly towards Delhi!
    res = FirePlumeTransportEngine.evaluate_fire_transport(
        fire_lat=30.90,
        fire_lon=75.85,
        fire_frp=150.0,
        u_wind=3.0,
        v_wind=-3.0,
        target_lat=28.61,
        target_lon=77.21
    )
    
    assert res["is_upwind"] is True
    assert res["alignment_factor"] > 0.7
    assert res["transport_potency"] > 0.0


def test_regional_plume_score_aggregation():
    fires_df = pd.DataFrame([
        {"latitude": 30.90, "longitude": 75.85, "frp": 120.0, "confidence": 90.0},
        {"latitude": 30.20, "longitude": 75.00, "frp": 80.0, "confidence": 85.0}
    ])
    
    score = FirePlumeTransportEngine.compute_regional_plume_score(fires_df, u_wind=2.5, v_wind=-2.5)
    assert score["fire_count"] == 2
    assert score["upwind_fire_count"] == 2
    assert score["plume_transport_score"] > 0.0
