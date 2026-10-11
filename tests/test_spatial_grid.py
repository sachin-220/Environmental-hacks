"""
Unit tests for spatial grid generation, KDTree indexing, and distance/bearing calculations
"""
import pytest
import pandas as pd
from processing.spatial_grid import (
    SpatialGridManager,
    haversine_distance_km,
    calculate_bearing_degrees,
    d03_grid_manager
)
from config.settings import settings


def test_haversine_distance():
    # Distance between Connaught Place (28.6315, 77.2167) and IGI Airport (28.5562, 77.1000) ~ 14 km
    d = haversine_distance_km(28.6315, 77.2167, 28.5562, 77.1000)
    assert 12.0 < d < 16.0


def test_bearing_calculation():
    # Due North: 0 deg
    assert round(calculate_bearing_degrees(28.0, 77.0, 29.0, 77.0)) == 0
    # Due East: 90 deg
    assert round(calculate_bearing_degrees(28.0, 77.0, 28.0, 78.0)) == 90
    # Due South: 180 deg
    assert round(calculate_bearing_degrees(28.0, 77.0, 27.0, 77.0)) == 180


def test_grid_generation_and_nearest_cell():
    mgr = d03_grid_manager
    assert not mgr.grid_df.empty
    assert "grid_id" in mgr.grid_df.columns
    assert "latitude" in mgr.grid_df.columns
    assert "longitude" in mgr.grid_df.columns

    # Look up nearest cell to central Delhi
    cell = mgr.find_nearest_grid_cell(28.6139, 77.2090)
    assert "grid_id" in cell
    assert cell["distance_km"] < 5.0 # Must be within 5 km of grid cell center for 3km resolution


def test_map_points_to_grid():
    mgr = d03_grid_manager
    points = pd.DataFrame([
        {"station_id": "S1", "latitude": 28.63, "longitude": 77.22},
        {"station_id": "S2", "latitude": 28.55, "longitude": 77.10}
    ])
    mapped = mgr.map_points_to_grid(points)
    assert "grid_id" in mapped.columns
    assert len(mapped) == 2
