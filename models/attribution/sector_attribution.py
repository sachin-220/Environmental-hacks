"""
Sectoral Emission Attribution Engine using Modelled Counterfactual Perturbations
"""
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd

from config.logging_config import get_logger
from config.settings import settings
from models.dmdc.dmdc_model import DMDcModel
from models.dmdc.preprocessing import DMDcPreprocessor
from models.dmdc.rollout import DMDcRolloutEngine, ForecastInputMode
from models.attribution.attribution_schema import (
    AttributionSector,
    SectorContribution,
    SourcePerturbation,
    ProvenanceType
)

logger = get_logger("models.attribution.sector_attribution")


class SectorAttributionEngine:
    """
    Computes source sector contributions to ambient air pollution using
    modelled counterfactual perturbations through the verified DMDc emulator:
        Delta_PM25_s(h) = PM25_baseline(h) - PM25_without_s(h)
    
    Distinguishes:
    - road_transport
    - industry
    - power_plants
    - residential
    - agriculture (biomass burning)
    - waste_burning
    - construction_proxy
    """

    # Default sectoral emission inventory split fractions (based on CAMS-GLOB-ANT / EDGAR for NCR)
    DEFAULT_INVENTORY_SHARES: Dict[str, Dict[str, float]] = {
        "anthro_nox": {
            AttributionSector.ROAD_TRANSPORT.value: 0.42,
            AttributionSector.POWER_PLANTS.value: 0.30,
            AttributionSector.INDUSTRY.value: 0.20,
            AttributionSector.RESIDENTIAL.value: 0.05,
            AttributionSector.WASTE_BURNING.value: 0.03
        },
        "anthro_so2": {
            AttributionSector.POWER_PLANTS.value: 0.65,
            AttributionSector.INDUSTRY.value: 0.28,
            AttributionSector.ROAD_TRANSPORT.value: 0.04,
            AttributionSector.RESIDENTIAL.value: 0.03
        },
        "anthro_co": {
            AttributionSector.ROAD_TRANSPORT.value: 0.48,
            AttributionSector.RESIDENTIAL.value: 0.32,
            AttributionSector.INDUSTRY.value: 0.12,
            AttributionSector.WASTE_BURNING.value: 0.08
        },
        "anthro_voc": {
            AttributionSector.ROAD_TRANSPORT.value: 0.45,
            AttributionSector.RESIDENTIAL.value: 0.30,
            AttributionSector.INDUSTRY.value: 0.18,
            AttributionSector.WASTE_BURNING.value: 0.07
        }
    }

    def __init__(
        self,
        model: DMDcModel,
        preprocessor: DMDcPreprocessor,
        inventory_csv_path: Optional[Path] = None
    ):
        self.model = model
        self.preprocessor = preprocessor
        self.rollout_engine = DMDcRolloutEngine(model, preprocessor)
        self.state_vars = self.preprocessor.state_vars
        self.control_vars = self.preprocessor.control_vars

        self.inventory_shares = self._load_inventory_shares(inventory_csv_path)

    def _load_inventory_shares(self, csv_path: Optional[Path]) -> Dict[str, Dict[str, float]]:
        """Loads and normalizes sectoral shares from emission inventory CSV"""
        path = csv_path or (settings.DATASETS_SAMPLE_DIR / "09_emission_inventory.csv")
        if not path.exists():
            alt_path = Path("data/raw/emissions/emissions_demo_2026.csv")
            if alt_path.exists():
                path = alt_path

        if path.exists():
            try:
                df = pd.read_csv(path)
                shares = {}
                for spec in ["anthro_nox", "anthro_so2", "anthro_co", "anthro_voc"]:
                    if spec in df.columns and "sector" in df.columns:
                        tot = df[spec].sum()
                        if tot > 0:
                            shares[spec] = {
                                row["sector"]: float(row[spec]) / tot
                                for _, row in df.iterrows()
                            }
                if shares:
                    logger.info(f"Loaded emission inventory sectoral shares from {path}")
                    return shares
            except Exception as e:
                logger.warning(f"Could not parse emission inventory from {path}: {e}. Using defaults.")

        return self.DEFAULT_INVENTORY_SHARES

    def get_sectoral_reduction_vector(
        self,
        sector: str,
        reduction_fraction: float = 1.0,
        baseline_u: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """
        Calculates the delta control vector delta_u in R^m corresponding to reducing
        emission sector 'sector' by reduction_fraction in [0.0, 1.0].
        """
        m = len(self.control_vars)
        delta_u = np.zeros(m, dtype=np.float64)

        frac = float(np.clip(reduction_fraction, 0.0, 1.0))

        # Check for agricultural burning sector
        if sector in [AttributionSector.AGRICULTURE.value, "agricultural_burning", "fire"]:
            if "fire_frp" in self.control_vars:
                f_idx = self.control_vars.index("fire_frp")
                base_val = baseline_u[f_idx] if baseline_u is not None else 1.0
                delta_u[f_idx] = base_val * frac
            if "plume_transport_score" in self.control_vars:
                p_idx = self.control_vars.index("plume_transport_score")
                base_val = baseline_u[p_idx] if baseline_u is not None else 1.0
                delta_u[p_idx] = base_val * frac
            return delta_u

        # Anthropogenic combustion sectors
        for spec_name, sector_map in self.inventory_shares.items():
            if spec_name in self.control_vars:
                spec_idx = self.control_vars.index(spec_name)
                share = sector_map.get(sector, 0.0)
                base_val = baseline_u[spec_idx] if baseline_u is not None else 1.0
                delta_u[spec_idx] += base_val * share * frac

        return delta_u

    def evaluate_sector_contributions(
        self,
        x0_physical: np.ndarray,
        u_sequence_physical: np.ndarray,
        horizon: int = 24,
        candidate_sectors: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Executes counterfactual zero-out simulations for all candidate emission sectors.
        Calculates:
            Delta_PM25_s(h) = PM25_baseline(h) - PM25_without_s(h)
        for each sector and quantifies non-linear interaction residuals.
        """
        sectors = candidate_sectors or [
            AttributionSector.ROAD_TRANSPORT.value,
            AttributionSector.INDUSTRY.value,
            AttributionSector.POWER_PLANTS.value,
            AttributionSector.RESIDENTIAL.value,
            AttributionSector.AGRICULTURE.value,
            AttributionSector.WASTE_BURNING.value
        ]

        # 1. Baseline simulation
        base_rollout = self.rollout_engine.forecast(
            x0_physical=x0_physical,
            u0_physical=u_sequence_physical[0],
            horizon=horizon,
            mode=ForecastInputMode.RETROSPECTIVE,
            actual_future_U=u_sequence_physical,
            apply_physical_bounds=True
        )
        base_traj = base_rollout["trajectory_matrix"]  # (H, n)

        pm25_idx = self.state_vars.index("pm25") if "pm25" in self.state_vars else 0
        pm10_idx = self.state_vars.index("pm10") if "pm10" in self.state_vars else 1
        o3_idx = self.state_vars.index("o3") if "o3" in self.state_vars else 2
        no2_idx = self.state_vars.index("no2") if "no2" in self.state_vars else 3

        base_pm25_final = float(base_traj[-1, pm25_idx])
        base_pm10_final = float(base_traj[-1, pm10_idx])
        base_o3_final = float(base_traj[-1, o3_idx])
        base_no2_final = float(base_traj[-1, no2_idx])

        # 2. Perturbation simulations per sector
        contributions: Dict[str, SectorContribution] = {}
        total_delta_pm25 = 0.0

        for sec in sectors:
            # Construct perturbed control trajectory: U_without_sec
            u_pert = u_sequence_physical[:horizon].copy()
            for h in range(horizon):
                d_u = self.get_sectoral_reduction_vector(sec, reduction_fraction=1.0, baseline_u=u_pert[h])
                u_pert[h] = np.maximum(0.0, u_pert[h] - d_u)

            pert_rollout = self.rollout_engine.forecast(
                x0_physical=x0_physical,
                u0_physical=u_pert[0],
                horizon=horizon,
                mode=ForecastInputMode.RETROSPECTIVE,
                actual_future_U=u_pert,
                apply_physical_bounds=True
            )
            pert_traj = pert_rollout["trajectory_matrix"]

            delta_pm25 = max(0.0, base_pm25_final - float(pert_traj[-1, pm25_idx]))
            delta_pm10 = max(0.0, base_pm10_final - float(pert_traj[-1, pm10_idx]))
            delta_o3 = base_o3_final - float(pert_traj[-1, o3_idx])  # O3 may increase or decrease
            delta_no2 = max(0.0, base_no2_final - float(pert_traj[-1, no2_idx]))

            contributions[sec] = SectorContribution(
                sector=sec,
                delta_pm25=round(delta_pm25, 3),
                delta_pm10=round(delta_pm10, 3),
                delta_o3=round(delta_o3, 3),
                delta_no2=round(delta_no2, 3),
                percentage_pm25=0.0,  # normalized below
                method="MODELLED COUNTERFACTUAL ZERO-OUT",
                provenance=ProvenanceType.COUNTERFACTUAL
            )
            total_delta_pm25 += delta_pm25

        # 3. Simulate Zero-Out of All Controllable Sectors simultaneously
        u_zero_all = u_sequence_physical[:horizon].copy()
        for sec in sectors:
            for h in range(horizon):
                d_u = self.get_sectoral_reduction_vector(sec, reduction_fraction=1.0, baseline_u=u_zero_all[h])
                u_zero_all[h] = np.maximum(0.0, u_zero_all[h] - d_u)

        zero_all_rollout = self.rollout_engine.forecast(
            x0_physical=x0_physical,
            u0_physical=u_zero_all[0],
            horizon=horizon,
            mode=ForecastInputMode.RETROSPECTIVE,
            actual_future_U=u_zero_all,
            apply_physical_bounds=True
        )
        zero_all_traj = zero_all_rollout["trajectory_matrix"]
        pm25_all_removed = float(zero_all_traj[-1, pm25_idx])
        actual_all_removed_delta = max(0.0, base_pm25_final - pm25_all_removed)

        # 4. Interaction Residual (non-linear atmospheric chemistry coupling)
        interaction_residual = round(actual_all_removed_delta - total_delta_pm25, 3)

        # 5. Compute attribution percentages
        denom = total_delta_pm25 if total_delta_pm25 > 1e-6 else 1.0
        for sec, item in contributions.items():
            pct = (item.delta_pm25 / denom) * 100.0
            item.percentage_pm25 = round(pct, 2)

        # Dominant sector
        dominant_sec = max(contributions.keys(), key=lambda k: contributions[k].delta_pm25)
        dominant_pct = contributions[dominant_sec].percentage_pm25

        return {
            "horizon_hours": horizon,
            "baseline_pm25": round(base_pm25_final, 3),
            "total_sector_delta_pm25": round(total_delta_pm25, 3),
            "simultaneous_all_removed_delta_pm25": round(actual_all_removed_delta, 3),
            "interaction_residual_pm25": interaction_residual,
            "sector_contributions": {k: v.model_dump() for k, v in contributions.items()},
            "dominant_sector": dominant_sec,
            "dominant_sector_percentage": dominant_pct,
            "provenance": ProvenanceType.COUNTERFACTUAL.value
        }
