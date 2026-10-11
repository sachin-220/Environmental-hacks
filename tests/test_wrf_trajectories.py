"""
Unit tests for coupled training trajectory building and chronological splits for DMDc
"""
from pathlib import Path
import pytest
import pandas as pd
import numpy as np
from models.wrfchem.trajectory_builder import CoupledTrajectoryBuilder


def test_trajectory_matrix_building(tmp_path: Path):
    # Construct 10-hour timeseries across 2 grid cells
    timestamps = [f"2023-11-01T{h:02d}:00:00Z" for h in range(10)]
    records = []
    for gid in ["D03_R00_C00", "D03_R00_C01"]:
        for i, ts in enumerate(timestamps):
            records.append({
                "timestamp": ts,
                "grid_id": gid,
                "boundary_layer_height": 400.0 + i * 10,
                "temperature_2m": 295.0 + i * 0.2,
                "u_wind_10m": 1.5,
                "v_wind_10m": -2.0,
                "wind_speed_10m": 2.5,
                "relative_humidity": 65.0,
                "surface_pressure": 1012.0,
                "inversion_strength": 2.5,
                "pm25": 150.0 + i * 5,
                "pm10": 240.0,
                "o3": 35.0,
                "no2": 40.0,
                "so2": 10.0,
                "co": 1.5,
                "cams_aerosol": 0.85,
                "anthro_nox": 25.0,
                "anthro_so2": 10.0,
                "anthro_co": 50.0,
                "anthro_voc": 30.0,
                "fire_frp": 120.0,
                "plume_transport_score": 60.0,
                "solar_radiation": 450.0,
                "precipitation": 0.0
            })

    df = pd.DataFrame(records)
    trajectories = CoupledTrajectoryBuilder.build_trajectories(df, train_ratio=0.7, val_ratio=0.15, test_ratio=0.15)

    assert "train" in trajectories
    assert "val" in trajectories
    assert "test" in trajectories
    
    X_train = trajectories["train"]["X"]
    X_prime_train = trajectories["train"]["X_prime"]
    U_train = trajectories["train"]["U"]

    assert X_train.shape[0] == X_prime_train.shape[0]
    assert X_train.shape[0] == U_train.shape[0]
    assert X_train.shape[1] == len(CoupledTrajectoryBuilder.STATE_VARIABLES)
    assert U_train.shape[1] == len(CoupledTrajectoryBuilder.CONTROL_VARIABLES)

    # Test saving trajectories to disk
    CoupledTrajectoryBuilder.save_trajectories(trajectories, tmp_path)
    assert (tmp_path / "wrfchem_coupled_trajectories.parquet").exists()
    assert (tmp_path / "wrfchem_dmdc_matrices.npz").exists()
