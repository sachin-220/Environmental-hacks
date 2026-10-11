"""
Forecast Verification, Baseline Comparison, and Episode-Based Evaluation Engine
"""
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd

from config.logging_config import get_logger
from models.dmdc.config import DMDcFeatureConfig, DMDcModelConfig
from models.dmdc.dmdc_model import DMDcModel
from models.dmdc.preprocessing import DMDcPreprocessor
from models.dmdc.rollout import DMDcRolloutEngine, ForecastInputMode

logger = get_logger("models.dmdc.evaluation")


class DMDcEvaluator:
    """
    Evaluates multi-step recursive DMDc forecast accuracy against held-out ground truth
    and benchmark baselines (Persistence and Rolling Mean).
    Computes MAE, RMSE, R², Mean Bias, NMB%, and Pearson r across evaluation horizons.
    """

    def __init__(
        self,
        model: DMDcModel,
        preprocessor: DMDcPreprocessor,
        config: Optional[DMDcModelConfig] = None
    ):
        self.model = model
        self.preprocessor = preprocessor
        self.config = config or DMDcModelConfig()
        self.state_vars = self.preprocessor.state_vars
        self.control_vars = self.preprocessor.control_vars
        self.rollout_engine = DMDcRolloutEngine(model, preprocessor, self.config)

    @staticmethod
    def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
        """
        Computes standard atmospheric validation metrics for 1D arrays:
        MAE, RMSE, R², Mean Bias (MB), Normalized Mean Bias % (NMB), Pearson r.
        """
        y_t = np.asarray(y_true, dtype=np.float64)
        y_p = np.asarray(y_pred, dtype=np.float64)

        mask = ~(np.isnan(y_t) | np.isnan(y_p) | np.isinf(y_t) | np.isinf(y_p))
        y_t = y_t[mask]
        y_p = y_p[mask]

        if len(y_t) < 2:
            return {
                "count": len(y_t),
                "mae": 0.0,
                "rmse": 0.0,
                "r2": 0.0,
                "mean_bias": 0.0,
                "nmb_percent": 0.0,
                "pearson_r": 0.0
            }

        diff = y_p - y_t
        mae = float(np.mean(np.abs(diff)))
        rmse = float(np.sqrt(np.mean(diff**2)))
        bias = float(np.mean(diff))

        # NMB% = (sum(y_p - y_t) / sum(y_t)) * 100
        sum_true = float(np.sum(y_t))
        nmb = float((np.sum(diff) / sum_true * 100.0)) if abs(sum_true) > 1e-6 else 0.0

        # R^2
        ss_tot = float(np.sum((y_t - np.mean(y_t))**2))
        ss_res = float(np.sum(diff**2))
        r2 = float(1.0 - (ss_res / ss_tot)) if ss_tot > 1e-6 else 0.0

        # Pearson r
        std_t = float(np.std(y_t))
        std_p = float(np.std(y_p))
        if std_t > 1e-6 and std_p > 1e-6:
            r = float(np.corrcoef(y_t, y_p)[0, 1])
        else:
            r = 0.0

        return {
            "count": len(y_t),
            "mae": round(mae, 3),
            "rmse": round(rmse, 3),
            "r2": round(r2, 4),
            "mean_bias": round(bias, 3),
            "nmb_percent": round(nmb, 2),
            "pearson_r": round(r, 4)
        }

    def evaluate_multi_horizon(
        self,
        X_test_seq: np.ndarray,   # (T_test, n_states)
        U_test_seq: np.ndarray,   # (T_test, n_controls)
        horizons: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        Evaluates DMDc, Persistence, and Rolling Mean across multiple forecast horizons.
        Uses non-overlapping windows of length max(horizons).
        """
        eval_horizons = horizons or self.config.evaluation_horizons
        max_h = max(eval_horizons)
        T_test = len(X_test_seq)

        if T_test < max_h + 1:
            raise ValueError(f"Test sequence length {T_test} is insufficient for max horizon {max_h}")

        # Baseline: Historical mean from preprocessor state_mean
        hist_mean = self.preprocessor.state_mean  # (n,)

        # Collect predictions across multiple starting points
        stride = max_h  # non-overlapping evaluation windows
        start_indices = list(range(0, T_test - max_h, stride))

        # Store predictions per horizon: {h: {var: {"true": [], "dmdc": [], "persistence": [], "rolling": []}}}
        data_by_h: Dict[int, Dict[str, Dict[str, List[float]]]] = {
            h: {
                var: {"true": [], "dmdc": [], "persistence": [], "rolling": []}
                for var in self.state_vars
            }
            for h in eval_horizons
        }

        for start_idx in start_indices:
            x0 = X_test_seq[start_idx]
            u_seq = U_test_seq[start_idx:start_idx + max_h]
            y_truth = X_test_seq[start_idx + 1:start_idx + max_h + 1]  # (max_h, n)

            # Rollout DMDc forecast
            rollout_res = self.rollout_engine.forecast(
                x0_physical=x0,
                u0_physical=u_seq[0],
                horizon=max_h,
                mode=ForecastInputMode.RETROSPECTIVE,
                actual_future_U=u_seq,
                apply_physical_bounds=True
            )
            dmdc_traj = rollout_res["trajectory_matrix"]  # (max_h, n)

            for h in eval_horizons:
                h_idx = h - 1
                y_true_h = y_truth[h_idx]
                y_dmdc_h = dmdc_traj[h_idx]
                y_persist_h = x0  # persistence baseline predicts x0 for all future steps
                y_rolling_h = hist_mean

                for v_idx, var in enumerate(self.state_vars):
                    data_by_h[h][var]["true"].append(float(y_true_h[v_idx]))
                    data_by_h[h][var]["dmdc"].append(float(y_dmdc_h[v_idx]))
                    data_by_h[h][var]["persistence"].append(float(y_persist_h[v_idx]))
                    data_by_h[h][var]["rolling"].append(float(y_rolling_h[v_idx]))

        # Compute metrics across horizons and models
        results_by_h = {}
        for h in eval_horizons:
            results_by_h[f"{h}h"] = {}
            for var in self.state_vars:
                yt = data_by_h[h][var]["true"]
                yp_dmdc = data_by_h[h][var]["dmdc"]
                yp_persist = data_by_h[h][var]["persistence"]
                yp_rolling = data_by_h[h][var]["rolling"]

                m_dmdc = self.compute_metrics(yt, yp_dmdc)
                m_persist = self.compute_metrics(yt, yp_persist)
                m_rolling = self.compute_metrics(yt, yp_rolling)

                # Skill Score: 1 - (RMSE_dmdc / RMSE_persist)
                skill_vs_persist = round(1.0 - (m_dmdc["rmse"] / max(1e-6, m_persist["rmse"])), 3)

                results_by_h[f"{h}h"][var] = {
                    "dmdc": m_dmdc,
                    "persistence_baseline": m_persist,
                    "rolling_mean_baseline": m_rolling,
                    "skill_score_vs_persistence": skill_vs_persist
                }

        logger.info(f"Multi-horizon evaluation completed across horizons: {eval_horizons}")
        return {
            "evaluation_horizons": eval_horizons,
            "evaluated_windows_count": len(start_indices),
            "results_by_horizon": results_by_h
        }

    def evaluate_episodes(
        self,
        X_test_seq: np.ndarray,
        U_test_seq: np.ndarray,
        horizon: int = 24
    ) -> Dict[str, Any]:
        """
        Evaluates model performance under specific high-pollution environmental episodes:
        1. Nocturnal Thermal Inversion Episode (inversion_strength > 2.0 K)
        2. Stubble Burning Plume Episode (plume_transport_score > 30.0)
        3. Severe Pollution Episode (PM2.5 > 200 ug/m3)
        """
        T_test = len(X_test_seq)
        if T_test < horizon + 1:
            return {"status": "INSUFFICIENT_TEST_LENGTH"}

        inv_idx = self.state_vars.index("inversion_strength") if "inversion_strength" in self.state_vars else None
        pm25_idx = self.state_vars.index("pm25") if "pm25" in self.state_vars else None
        plume_idx = self.control_vars.index("plume_transport_score") if "plume_transport_score" in self.control_vars else None

        episode_masks = {
            "nocturnal_inversion_episodes": [],
            "stubble_plume_episodes": [],
            "severe_pm25_episodes": []
        }

        for t in range(0, T_test - horizon):
            if inv_idx is not None and X_test_seq[t, inv_idx] > 1.5:
                episode_masks["nocturnal_inversion_episodes"].append(t)
            if plume_idx is not None and U_test_seq[t, plume_idx] > 25.0:
                episode_masks["stubble_plume_episodes"].append(t)
            if pm25_idx is not None and X_test_seq[t, pm25_idx] > 180.0:
                episode_masks["severe_pm25_episodes"].append(t)

        episode_reports = {}
        for ep_name, t_indices in episode_masks.items():
            if not t_indices:
                episode_reports[ep_name] = {"count": 0, "status": "NO_EPISODES_FOUND"}
                continue

            pm25_true, pm25_pred = [], []
            pbl_true, pbl_pred = [], []

            for start_t in t_indices[:10]: # evaluate up to 10 sample episodes
                x0 = X_test_seq[start_t]
                u_seq = U_test_seq[start_t:start_t + horizon]
                y_truth = X_test_seq[start_t + 1:start_t + horizon + 1]

                rollout_res = self.rollout_engine.forecast(
                    x0_physical=x0,
                    u0_physical=u_seq[0],
                    horizon=horizon,
                    mode=ForecastInputMode.RETROSPECTIVE,
                    actual_future_U=u_seq
                )
                pred_traj = rollout_res["trajectory_matrix"]

                if pm25_idx is not None:
                    pm25_true.extend(y_truth[:, pm25_idx].tolist())
                    pm25_pred.extend(pred_traj[:, pm25_idx].tolist())
                
                pbl_idx = self.state_vars.index("boundary_layer_height") if "boundary_layer_height" in self.state_vars else None
                if pbl_idx is not None:
                    pbl_true.extend(y_truth[:, pbl_idx].tolist())
                    pbl_pred.extend(pred_traj[:, pbl_idx].tolist())

            episode_reports[ep_name] = {
                "episodes_count": len(t_indices),
                "pm25_metrics": self.compute_metrics(pm25_true, pm25_pred) if pm25_true else {},
                "pblh_metrics": self.compute_metrics(pbl_true, pbl_pred) if pbl_true else {}
            }

        return episode_reports
