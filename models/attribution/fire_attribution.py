"""
Regional Fire Attribution and Plume Arrival Clock Engine
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import math
import numpy as np
import pandas as pd

from config.logging_config import get_logger
from config.settings import settings
from processing.spatial_grid import haversine_distance_km, calculate_bearing_degrees
from processing.plume import FirePlumeTransportEngine, calculate_wind_speed_direction, circular_angular_difference
from models.dmdc.dmdc_model import DMDcModel
from models.dmdc.preprocessing import DMDcPreprocessor
from models.dmdc.rollout import DMDcRolloutEngine, ForecastInputMode
from models.attribution.attribution_schema import (
    FireCluster,
    PlumeArrivalEstimate,
    ProvenanceType
)

logger = get_logger("models.attribution.fire_attribution")


class FireAttributionEngine:
    """
    Dedicated regional agricultural fire attribution and plume clock engine.
    Combines satellite active fire detections (FIRMS/GFAS) with wind transport dynamics
    to identify upwind fire clusters, calculate estimated plume arrival times,
    and compute fire counterfactual impacts via DMDc rollout.
    """

    def __init__(
        self,
        model: DMDcModel,
        preprocessor: DMDcPreprocessor,
        target_lat: float = settings.DELHI_CENTER_LAT,
        target_lon: float = settings.DELHI_CENTER_LON
    ):
        self.model = model
        self.preprocessor = preprocessor
        self.rollout_engine = DMDcRolloutEngine(model, preprocessor)
        self.target_lat = target_lat
        self.target_lon = target_lon

        self.state_vars = self.preprocessor.state_vars
        self.control_vars = self.preprocessor.control_vars

    def cluster_fires(
        self,
        fires_df: pd.DataFrame,
        cluster_radius_km: float = 30.0
    ) -> List[FireCluster]:
        """
        Groups individual satellite hotspot detections into regional fire clusters.
        """
        if fires_df.empty:
            return []

        clusters: List[FireCluster] = []
        unassigned = fires_df.copy().reset_index(drop=True)

        cluster_idx = 1
        while not unassigned.empty:
            # Seed cluster with highest FRP hotspot
            seed_idx = unassigned["frp"].idxmax() if "frp" in unassigned.columns else 0
            seed = unassigned.iloc[seed_idx]
            seed_lat = float(seed["latitude"])
            seed_lon = float(seed["longitude"])

            # Find all fires within cluster radius
            distances = unassigned.apply(
                lambda r: haversine_distance_km(seed_lat, seed_lon, float(r["latitude"]), float(r["longitude"])),
                axis=1
            )
            in_cluster = unassigned[distances <= cluster_radius_km]

            total_frp = float(in_cluster["frp"].sum()) if "frp" in in_cluster.columns else float(in_cluster.shape[0] * 10.0)
            if "confidence" in in_cluster.columns:
                conf_series = in_cluster["confidence"].astype(str).str.lower().map({
                    "l": 30.0, "n": 65.0, "h": 90.0, "low": 30.0, "nominal": 65.0, "high": 90.0
                })
                num_conf = pd.to_numeric(in_cluster["confidence"], errors="coerce").fillna(conf_series).fillna(75.0)
                avg_conf = float(num_conf.mean())
            else:
                avg_conf = 80.0
            ts_str = str(seed.get("timestamp", datetime.utcnow().isoformat()))

            # Assign region name based on coordinates
            region_name = "Punjab/Haryana"
            if seed_lat > 31.0:
                region_name = "Punjab (North)"
            elif seed_lat > 29.5:
                region_name = "Punjab/Haryana (Central)"
            else:
                region_name = "Western UP / NCR Border"

            cluster = FireCluster(
                cluster_id=f"FC_{cluster_idx:03d}_{region_name.split()[0]}",
                latitude=round(float(in_cluster["latitude"].mean()), 3),
                longitude=round(float(in_cluster["longitude"].mean()), 3),
                total_frp=round(total_frp, 1),
                fire_count=len(in_cluster),
                mean_confidence=round(avg_conf, 1),
                timestamp=ts_str,
                provenance=ProvenanceType.OBSERVED
            )
            clusters.append(cluster)
            cluster_idx += 1

            # Remove grouped fires
            unassigned = unassigned[distances > cluster_radius_km].reset_index(drop=True)

        return clusters

    def estimate_plume_arrivals(
        self,
        clusters: List[FireCluster],
        u_wind: float,
        v_wind: float,
        ref_timestamp: Optional[datetime] = None
    ) -> List[PlumeArrivalEstimate]:
        """
        Computes the Plume Clock: estimates transport time and arrival timestamp
        for each active fire cluster into the Delhi NCR urban airshed.
        """
        estimates: List[PlumeArrivalEstimate] = []
        ref_dt = ref_timestamp or datetime.utcnow()

        ws, wd_from = calculate_wind_speed_direction(u_wind, v_wind)
        wind_towards = (wd_from + 180.0) % 360.0

        for fc in clusters:
            dist_km = haversine_distance_km(fc.latitude, fc.longitude, self.target_lat, self.target_lon)
            bearing_to_delhi = calculate_bearing_degrees(fc.latitude, fc.longitude, self.target_lat, self.target_lon)

            # Angular difference between wind transport direction and vector towards Delhi
            angle_diff = circular_angular_difference(wind_towards, bearing_to_delhi)
            is_upwind = bool(angle_diff < 90.0)

            # Transport velocity: wind speed projected along transport vector
            effective_speed_ms = max(0.5, ws * math.cos(math.radians(angle_diff))) if is_upwind else max(0.5, ws * 0.2)
            speed_kmh = effective_speed_ms * 3.6
            transport_hours = round(dist_km / speed_kmh, 1)

            # Parse fire timestamp
            try:
                fire_dt = datetime.fromisoformat(fc.timestamp.replace("Z", "+00:00")).replace(tzinfo=None)
            except Exception:
                fire_dt = ref_dt

            arrival_dt = fire_dt + timedelta(hours=transport_hours)
            arrival_iso = arrival_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

            # Transport confidence: depends on alignment, FRP, and proximity
            alignment = math.cos(math.radians(angle_diff)) if is_upwind else 0.0
            dist_decay = math.exp(-dist_km / 250.0)
            confidence = min(0.95, max(0.10, alignment * dist_decay * min(1.0, fc.total_frp / 200.0)))

            estimate = PlumeArrivalEstimate(
                fire_cluster_id=fc.cluster_id,
                source_region=fc.cluster_id.split("_")[-1],
                latitude=fc.latitude,
                longitude=fc.longitude,
                fire_count=fc.fire_count,
                fire_timestamp=fc.timestamp,
                total_frp=fc.total_frp,
                wind_speed_ms=ws,
                wind_direction_from_deg=wd_from,
                estimated_distance_km=round(dist_km, 1),
                estimated_transport_time_hours=transport_hours,
                estimated_arrival_time=arrival_iso,
                transport_confidence=round(confidence, 2),
                is_upwind=is_upwind,
                status="Estimated plume arrival" if is_upwind else "Downwind / Plume bypasses Delhi",
                provenance=ProvenanceType.INFERRED
            )
            estimates.append(estimate)

        return sorted(estimates, key=lambda e: e.estimated_transport_time_hours)

    def evaluate_fire_counterfactual(
        self,
        x0_physical: np.ndarray,
        u_sequence_physical: np.ndarray,
        horizon: int = 24
    ) -> Dict[str, Any]:
        """
        Executes fire counterfactual simulation:
            Baseline (with fire controls) vs. Counterfactual (fire_frp=0, plume_score=0)
        Returns delta PM2.5, PM10, O3 across horizons.
        """
        # Baseline rollout
        base_rollout = self.rollout_engine.forecast(
            x0_physical=x0_physical,
            u0_physical=u_sequence_physical[0],
            horizon=horizon,
            mode=ForecastInputMode.RETROSPECTIVE,
            actual_future_U=u_sequence_physical,
            apply_physical_bounds=True
        )
        base_traj = base_rollout["trajectory_matrix"]

        # Perturbed rollout: fire emissions removed
        u_no_fire = u_sequence_physical[:horizon].copy()
        if "fire_frp" in self.control_vars:
            u_no_fire[:, self.control_vars.index("fire_frp")] = 0.0
        if "plume_transport_score" in self.control_vars:
            u_no_fire[:, self.control_vars.index("plume_transport_score")] = 0.0

        no_fire_rollout = self.rollout_engine.forecast(
            x0_physical=x0_physical,
            u0_physical=u_no_fire[0],
            horizon=horizon,
            mode=ForecastInputMode.RETROSPECTIVE,
            actual_future_U=u_no_fire,
            apply_physical_bounds=True
        )
        no_fire_traj = no_fire_rollout["trajectory_matrix"]

        pm25_idx = self.state_vars.index("pm25") if "pm25" in self.state_vars else 0
        pm10_idx = self.state_vars.index("pm10") if "pm10" in self.state_vars else 1
        o3_idx = self.state_vars.index("o3") if "o3" in self.state_vars else 2

        checkpoints = [1, 6, 12, 24, 48, 72]
        valid_checkpoints = [h for h in checkpoints if h <= horizon]

        impact_by_horizon = {}
        for h in valid_checkpoints:
            h_idx = h - 1
            delta_pm25 = max(0.0, float(base_traj[h_idx, pm25_idx] - no_fire_traj[h_idx, pm25_idx]))
            delta_pm10 = max(0.0, float(base_traj[h_idx, pm10_idx] - no_fire_traj[h_idx, pm10_idx]))
            delta_o3 = float(base_traj[h_idx, o3_idx] - no_fire_traj[h_idx, o3_idx])

            impact_by_horizon[f"{h}h"] = {
                "delta_pm25": round(delta_pm25, 3),
                "delta_pm10": round(delta_pm10, 3),
                "delta_o3": round(delta_o3, 3),
                "baseline_pm25": round(float(base_traj[h_idx, pm25_idx]), 3),
                "without_fire_pm25": round(float(no_fire_traj[h_idx, pm25_idx]), 3)
            }

        return {
            "evaluation_horizon": horizon,
            "checkpoints": impact_by_horizon,
            "provenance": ProvenanceType.COUNTERFACTUAL.value
        }
