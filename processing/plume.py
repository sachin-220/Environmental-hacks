"""
Fire-to-Wind Transport Diagnostic and Biomass Inflow Calculator
"""
import math
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd
from processing.spatial_grid import haversine_distance_km, calculate_bearing_degrees
from config.settings import settings
from config.logging_config import get_logger

logger = get_logger("processing.plume")


def calculate_wind_speed_direction(u: float, v: float) -> Tuple[float, float]:
    """
    Convert U (eastward) and V (northward) wind components to speed (m/s)
    and meteorological wind direction (degrees FROM which the wind blows).
    """
    speed = math.sqrt(u**2 + v**2)
    # Meteorological direction (0=N, 90=E, 180=S, 270=W)
    direction = (270.0 - math.degrees(math.atan2(v, u))) % 360.0
    return round(speed, 2), round(direction, 1)


def circular_angular_difference(angle1_deg: float, angle2_deg: float) -> float:
    """Calculate the shortest angular difference in degrees [0, 180] between two angles"""
    diff = abs((angle1_deg - angle2_deg + 180.0) % 360.0 - 180.0)
    return diff


class FirePlumeTransportEngine:
    """
    Physical fire-to-wind transport diagnostic. Evaluates whether active biomass burning
    hotspots in Punjab/Haryana/W-UP are directly upwind of Delhi NCR and computes the
    plume transport score.
    """

    @classmethod
    def evaluate_fire_transport(
        cls,
        fire_lat: float,
        fire_lon: float,
        fire_frp: float,
        u_wind_10m: Optional[float] = None,
        v_wind_10m: Optional[float] = None,
        u_wind: Optional[float] = None,
        v_wind: Optional[float] = None,
        target_lat: float = settings.DELHI_CENTER_LAT,
        target_lon: float = settings.DELHI_CENTER_LON
    ) -> Dict[str, Any]:
        """
        Evaluate transport dynamics from a single fire hotspot to Delhi NCR.
        """
        u_eff = u_wind_10m if u_wind_10m is not None else (u_wind if u_wind is not None else 0.0)
        v_eff = v_wind_10m if v_wind_10m is not None else (v_wind if v_wind is not None else 0.0)
        
        dist_km = haversine_distance_km(fire_lat, fire_lon, target_lat, target_lon)
        bearing_fire_to_target = calculate_bearing_degrees(fire_lat, fire_lon, target_lat, target_lon)
        
        ws, wd_from = calculate_wind_speed_direction(u_eff, v_eff)
        
        # Wind blowing TOWARDS direction
        wind_towards = (wd_from + 180.0) % 360.0
        
        # Angular misalignment between where wind is blowing and where Delhi is
        angle_diff = circular_angular_difference(wind_towards, bearing_fire_to_target)
        
        # Upwind factor: 1.0 when perfectly aligned towards target, 0.0 when perpendicular or downwind (>90 deg)
        is_upwind = angle_diff < 90.0
        alignment_factor = math.cos(math.radians(angle_diff)) if is_upwind else 0.0
        
        # Physical exponential spatial decay with distance (e-folding scale ~250 km)
        d_decay_km = 250.0
        distance_decay = math.exp(-dist_km / d_decay_km)
        
        # Advective speed factor (normalized around 5 m/s)
        advection_speed_factor = max(0.2, min(2.5, ws / 5.0))
        
        # Individual fire transport contribution
        transport_potency = fire_frp * alignment_factor * distance_decay * advection_speed_factor

        return {
            "distance_to_target_km": round(dist_km, 2),
            "bearing_to_target_deg": round(bearing_fire_to_target, 1),
            "wind_speed_ms": ws,
            "wind_direction_from_deg": wd_from,
            "wind_towards_deg": round(wind_towards, 1),
            "wind_fire_angle_diff": round(angle_diff, 1),
            "is_upwind": bool(is_upwind),
            "alignment_factor": round(alignment_factor, 3),
            "transport_potency": round(transport_potency, 2)
        }

    @classmethod
    def compute_regional_plume_score(
        cls,
        fires_df: pd.DataFrame,
        u_wind: float,
        v_wind: float,
        target_lat: float = settings.DELHI_CENTER_LAT,
        target_lon: float = settings.DELHI_CENTER_LON
    ) -> Dict[str, Any]:
        """
        Aggregate active fire observations over the regional domain and compute
        the integrated Plume Transport Score [0.0 - 100.0] into Delhi NCR.
        """
        if fires_df.empty:
            return {
                "fire_count": 0,
                "fire_frp": 0.0,
                "fire_confidence": 0.0,
                "nearest_fire_distance": None,
                "upwind_fire_count": 0,
                "upwind_fire_frp": 0.0,
                "upwind_fire_distance": None,
                "wind_fire_angle": None,
                "plume_transport_score": 0.0
            }

        total_fires = len(fires_df)
        total_frp = float(fires_df["frp"].sum()) if "frp" in fires_df.columns else 0.0
        avg_conf = float(fires_df["confidence"].mean()) if "confidence" in fires_df.columns else 80.0

        upwind_count = 0
        upwind_frp = 0.0
        upwind_dists = []
        angle_diffs = []
        total_potency = 0.0
        min_dist = float("inf")

        for _, row in fires_df.iterrows():
            f_lat = float(row.get("latitude", 0.0))
            f_lon = float(row.get("longitude", 0.0))
            f_frp = float(row.get("frp", 10.0))
            
            diag = cls.evaluate_fire_transport(f_lat, f_lon, f_frp, u_wind, v_wind, target_lat, target_lon)
            d = diag["distance_to_target_km"]
            if d < min_dist:
                min_dist = d

            if diag["is_upwind"]:
                upwind_count += 1
                upwind_frp += f_frp
                upwind_dists.append(d)
                angle_diffs.append(diag["wind_fire_angle_diff"])
                total_potency += diag["transport_potency"]

        # Scale transport score to 0.0 - 100.0 scale (non-linear logistic saturation)
        # 100 MW of well-aligned upwind fires within 150 km generates ~30-50 score; severe episodes > 75
        scaled_score = min(100.0, 100.0 * (1.0 - math.exp(-total_potency / 350.0)))

        return {
            "fire_count": total_fires,
            "fire_frp": round(total_frp, 2),
            "fire_confidence": round(avg_conf, 1),
            "nearest_fire_distance": round(min_dist, 2) if min_dist != float("inf") else None,
            "upwind_fire_count": upwind_count,
            "upwind_fire_frp": round(upwind_frp, 2),
            "upwind_fire_distance": round(float(np.mean(upwind_dists)), 2) if upwind_dists else None,
            "wind_fire_angle": round(float(np.mean(angle_diffs)), 1) if angle_diffs else None,
            "plume_transport_score": round(scaled_score, 2)
        }
