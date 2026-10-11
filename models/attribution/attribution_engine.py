"""
Unified Source Attribution and Counterfactual Intelligence Facade Engine
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import numpy as np
import pandas as pd

from config.logging_config import get_logger
from config.settings import settings
from models.dmdc.dmdc_model import DMDcModel
from models.dmdc.preprocessing import DMDcPreprocessor
from models.attribution.attribution_schema import (
    AttributionResult,
    SectorContribution,
    RegionalAttribution,
    PlumeArrivalEstimate,
    ProvenanceType
)
from models.attribution.sector_attribution import SectorAttributionEngine
from models.attribution.fire_attribution import FireAttributionEngine
from models.attribution.regional_attribution import RegionalAttributionEngine
from models.attribution.counterfactual import CounterfactualEngine

logger = get_logger("models.attribution.attribution_engine")


class SourceAttributionEngine:
    """
    Unified entry point for SAMEER Source Attribution, Plume Tracking,
    Regional Disaggregation, and Counterfactual Intelligence.
    """

    def __init__(self, model: DMDcModel, preprocessor: DMDcPreprocessor):
        self.model = model
        self.preprocessor = preprocessor

        self.sector_engine = SectorAttributionEngine(model, preprocessor)
        self.fire_engine = FireAttributionEngine(model, preprocessor)
        self.regional_engine = RegionalAttributionEngine(model, preprocessor)
        self.counterfactual_engine = CounterfactualEngine(model, preprocessor)
        self.rollout_engine = self.sector_engine.rollout_engine

    def analyze(
        self,
        x0_physical: np.ndarray,
        u_sequence_physical: np.ndarray,
        fires_df: Optional[pd.DataFrame] = None,
        u_wind: float = -2.0,
        v_wind: float = -1.5,
        horizon: int = 24,
        target_cell: str = "D03_R30_C30",
        target_region: str = "Delhi NCR Central",
        timestamp: Optional[str] = None
    ) -> AttributionResult:
        """
        Executes end-to-end multi-sector, regional, and fire plume attribution analysis.
        """
        ts = timestamp or datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

        # 1. Sectoral Counterfactual Attribution
        sector_results = self.sector_engine.evaluate_sector_contributions(
            x0_physical=x0_physical,
            u_sequence_physical=u_sequence_physical,
            horizon=horizon
        )

        # Convert dict to typed objects
        sector_contrib_objs = {}
        for s_name, item in sector_results["sector_contributions"].items():
            sector_contrib_objs[s_name] = SectorContribution(**item)

        # 2. Regional Disaggregation (Local vs Regional vs Background)
        regional_breakdown = self.regional_engine.disaggregate_spatial_scales(
            x0_physical=x0_physical,
            u_sequence_physical=u_sequence_physical,
            horizon=horizon
        )

        # 3. Plume Arrival Clock (if fire observations available)
        plume_estimates: List[PlumeArrivalEstimate] = []
        if fires_df is not None and not fires_df.empty:
            clusters = self.fire_engine.cluster_fires(fires_df)
            plume_estimates = self.fire_engine.estimate_plume_arrivals(
                clusters=clusters,
                u_wind=u_wind,
                v_wind=v_wind
            )

        # 4. Assemble AttributionResult
        result = AttributionResult(
            timestamp=ts,
            target_cell=target_cell,
            target_region=target_region,
            horizon_hours=horizon,
            baseline_pm25=sector_results["baseline_pm25"],
            counterfactual_pm25=round(sector_results["baseline_pm25"] - sector_results["total_sector_delta_pm25"], 3),
            sector_contributions=sector_contrib_objs,
            regional_breakdown=regional_breakdown,
            plume_estimates=plume_estimates,
            interaction_residual_pm25=sector_results["interaction_residual_pm25"],
            dominant_sector=sector_results["dominant_sector"],
            dominant_sector_percentage=sector_results["dominant_sector_percentage"],
            confidence_level=0.95,
            provenance=ProvenanceType.COUNTERFACTUAL
        )

        logger.info(
            f"Source attribution complete: Dominant={result.dominant_sector} "
            f"({result.dominant_sector_percentage}%), Local={regional_breakdown.local_percentage}%, "
            f"Regional={regional_breakdown.regional_percentage}%, Background={regional_breakdown.background_percentage}%"
        )
        return result
