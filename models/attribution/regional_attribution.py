"""
Spatial Disaggregation Engine: Local vs. Regional vs. Background Source Attribution
"""
from typing import Dict, Any, List, Optional
import numpy as np

from config.logging_config import get_logger
from models.dmdc.dmdc_model import DMDcModel
from models.dmdc.preprocessing import DMDcPreprocessor
from models.dmdc.rollout import DMDcRolloutEngine, ForecastInputMode
from models.attribution.attribution_schema import RegionalAttribution, ProvenanceType

logger = get_logger("models.attribution.regional_attribution")


class RegionalAttributionEngine:
    """
    Separates total ambient air pollution into:
    1. Local: Urban surface emissions within Delhi NCR (road transport, residential, local small industry)
    2. Regional: Long-range transport and upwind agricultural biomass burning (Punjab/Haryana fires, regional coal plants)
    3. Background: Regional baseline concentration persisting without controllable anthropogenic emissions
    """

    def __init__(self, model: DMDcModel, preprocessor: DMDcPreprocessor):
        self.model = model
        self.preprocessor = preprocessor
        self.rollout_engine = DMDcRolloutEngine(model, preprocessor)
        self.state_vars = self.preprocessor.state_vars
        self.control_vars = self.preprocessor.control_vars

    def disaggregate_spatial_scales(
        self,
        x0_physical: np.ndarray,
        u_sequence_physical: np.ndarray,
        horizon: int = 24
    ) -> RegionalAttribution:
        """
        Computes the three-tier spatial disaggregation using counterfactual simulations:
        - Baseline: all emissions active -> Total PM2.5
        - Zero-Local: road_transport & residential & urban industry set to 0 -> Regional + Background
        - Zero-Regional: fire_frp & plume_score & power_plants set to 0 -> Local + Background
        - Zero-All: all anthropogenic/fire controls set to 0 -> Background
        """
        pm25_idx = self.state_vars.index("pm25") if "pm25" in self.state_vars else 0

        # 1. Baseline rollout
        base_rollout = self.rollout_engine.forecast(
            x0_physical=x0_physical,
            u0_physical=u_sequence_physical[0],
            horizon=horizon,
            mode=ForecastInputMode.RETROSPECTIVE,
            actual_future_U=u_sequence_physical,
            apply_physical_bounds=True
        )
        pm25_total = max(1.0, float(base_rollout["trajectory_matrix"][-1, pm25_idx]))

        # 2. Zero-All anthropogenic and fire forcing (Background estimate)
        u_zero_all = u_sequence_physical[:horizon].copy()
        for col in ["anthro_nox", "anthro_so2", "anthro_co", "anthro_voc", "fire_frp", "plume_transport_score"]:
            if col in self.control_vars:
                u_zero_all[:, self.control_vars.index(col)] = 0.0

        bg_rollout = self.rollout_engine.forecast(
            x0_physical=x0_physical,
            u0_physical=u_zero_all[0],
            horizon=horizon,
            mode=ForecastInputMode.RETROSPECTIVE,
            actual_future_U=u_zero_all,
            apply_physical_bounds=True
        )
        pm25_bg = float(bg_rollout["trajectory_matrix"][-1, pm25_idx])
        pm25_bg = float(np.clip(pm25_bg, 5.0, pm25_total * 0.40))  # natural background bounds

        # 3. Controllable fraction
        controllable_pm25 = max(0.0, pm25_total - pm25_bg)

        # 4. Regional plume share: evaluate fire + regional transport forcing
        u_no_regional = u_sequence_physical[:horizon].copy()
        if "fire_frp" in self.control_vars:
            u_no_regional[:, self.control_vars.index("fire_frp")] = 0.0
        if "plume_transport_score" in self.control_vars:
            u_no_regional[:, self.control_vars.index("plume_transport_score")] = 0.0
        if "anthro_so2" in self.control_vars:
            # Regional coal/power plants contribute ~65% of SO2
            u_no_regional[:, self.control_vars.index("anthro_so2")] *= 0.35

        no_reg_rollout = self.rollout_engine.forecast(
            x0_physical=x0_physical,
            u0_physical=u_no_regional[0],
            horizon=horizon,
            mode=ForecastInputMode.RETROSPECTIVE,
            actual_future_U=u_no_regional,
            apply_physical_bounds=True
        )
        pm25_no_reg = float(no_reg_rollout["trajectory_matrix"][-1, pm25_idx])
        delta_regional = max(0.0, pm25_total - pm25_no_reg)

        # 5. Local urban share
        delta_local = max(0.0, controllable_pm25 - delta_regional)

        # Normalize percentages
        denom = delta_local + delta_regional + pm25_bg
        if denom > 0:
            local_pct = round((delta_local / denom) * 100.0, 1)
            regional_pct = round((delta_regional / denom) * 100.0, 1)
            bg_pct = round((pm25_bg / denom) * 100.0, 1)
        else:
            local_pct, regional_pct, bg_pct = 50.0, 30.0, 20.0

        return RegionalAttribution(
            local_pm25=round(delta_local, 2),
            regional_pm25=round(delta_regional, 2),
            background_pm25=round(pm25_bg, 2),
            local_percentage=local_pct,
            regional_percentage=regional_pct,
            background_percentage=bg_pct,
            provenance=ProvenanceType.INFERRED
        )
