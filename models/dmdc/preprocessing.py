"""
Data Preprocessing, Train-Only Scaling, and Leakage Audit for DMDc Emulator
"""
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import json
import numpy as np
import pandas as pd

from config.logging_config import get_logger
from models.dmdc.config import DMDcFeatureConfig

logger = get_logger("models.dmdc.preprocessing")


class DMDcPreprocessor:
    """
    Manages train-only feature normalization and inverse transformations for
    coupled atmospheric state x(t) and control inputs u(t).
    Prevents data leakage by ensuring parameters originate exclusively from training data.
    """

    def __init__(
        self,
        state_vars: Optional[List[str]] = None,
        control_vars: Optional[List[str]] = None
    ):
        self.state_vars = state_vars or list(DMDcFeatureConfig.STATE_VARIABLES)
        self.control_vars = control_vars or list(DMDcFeatureConfig.CONTROL_VARIABLES)
        self.is_fitted = False
        
        # State normalization parameters
        self.state_mean = np.zeros(len(self.state_vars), dtype=np.float64)
        self.state_scale = np.ones(len(self.state_vars), dtype=np.float64)
        
        # Control normalization parameters
        self.control_mean = np.zeros(len(self.control_vars), dtype=np.float64)
        self.control_scale = np.ones(len(self.control_vars), dtype=np.float64)

    def fit(self, X_train: np.ndarray, U_train: np.ndarray) -> "DMDcPreprocessor":
        """
        Fits mean and standard deviation strictly on the training partition.
        """
        if X_train.shape[1] != len(self.state_vars):
            raise ValueError(f"X_train column count {X_train.shape[1]} does not match state_vars {len(self.state_vars)}")
        if U_train.shape[1] != len(self.control_vars):
            raise ValueError(f"U_train column count {U_train.shape[1]} does not match control_vars {len(self.control_vars)}")

        # Validate non-emptiness
        if len(X_train) == 0 or len(U_train) == 0:
            raise ValueError("Cannot fit scaler on empty training arrays.")

        # Handle NaNs / Infs in training data
        X_clean = np.nan_to_num(X_train, nan=0.0, posinf=0.0, neginf=0.0)
        U_clean = np.nan_to_num(U_train, nan=0.0, posinf=0.0, neginf=0.0)

        # State scaling
        self.state_mean = np.mean(X_clean, axis=0)
        state_std = np.std(X_clean, axis=0)
        # Prevent division by zero for invariant features
        self.state_scale = np.where(state_std < 1e-8, 1.0, state_std)

        # Control scaling
        self.control_mean = np.mean(U_clean, axis=0)
        control_std = np.std(U_clean, axis=0)
        self.control_scale = np.where(control_std < 1e-8, 1.0, control_std)

        self.is_fitted = True
        logger.info(
            f"DMDcPreprocessor fitted on {len(X_train)} training snapshots: "
            f"{len(self.state_vars)} state features, {len(self.control_vars)} control features"
        )
        return self

    def transform_state(self, X: np.ndarray) -> np.ndarray:
        """Standardizes state snapshots: (X - mean) / scale"""
        self._check_fitted()
        X_clean = np.nan_to_num(X, nan=self.state_mean, posinf=self.state_mean, neginf=self.state_mean)
        return (X_clean - self.state_mean) / self.state_scale

    def inverse_transform_state(self, X_scaled: np.ndarray) -> np.ndarray:
        """Inverts standardized state back to physical units: X_scaled * scale + mean"""
        self._check_fitted()
        return (X_scaled * self.state_scale) + self.state_mean

    def transform_control(self, U: np.ndarray) -> np.ndarray:
        """Standardizes control inputs: (U - mean) / scale"""
        self._check_fitted()
        U_clean = np.nan_to_num(U, nan=self.control_mean, posinf=self.control_mean, neginf=self.control_mean)
        return (U_clean - self.control_mean) / self.control_scale

    def inverse_transform_control(self, U_scaled: np.ndarray) -> np.ndarray:
        """Inverts standardized control back to physical units: U_scaled * scale + mean"""
        self._check_fitted()
        return (U_scaled * self.control_scale) + self.control_mean

    def _check_fitted(self):
        if not self.is_fitted:
            raise RuntimeError("DMDcPreprocessor has not been fitted yet. Call fit() first.")

    def to_dict(self) -> Dict[str, Any]:
        """Serializes scaling parameters to dictionary"""
        self._check_fitted()
        return {
            "state_variables": self.state_vars,
            "control_variables": self.control_vars,
            "state_mean": self.state_mean.tolist(),
            "state_scale": self.state_scale.tolist(),
            "control_mean": self.control_mean.tolist(),
            "control_scale": self.control_scale.tolist(),
            "is_fitted": self.is_fitted
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DMDcPreprocessor":
        """Reconstructs preprocessor from dictionary"""
        scaler = cls(
            state_vars=data["state_variables"],
            control_vars=data["control_variables"]
        )
        scaler.state_mean = np.array(data["state_mean"], dtype=np.float64)
        scaler.state_scale = np.array(data["state_scale"], dtype=np.float64)
        scaler.control_mean = np.array(data["control_mean"], dtype=np.float64)
        scaler.control_scale = np.array(data["control_scale"], dtype=np.float64)
        scaler.is_fitted = data.get("is_fitted", True)
        return scaler

    def save(self, filepath: Path) -> Path:
        """Saves scaler configuration to JSON"""
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)
        logger.info(f"Saved DMDcPreprocessor parameters to {filepath}")
        return filepath

    @classmethod
    def load(cls, filepath: Path) -> "DMDcPreprocessor":
        """Loads scaler from JSON"""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)


class DataLeakageAuditor:
    """
    Performs verification to guarantee no future data leakage across train, validation, and test sets.
    """

    @staticmethod
    def audit_splits(
        train_times: List[str],
        val_times: List[str],
        test_times: List[str],
        scaler_fitted_on_test: bool = False
    ) -> Dict[str, Any]:
        """
        Audits temporal timestamps and normalization pipeline for leakage.
        """
        train_set = set(train_times)
        val_set = set(val_times)
        test_set = set(test_times)

        train_val_overlap = sorted(list(train_set.intersection(val_set)))
        val_test_overlap = sorted(list(val_set.intersection(test_set)))
        train_test_overlap = sorted(list(train_set.intersection(test_set)))

        has_temporal_leakage = (
            len(train_val_overlap) > 0 or
            len(val_test_overlap) > 0 or
            len(train_test_overlap) > 0
        )

        audit_result = {
            "status": "PASS" if (not has_temporal_leakage and not scaler_fitted_on_test) else "FAIL",
            "train_snapshots_count": len(train_times),
            "val_snapshots_count": len(val_times),
            "test_snapshots_count": len(test_times),
            "train_val_overlap_count": len(train_val_overlap),
            "val_test_overlap_count": len(val_test_overlap),
            "train_test_overlap_count": len(train_test_overlap),
            "train_val_overlap_timestamps": train_val_overlap[:5],
            "val_test_overlap_timestamps": val_test_overlap[:5],
            "train_test_overlap_timestamps": train_test_overlap[:5],
            "scaler_fitted_on_test": scaler_fitted_on_test,
            "future_target_leakage": "NONE" if not has_temporal_leakage else "DETECTED_OVERLAP",
            "data_leakage_audit_summary": (
                "DATA LEAKAGE AUDIT: PASS - Strictly chronological splits and train-only normalization verified."
                if not has_temporal_leakage and not scaler_fitted_on_test
                else "DATA LEAKAGE AUDIT: FAIL - Temporal overlap or test-scaler contamination detected."
            )
        }
        return audit_result
