"""
WRF-Chem to Koopman/DMDc Training Trajectory Generator and Temporal Split Engine
"""
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import numpy as np
import pandas as pd

from config.settings import settings
from config.logging_config import get_logger

logger = get_logger("models.wrfchem.trajectory_builder")


class CoupledTrajectoryBuilder:
    """
    Transforms coupled WRF-Chem simulation time-series into state matrices X, X_prime,
    and exogenous control matrices U formatted specifically for Koopman/DMDc spectral learning.
    """

    # State Vector Features x(t) (Physical coupled state variables)
    STATE_VARIABLES = [
        "boundary_layer_height",
        "temperature_2m",
        "u_wind_10m",
        "v_wind_10m",
        "wind_speed_10m",
        "relative_humidity",
        "surface_pressure",
        "inversion_strength",
        "pm25",
        "pm10",
        "o3",
        "no2",
        "so2",
        "co",
        "cams_aerosol"
    ]

    # Exogenous Control / Policy Input Vector u(t) (Emissions, fire forcing, meteorology)
    CONTROL_VARIABLES = [
        "anthro_nox",
        "anthro_so2",
        "anthro_co",
        "anthro_voc",
        "fire_frp",
        "plume_transport_score",
        "solar_radiation",
        "precipitation"
    ]

    @classmethod
    def build_trajectories(
        cls,
        df: pd.DataFrame,
        train_ratio: float = 0.70,
        val_ratio: float = 0.15,
        test_ratio: float = 0.15
    ) -> Dict[str, Any]:
        """
        Extracts contiguous time-ordered state and control trajectories,
        split strictly chronologically to prevent future-data leakage.
        """
        if df.empty:
            raise ValueError("Input DataFrame is empty. Cannot construct coupled trajectories.")

        # Ensure sorted by timestamp and grid_id
        df_sorted = df.sort_values(by=["grid_id", "timestamp"]).copy()

        # Fill missing values with forward fill + zero fallback
        for col in cls.STATE_VARIABLES + cls.CONTROL_VARIABLES:
            if col not in df_sorted.columns:
                df_sorted[col] = 0.0
            else:
                df_sorted[col] = df_sorted[col].ffill().bfill().fillna(0.0)

        # Unique time steps
        unique_times = df_sorted["timestamp"].drop_duplicates().tolist()
        n_times = len(unique_times)
        
        if n_times < 3:
            raise ValueError(f"Need at least 3 unique time steps to build trajectories, got {n_times}")

        # Compute chronological split indices
        idx_train = int(n_times * train_ratio)
        idx_val = int(n_times * (train_ratio + val_ratio))

        train_times = set(unique_times[:idx_train])
        val_times = set(unique_times[idx_train:idx_val])
        test_times = set(unique_times[idx_val:])

        df_train = df_sorted[df_sorted["timestamp"].isin(train_times)].copy()
        df_val = df_sorted[df_sorted["timestamp"].isin(val_times)].copy()
        df_test = df_sorted[df_sorted["timestamp"].isin(test_times)].copy()

        def extract_matrices(split_df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
            """Construct X (t), X_prime (t+1), and U (t) matrices across grid cells"""
            X_list, X_prime_list, U_list = [], [], []
            
            for _, group in split_df.groupby("grid_id"):
                g_sorted = group.sort_values(by="timestamp")
                if len(g_sorted) < 2:
                    continue
                
                s_mat = g_sorted[cls.STATE_VARIABLES].values
                c_mat = g_sorted[cls.CONTROL_VARIABLES].values
                
                # Snapshot pairs: X_k = s[t], X_prime_k = s[t+1], U_k = c[t]
                X_list.append(s_mat[:-1])
                X_prime_list.append(s_mat[1:])
                U_list.append(c_mat[:-1])

            if X_list:
                X = np.vstack(X_list)
                X_prime = np.vstack(X_prime_list)
                U = np.vstack(U_list)
            else:
                X = np.empty((0, len(cls.STATE_VARIABLES)))
                X_prime = np.empty((0, len(cls.STATE_VARIABLES)))
                U = np.empty((0, len(cls.CONTROL_VARIABLES)))

            return X, X_prime, U

        X_train, X_p_train, U_train = extract_matrices(df_train)
        X_val, X_p_val, U_val = extract_matrices(df_val)
        X_test, X_p_test, U_test = extract_matrices(df_test)

        logger.info(
            f"Built training trajectories: Train snapshots={X_train.shape[0]} "
            f"(state_dim={X_train.shape[1]}, control_dim={U_train.shape[1]}), "
            f"Val snapshots={X_val.shape[0]}, Test snapshots={X_test.shape[0]}"
        )

        return {
            "splits": {
                "train_time_range": (unique_times[0], unique_times[idx_train-1]) if idx_train > 0 else ("", ""),
                "val_time_range": (unique_times[idx_train], unique_times[idx_val-1]) if idx_val > idx_train else ("", ""),
                "test_time_range": (unique_times[idx_val], unique_times[-1]) if n_times > idx_val else ("", "")
            },
            "train": {"X": X_train, "X_prime": X_p_train, "U": U_train, "dataframe": df_train},
            "val": {"X": X_val, "X_prime": X_p_val, "U": U_val, "dataframe": df_val},
            "test": {"X": X_test, "X_prime": X_p_test, "U": U_test, "dataframe": df_test},
            "state_variables": cls.STATE_VARIABLES,
            "control_variables": cls.CONTROL_VARIABLES
        }

    @classmethod
    def save_trajectories(cls, trajectories: Dict[str, Any], output_dir: Path) -> Path:
        """Save formatted trajectories to disk as Parquet and compressed NumPy archives"""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save training dataset to Parquet
        train_df = trajectories["train"]["dataframe"]
        parquet_path = output_dir / "wrfchem_coupled_trajectories.parquet"
        train_df.to_parquet(parquet_path, index=False)

        # Save NumPy snapshot matrices for fast Koopman/DMDc loading
        npz_path = output_dir / "wrfchem_dmdc_matrices.npz"
        np.savez_compressed(
            npz_path,
            X_train=trajectories["train"]["X"],
            X_prime_train=trajectories["train"]["X_prime"],
            U_train=trajectories["train"]["U"],
            X_val=trajectories["val"]["X"],
            X_prime_val=trajectories["val"]["X_prime"],
            U_val=trajectories["val"]["U"],
            X_test=trajectories["test"]["X"],
            X_prime_test=trajectories["test"]["X_prime"],
            U_test=trajectories["test"]["U"],
            state_vars=np.array(trajectories["state_variables"]),
            control_vars=np.array(trajectories["control_variables"])
        )
        logger.info(f"Saved coupled trajectories to {parquet_path} and {npz_path}")
        return output_dir
