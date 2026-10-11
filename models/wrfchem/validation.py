"""
WRF-Chem Observational Validation and Statistical Assessment Engine
"""
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
from scipy import stats

from config.logging_config import get_logger

logger = get_logger("models.wrfchem.validation")


class WRFChemModelValidator:
    """
    Computes rigorous atmospheric modeling performance metrics
    comparing WRF-Chem simulation fields against ground observations and reanalysis.
    """

    @classmethod
    def compute_metrics(cls, simulated: np.ndarray, observed: np.ndarray) -> Dict[str, float]:
        """
        Calculate MAE, RMSE, Mean Bias (MB), Normalized Mean Bias (NMB %),
        Pearson r correlation, and Willmott Index of Agreement (d).
        """
        # Filter NaNs
        mask = (~np.isnan(simulated)) & (~np.isnan(observed))
        sim = simulated[mask]
        obs = observed[mask]

        if len(sim) < 2:
            return {
                "count": len(sim),
                "mae": 0.0,
                "rmse": 0.0,
                "mean_bias": 0.0,
                "nmb_percent": 0.0,
                "pearson_r": 0.0,
                "index_of_agreement": 0.0
            }

        n = len(sim)
        mae = float(np.mean(np.abs(sim - obs)))
        rmse = float(np.sqrt(np.mean((sim - obs) ** 2)))
        mb = float(np.mean(sim - obs))
        obs_sum = float(np.sum(obs))
        nmb = float((np.sum(sim - obs) / obs_sum * 100.0)) if obs_sum != 0 else 0.0
        
        # Pearson correlation
        if np.std(sim) > 0 and np.std(obs) > 0:
            r_val, _ = stats.pearsonr(sim, obs)
            r_val = float(r_val)
        else:
            r_val = 0.0

        # Willmott Index of Agreement (d)
        obs_mean = np.mean(obs)
        denom = np.sum((np.abs(sim - obs_mean) + np.abs(obs - obs_mean)) ** 2)
        numer = np.sum((sim - obs) ** 2)
        d_val = float(1.0 - (numer / denom)) if denom > 0 else 0.0

        return {
            "count": n,
            "mae": round(mae, 2),
            "rmse": round(rmse, 2),
            "mean_bias": round(mb, 2),
            "nmb_percent": round(nmb, 2),
            "pearson_r": round(r_val, 3),
            "index_of_agreement": round(d_val, 3)
        }

    @classmethod
    def validate_simulation(
        cls,
        model_df: pd.DataFrame,
        observed_df: pd.DataFrame,
        variables: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Evaluate full multi-variable simulation against ground observations table.
        """
        if model_df.empty or observed_df.empty:
            raise ValueError("Simulation and observation datasets cannot be empty.")

        target_vars = variables or ["pm25", "pm10", "o3", "no2", "temperature_2m", "wind_speed_10m"]
        
        # Match spatio-temporal coordinates
        join_keys = [k for k in ["timestamp", "grid_id"] if k in model_df.columns and k in observed_df.columns]
        if not join_keys:
            join_keys = ["timestamp"]

        merged = pd.merge(
            model_df,
            observed_df,
            on=join_keys,
            suffixes=("_sim", "_obs")
        )

        results = {}
        for var in target_vars:
            sim_col = f"{var}_sim" if f"{var}_sim" in merged.columns else var
            obs_col = f"{var}_obs" if f"{var}_obs" in merged.columns else var

            if sim_col in merged.columns and obs_col in merged.columns:
                sim_vals = merged[sim_col].astype(float).values
                obs_vals = merged[obs_col].astype(float).values
                stats_dict = cls.compute_metrics(sim_vals, obs_vals)
                results[var] = stats_dict

        logger.info(f"Simulation validation completed across {len(results)} parameters")
        return {
            "evaluated_pairs_count": len(merged),
            "variable_metrics": results
        }
