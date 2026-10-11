"""
Atmospheric Inversion Engine and Vertical Stability Diagnostics
"""
import math
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd
from config.logging_config import get_logger

logger = get_logger("processing.inversion")

# Standard atmospheric pressure to approximate geopotential height (m ASL)
# For Indo-Gangetic Plains / Delhi region (~215m ground elevation)
PRESSURE_TO_APPROX_HEIGHT_M: Dict[int, float] = {
    1000: 110.0,
    950: 540.0,
    925: 760.0,
    900: 1000.0,
    850: 1500.0,
    700: 3010.0,
    500: 5570.0
}


def pressure_to_altitude_hypsometric(p_hpa: float, t_k: float, p0_hpa: float = 1013.25) -> float:
    """Calculate geopotential height from pressure and temperature using Hypsometric equation"""
    if p_hpa <= 0 or t_k <= 0:
        return 0.0
    R_d = 287.058  # Specific gas constant for dry air J/(kg*K)
    g = 9.80665    # Gravitational acceleration m/s^2
    z = (R_d * t_k / g) * math.log(p0_hpa / p_hpa)
    return max(0.0, z)


class AtmosphericInversionEngine:
    """
    Physically computes thermal inversion layers, lapse rates, and boundary layer stability
    strictly from vertical temperature/wind soundings or reanalysis levels.
    """

    @classmethod
    def compute_inversion_profile(
        cls,
        levels_hpa: List[int],
        temperatures_k: List[float],
        wind_speeds: Optional[List[float]] = None,
        pbl_height_m: Optional[float] = None,
        is_modelled: bool = False
    ) -> Dict[str, Any]:
        """
        Analyze a vertical sounding profile for thermal inversions and atmospheric stability.
        
        Parameters:
            levels_hpa: Pressure levels in descending order (e.g. [1000, 950, 925, 850, 700, 500])
            temperatures_k: Temperature in Kelvin at each corresponding pressure level
            wind_speeds: Wind speed in m/s at each level (optional)
            pbl_height_m: Planetary boundary layer height in meters (optional)
            is_modelled: Flag indicating if sounding is from WRF/model or OBSERVED/REANALYSIS
        """
        if len(levels_hpa) < 2 or len(temperatures_k) < 2:
            return {
                "inversion_presence": 0,
                "inversion_strength": 0.0,
                "inversion_height": 0.0,
                "inversion_top": 0.0,
                "vertical_temperature_gradient": 0.0,
                "wind_shear": 0.0,
                "stability_index": "NEUTRAL",
                "diagnostic_type": "MODEL_DERIVED" if is_modelled else "REANALYSIS_DIAGNOSTIC"
            }

        # Convert pressures to altitude
        altitudes = [PRESSURE_TO_APPROX_HEIGHT_M.get(int(p), pressure_to_altitude_hypsometric(p, t)) 
                     for p, t in zip(levels_hpa, temperatures_k)]
        
        # Sort by ascending altitude
        profile = sorted(zip(altitudes, temperatures_k, levels_hpa), key=lambda x: x[0])
        sorted_z = [p[0] for p in profile]
        sorted_t = [p[1] for p in profile]

        # Environmental Lapse Rate in lower boundary layer (surface to ~1000m)
        # dT/dz in K/km (positive means temperature decreases with height; inversion is negative lapse rate)
        z_low, z_high = sorted_z[0], sorted_z[min(3, len(sorted_z)-1)]
        t_low, t_high = sorted_t[0], sorted_t[min(3, len(sorted_t)-1)]
        dz_km = (z_high - z_low) / 1000.0
        
        if dz_km > 0:
            lapse_rate_k_per_km = -(t_high - t_low) / dz_km
            grad_k_per_km = (t_high - t_low) / dz_km
        else:
            lapse_rate_k_per_km = 6.5
            grad_k_per_km = -6.5

        # Detect thermal inversion layer: dT > 0 with increasing altitude
        inversion_found = False
        max_inversion_strength = 0.0
        inv_base_z = 0.0
        inv_top_z = 0.0

        for i in range(len(sorted_z) - 1):
            z1, z2 = sorted_z[i], sorted_z[i+1]
            t1, t2 = sorted_t[i], sorted_t[i+1]
            
            # If temperature increases with altitude, an inversion layer exists
            if t2 > t1:
                inversion_found = True
                strength = t2 - t1
                if strength > max_inversion_strength:
                    max_inversion_strength = strength
                    inv_base_z = z1
                    inv_top_z = z2

        # Wind shear calculation (du/dz)
        shear = 0.0
        if wind_speeds and len(wind_speeds) >= 2:
            du = abs(wind_speeds[1] - wind_speeds[0])
            dz = max(10.0, sorted_z[1] - sorted_z[0])
            shear = du / dz

        # Stability classification (Pasquill-Gifford / Lapse rate criteria)
        # Dry adiabatic lapse rate is ~9.8 K/km
        if inversion_found or grad_k_per_km > 0:
            if max_inversion_strength > 3.0:
                stability = "VERY_STABLE"
            else:
                stability = "STABLE"
        elif lapse_rate_k_per_km > 10.0:
            stability = "UNSTABLE"
        elif 6.0 <= lapse_rate_k_per_km <= 10.0:
            stability = "NEUTRAL"
        else:
            stability = "STABLE"

        return {
            "inversion_presence": 1 if inversion_found else 0,
            "inversion_strength": round(float(max_inversion_strength), 2),
            "inversion_height": round(float(inv_base_z), 1),
            "inversion_top": round(float(inv_top_z), 1),
            "vertical_temperature_gradient": round(float(grad_k_per_km), 2),
            "wind_shear": round(float(shear), 4),
            "stability_index": stability,
            "boundary_layer_height": round(float(pbl_height_m), 1) if pbl_height_m is not None else None,
            "diagnostic_type": "MODEL_DERIVED" if is_modelled else "REANALYSIS_DIAGNOSTIC"
        }

    @classmethod
    def process_vertical_dataset(cls, df: pd.DataFrame) -> pd.DataFrame:
        """
        Process a multi-level vertical dataframe (e.g. ERA5 or sounding table)
        and compute hourly inversion & stability metrics per timestamp.
        """
        if df.empty or "timestamp" not in df.columns or "pressure_level_hpa" not in df.columns:
            return pd.DataFrame()

        results = []
        for ts, group in df.groupby("timestamp"):
            sorted_g = group.sort_values(by="pressure_level_hpa", ascending=False)
            levels = sorted_g["pressure_level_hpa"].tolist()
            temps = sorted_g["temperature_k"].tolist() if "temperature_k" in sorted_g.columns else (sorted_g["temperature_c"] + 273.15).tolist()
            winds = sorted_g["wind_speed_ms"].tolist() if "wind_speed_ms" in sorted_g.columns else None
            pbl = sorted_g["pbl_height_m"].iloc[0] if "pbl_height_m" in sorted_g.columns else None
            
            diag = cls.compute_inversion_profile(levels, temps, winds, pbl)
            diag["timestamp"] = ts
            results.append(diag)

        res_df = pd.DataFrame(results)
        logger.info(f"Computed atmospheric inversion metrics for {len(res_df)} timestamps")
        return res_df
