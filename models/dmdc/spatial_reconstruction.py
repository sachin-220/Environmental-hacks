"""
Spatial State Reconstruction and Grid-Level (D03) Mapping Engine
"""
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd

from config.logging_config import get_logger
from models.dmdc.dmdc_model import DMDcModel
from models.dmdc.preprocessing import DMDcPreprocessor
from models.dmdc.aqi import NationalAQICalculator

logger = get_logger("models.dmdc.spatial_reconstruction")


class SpatialReconstructionEngine:
    """
    Reconstructs full-resolution 3-km D03 spatial grid fields across Delhi NCR.
    Leverages vectorized batch matrix operations:
        X_{t+1} = X_t @ A^T + U_t @ B^T
    enabling instantaneous 72-hour spatial rollouts for all 3,600 grid cells simultaneously.
    """

    def __init__(
        self,
        model: DMDcModel,
        preprocessor: DMDcPreprocessor,
        grid_metadata_df: Optional[pd.DataFrame] = None
    ):
        self.model = model
        self.preprocessor = preprocessor
        self.state_vars = self.preprocessor.state_vars
        self.control_vars = self.preprocessor.control_vars
        
        # Grid layout (3600 cells for D03 60x60)
        self.grid_df = grid_metadata_df
        if self.grid_df is not None and not self.grid_df.empty:
            self._init_grid_structure(self.grid_df)
        else:
            self.n_cells = 3600
            self.grid_ids = [f"D03_R{r:02d}_C{c:02d}" for r in range(60) for c in range(60)]

    def _init_grid_structure(self, df: pd.DataFrame):
        """Extract unique spatial coordinates for D03"""
        unique_cells = df[["grid_id", "latitude", "longitude"]].drop_duplicates().sort_values("grid_id")
        self.grid_df = unique_cells.reset_index(drop=True)
        self.n_cells = len(self.grid_df)
        self.grid_ids = self.grid_df["grid_id"].tolist()

    def batch_rollout_spatial(
        self,
        X0_grid: np.ndarray,      # (N_cells, n_states) in physical units
        U_grid_seq: np.ndarray,   # (horizon, N_cells, n_controls) in physical units
        horizon: int = 72
    ) -> np.ndarray:
        """
        Executes vectorized batch recursive rollout across all spatial cells simultaneously:
        Returns:
            trajectory: (horizon, N_cells, n_states) in physical units
        """
        N_cells = X0_grid.shape[0]
        n_states = len(self.state_vars)
        
        # 1. Scale initial conditions and control sequences
        # Transform: (X - mean) / scale
        X0_scaled = (X0_grid - self.preprocessor.state_mean) / self.preprocessor.state_scale
        U_scaled_seq = np.zeros_like(U_grid_seq, dtype=np.float64)
        for h in range(horizon):
            U_scaled_seq[h] = (U_grid_seq[h] - self.preprocessor.control_mean) / self.preprocessor.control_scale

        # 2. Vectorized matrix recursion: X_{t+1} = X_t @ A^T + U_t @ B^T
        A_T = self.model.A.T  # (n_states, n_states)
        B_T = self.model.B.T  # (n_controls, n_states)

        trajectory_scaled = np.zeros((horizon, N_cells, n_states), dtype=np.float64)
        current_X = X0_scaled.copy()

        for h in range(horizon):
            U_h = U_scaled_seq[h]
            # (N_cells, n_states) @ (n_states, n_states) + (N_cells, n_controls) @ (n_controls, n_states)
            next_X = (current_X @ A_T) + (U_h @ B_T)
            trajectory_scaled[h] = next_X
            current_X = next_X

        # 3. Inverse transform back to physical units
        trajectory_phys = (trajectory_scaled * self.preprocessor.state_scale) + self.preprocessor.state_mean
        
        # Clip negative concentrations
        trajectory_phys = np.maximum(0.0, trajectory_phys)
        return trajectory_phys

    def reconstruct_spatial_dataframe(
        self,
        trajectory_phys: np.ndarray,
        horizon_step: int = 24,
        timestamp: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Formats spatial forecast at specified horizon step into a Pandas DataFrame.
        """
        step_idx = min(horizon_step - 1, trajectory_phys.shape[0] - 1)
        snapshot = trajectory_phys[step_idx]  # (N_cells, n_states)

        records = []
        for i in range(len(snapshot)):
            row = {
                "grid_id": self.grid_ids[i] if i < len(self.grid_ids) else f"CELL_{i:04d}",
                "horizon_step": horizon_step,
                "timestamp": timestamp or ""
            }
            if self.grid_df is not None and i < len(self.grid_df):
                row["latitude"] = float(self.grid_df.iloc[i]["latitude"])
                row["longitude"] = float(self.grid_df.iloc[i]["longitude"])
            
            # Map state variables
            for v_idx, var_name in enumerate(self.state_vars):
                row[var_name] = round(float(snapshot[i, v_idx]), 2)
            
            # Compute NAQI
            aqi_res = NationalAQICalculator.evaluate_aqi(row)
            row["aqi"] = aqi_res["aqi"]
            row["aqi_category"] = aqi_res["category"]
            row["dominant_pollutant"] = aqi_res["dominant_pollutant"]

            records.append(row)

        return pd.DataFrame(records)

    def evaluate_spatial_metrics(
        self,
        pred_phys: np.ndarray,   # (N_cells, n_states)
        true_phys: np.ndarray    # (N_cells, n_states)
    ) -> Dict[str, Any]:
        """
        Computes spatial agreement metrics: cell-level MAE/RMSE, spatial Pearson correlation, regional bias.
        """
        metrics = {}
        for v_idx, var in enumerate(self.state_vars):
            p = pred_phys[:, v_idx]
            y = true_phys[:, v_idx]
            
            mae = float(np.mean(np.abs(y - p)))
            rmse = float(np.sqrt(np.mean((y - p)**2)))
            bias = float(np.mean(p - y))
            
            # Spatial Pearson correlation
            std_p = np.std(p)
            std_y = np.std(y)
            if std_p > 1e-6 and std_y > 1e-6:
                corr = float(np.corrcoef(y, p)[0, 1])
            else:
                corr = 0.0

            metrics[var] = {
                "spatial_mae": round(mae, 3),
                "spatial_rmse": round(rmse, 3),
                "spatial_bias": round(bias, 3),
                "spatial_correlation": round(corr, 4)
            }
        return metrics
