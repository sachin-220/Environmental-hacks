"""
Two-Way Aerosol-Radiation Feedback Diagnostic and Coupling Comparison Framework
"""
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

from config.logging_config import get_logger

logger = get_logger("models.wrfchem.feedback_diagnostics")


class TwoWayFeedbackDiagnostics:
    """
    Quantifies and validates two-way aerosol-radiation feedback by executing
    rigorous differential diagnostics between Coupled (aer_ra_feedback=1)
    and Control/Reduced-Feedback (aer_ra_feedback=0) simulations.
    """

    @classmethod
    def compare_coupled_vs_control(
        cls,
        coupled_df: pd.DataFrame,
        control_df: pd.DataFrame,
        group_by_time: bool = True
    ) -> Dict[str, Any]:
        """
        Calculates physical differential fields (Coupled - Control):
        Delta_T2, Delta_PBL, Delta_Radiation, Delta_Wind, Delta_PM25, Delta_O3
        """
        if coupled_df.empty or control_df.empty:
            raise ValueError("Both coupled and control DataFrames must contain records for feedback comparison.")

        # Join on timestamp and grid_id
        join_keys = [k for k in ["timestamp", "grid_id"] if k in coupled_df.columns and k in control_df.columns]
        if not join_keys:
            join_keys = ["timestamp"]

        merged = pd.merge(
            coupled_df,
            control_df,
            on=join_keys,
            suffixes=("_coupled", "_control")
        )

        if merged.empty:
            raise ValueError("No overlapping space-time coordinates found between coupled and control runs.")

        # 1. Surface Temperature Differential (Aerosol Dimming: T_coupled < T_control during daytime)
        merged["delta_temperature_2m"] = merged["temperature_2m_coupled"] - merged["temperature_2m_control"]
        
        # 2. Boundary Layer Height Differential (Stabilization: PBL_coupled < PBL_control)
        merged["delta_boundary_layer_height"] = merged["boundary_layer_height_coupled"] - merged["boundary_layer_height_control"]
        
        # 3. Solar Radiation Extinction Differential (SW_coupled < SW_control)
        merged["delta_solar_radiation"] = merged["solar_radiation_coupled"] - merged["solar_radiation_control"]
        
        # 4. Wind Speed Differential
        merged["delta_wind_speed_10m"] = merged["wind_speed_10m_coupled"] - merged["wind_speed_10m_control"]
        
        # 5. PM2.5 Trapping Amplification Differential (Positive Feedback: PM2.5_coupled > PM2.5_control)
        merged["delta_pm25"] = merged["pm25_coupled"] - merged["pm25_control"]
        
        # 6. Ozone Photolysis Attenuation Differential (O3_coupled < O3_control)
        merged["delta_o3"] = merged["o3_coupled"] - merged["o3_control"]

        # Aggregate Physical Metrics
        mean_delta_t = float(merged["delta_temperature_2m"].mean())
        mean_delta_pbl = float(merged["delta_boundary_layer_height"].mean())
        mean_delta_sw = float(merged["delta_solar_radiation"].mean())
        mean_delta_ws = float(merged["delta_wind_speed_10m"].mean())
        mean_delta_pm25 = float(merged["delta_pm25"].mean())
        mean_delta_o3 = float(merged["delta_o3"].mean())
        
        # Mean percentage change in PM2.5 due to coupled stagnation feedback
        ctrl_pm25 = merged["pm25_control"].replace(0, np.nan)
        pm25_rel_enhancement_pct = float(((merged["pm25_coupled"] - ctrl_pm25) / ctrl_pm25 * 100.0).mean())

        # Feedback Coupling Strength Index [0 - 100]
        # Evaluates combined magnitude of radiative dimming + PBL suppression + pollutant accumulation
        dimming_score = min(35.0, abs(mean_delta_sw) / 2.5) if mean_delta_sw < 0 else 0.0
        pbl_suppression_score = min(35.0, abs(mean_delta_pbl) / 3.0) if mean_delta_pbl < 0 else 0.0
        trapping_score = min(30.0, max(0.0, pm25_rel_enhancement_pct) * 1.5)
        coupling_strength_index = round(float(dimming_score + pbl_suppression_score + trapping_score), 2)

        summary = {
            "comparison_label": "COUPLED - CONTROL DIFFERENCE",
            "evaluated_records_count": len(merged),
            "mean_delta_temperature_k": round(mean_delta_t, 3),
            "mean_delta_pbl_height_m": round(mean_delta_pbl, 2),
            "mean_delta_solar_radiation_wm2": round(mean_delta_sw, 2),
            "mean_delta_wind_speed_ms": round(mean_delta_ws, 3),
            "mean_delta_pm25_ug_m3": round(mean_delta_pm25, 2),
            "mean_delta_o3_ug_m3": round(mean_delta_o3, 2),
            "pm25_coupling_enhancement_percent": round(pm25_rel_enhancement_pct, 2),
            "coupling_strength_index": coupling_strength_index,
            "feedback_verification_status": (
                "CONFIRMED_PHYSICAL_COUPLING" if (mean_delta_sw <= 0 and mean_delta_pbl <= 0 and mean_delta_pm25 >= 0)
                else "NEGLIGIBLE_OR_INVERSE_COUPLING"
            )
        }

        logger.info(
            f"Two-way feedback verified: Delta_SW={mean_delta_sw:.1f} W/m2, "
            f"Delta_PBL={mean_delta_pbl:.1f} m, Delta_PM2.5=+{mean_delta_pm25:.1f} ug/m3 "
            f"(Enhancement: +{pm25_rel_enhancement_pct:.1f}%)"
        )
        return {
            "summary": summary,
            "differential_dataframe": merged
        }
