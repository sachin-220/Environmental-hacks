"""
Dynamic Mode Decomposition with Control (DMDc) Model Implementation
"""
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import json
import numpy as np
import scipy.linalg as la

from config.logging_config import get_logger
from models.dmdc.config import DMDcFeatureConfig, DMDcModelConfig

logger = get_logger("models.dmdc.dmdc_model")


class DMDcModel:
    """
    Dynamic Mode Decomposition with Control (DMDc) Linear Operator Estimator.
    Learns discrete state-transition operator A in R^(n x n) and input operator B in R^(n x m):
        x(t+1) = A x(t) + B u(t)
    using regularized truncated Singular Value Decomposition (SVD).
    """

    def __init__(
        self,
        rank: Optional[int] = None,
        reg_lambda: float = 0.0,
        state_vars: Optional[List[str]] = None,
        control_vars: Optional[List[str]] = None
    ):
        self.rank = rank
        self.reg_lambda = reg_lambda
        self.state_vars = state_vars or list(DMDcFeatureConfig.STATE_VARIABLES)
        self.control_vars = control_vars or list(DMDcFeatureConfig.CONTROL_VARIABLES)
        
        self.n_states = len(self.state_vars)
        self.n_controls = len(self.control_vars)
        
        # Learned operators
        self.A: Optional[np.ndarray] = None  # (n x n)
        self.B: Optional[np.ndarray] = None  # (n x m)
        self.G: Optional[np.ndarray] = None  # (n x (n+m))
        
        # SVD diagnostics
        self.singular_values: Optional[np.ndarray] = None
        self.explained_energy: float = 0.0
        self.is_fitted: bool = False
        self.fit_history: Dict[str, Any] = {}

    def fit(
        self,
        X: np.ndarray,
        X_prime: np.ndarray,
        U: np.ndarray,
        rank: Optional[int] = None,
        reg_lambda: Optional[float] = None
    ) -> "DMDcModel":
        """
        Fits A and B operators from snapshot matrices.
        Shapes:
            X: (N, n)
            X_prime: (N, n)
            U: (N, m)
        """
        N, n = X.shape
        _, m = U.shape
        
        if n != self.n_states:
            raise ValueError(f"State dimension mismatch: expected {self.n_states}, got {n}")
        if m != self.n_controls:
            raise ValueError(f"Control dimension mismatch: expected {self.n_controls}, got {m}")
        if X_prime.shape != (N, n):
            raise ValueError(f"X_prime shape {X_prime.shape} does not match (N={N}, n={n})")

        use_rank = rank if rank is not None else (self.rank or (n + m))
        use_lambda = reg_lambda if reg_lambda is not None else self.reg_lambda

        # Formulate column-major matrices: X_mat in R^(n x N), U_mat in R^(m x N)
        X_mat = X.T.astype(np.float64)        # (n, N)
        X_p_mat = X_prime.T.astype(np.float64)  # (n, N)
        U_mat = U.T.astype(np.float64)        # (m, N)

        # Construct augmented snapshot matrix Omega in R^((n+m) x N)
        Omega = np.vstack([X_mat, U_mat])     # (n+m, N)
        
        total_dim = n + m
        max_possible_rank = min(total_dim, N)
        actual_rank = min(use_rank, max_possible_rank)

        # Numerically stable Economy/Truncated SVD of Omega
        # Omega = U_omega * Sigma_omega * V_omega^T
        U_omega, s_omega, Vt_omega = la.svd(Omega, full_matrices=False)
        
        self.singular_values = s_omega.copy()
        total_energy = np.sum(s_omega**2)
        r_energy = np.sum(s_omega[:actual_rank]**2)
        self.explained_energy = float(r_energy / total_energy) if total_energy > 0 else 1.0

        # Truncate to rank r
        U_r = U_omega[:, :actual_rank]          # ((n+m), r)
        s_r = s_omega[:actual_rank]              # (r,)
        V_r = Vt_omega[:actual_rank, :].T        # (N, r)

        # Solve for G = [A B] with Tikhonov regularization:
        # G = X' * V_r * (Sigma_r / (Sigma_r^2 + lambda)) * U_r^T
        if use_lambda > 0.0:
            inv_filter = s_r / (s_r**2 + use_lambda)
        else:
            inv_filter = 1.0 / np.where(s_r < 1e-12, 1e-12, s_r)

        # Compute G in R^(n x (n+m))
        # (X_p_mat @ V_r) is (n, r)
        # np.diag(inv_filter) @ U_r.T is (r, n+m)
        G = (X_p_mat @ V_r) @ (np.diag(inv_filter) @ U_r.T)
        
        # Partition G into A and B
        self.A = G[:, :n]
        self.B = G[:, n:]
        self.G = G
        self.rank = actual_rank
        self.reg_lambda = use_lambda
        self.is_fitted = True

        logger.info(
            f"DMDc model fitted: rank={actual_rank}/{total_dim}, "
            f"lambda={use_lambda}, energy_retained={self.explained_energy*100:.2f}%"
        )
        return self

    def fit_with_validation(
        self,
        X_train: np.ndarray,
        X_p_train: np.ndarray,
        U_train: np.ndarray,
        X_val: np.ndarray,
        X_p_val: np.ndarray,
        U_val: np.ndarray,
        candidate_ranks: Optional[List[int]] = None,
        candidate_lambdas: Optional[List[float]] = None
    ) -> Dict[str, Any]:
        """
        Hyperparameter tuning of rank r and Tikhonov lambda strictly on validation data.
        Selects (r*, lambda*) that minimizes one-step validation RMSE.
        """
        ranks = candidate_ranks or list(range(4, min(self.n_states + self.n_controls + 1, 24)))
        lambdas = candidate_lambdas or [0.0, 1e-6, 1e-4, 1e-2, 0.1, 1.0]

        best_rmse = float("inf")
        best_rank = ranks[0]
        best_lambda = lambdas[0]
        tuning_results = []

        for r in ranks:
            for lmb in lambdas:
                self.fit(X_train, X_p_train, U_train, rank=r, reg_lambda=lmb)
                # Predict one-step on validation set
                X_p_pred = self.predict_step(X_val, U_val)
                rmse = float(np.sqrt(np.mean((X_p_val - X_p_pred)**2)))
                mae = float(np.mean(np.abs(X_p_val - X_p_pred)))
                
                # Check spectral radius for stability
                eigvals = la.eigvals(self.A)
                spec_rad = float(np.max(np.abs(eigvals)))

                tuning_results.append({
                    "rank": r,
                    "lambda": lmb,
                    "val_rmse": round(rmse, 5),
                    "val_mae": round(mae, 5),
                    "spectral_radius": round(spec_rad, 4),
                    "explained_energy": round(self.explained_energy, 5)
                })

                if rmse < best_rmse:
                    best_rmse = rmse
                    best_rank = r
                    best_lambda = lmb

        # Refit on training data with best hyperparameters
        self.fit(X_train, X_p_train, U_train, rank=best_rank, reg_lambda=best_lambda)
        
        self.fit_history = {
            "best_rank": best_rank,
            "best_lambda": best_lambda,
            "best_val_rmse": round(best_rmse, 5),
            "candidate_evaluations": tuning_results
        }
        logger.info(
            f"Validation selection complete: Optimal rank={best_rank}, "
            f"lambda={best_lambda} with Val RMSE={best_rmse:.5f}"
        )
        return self.fit_history

    def predict_step(self, x: np.ndarray, u: np.ndarray) -> np.ndarray:
        """
        One-step forward prediction: x(t+1) = A x(t) + B u(t).
        Supports 1D (n,) or 2D (batch_size, n) inputs.
        """
        self._check_fitted()
        if x.ndim == 1:
            return (self.A @ x) + (self.B @ u)
        elif x.ndim == 2:
            # (batch, n) @ A^T + (batch, m) @ B^T
            return (x @ self.A.T) + (u @ self.B.T)
        else:
            raise ValueError(f"Unsupported array dimension: {x.ndim}")

    def rollout(self, x0: np.ndarray, U_sequence: np.ndarray) -> np.ndarray:
        """
        Recursive multi-step forward simulation:
            x_1 = A x_0 + B u_0
            x_2 = A x_1 + B u_1
            ...
            x_H = A x_{H-1} + B u_{H-1}
        Returns trajectory array of shape (horizon, n).
        """
        self._check_fitted()
        horizon = len(U_sequence)
        trajectory = np.zeros((horizon, self.n_states), dtype=np.float64)
        
        current_x = x0.copy()
        for t in range(horizon):
            current_x = self.predict_step(current_x, U_sequence[t])
            trajectory[t] = current_x
            
        return trajectory

    def _check_fitted(self):
        if not self.is_fitted or self.A is None or self.B is None:
            raise RuntimeError("DMDcModel is not fitted. Call fit() first.")

    def save(self, output_dir: Path) -> Path:
        """
        Serializes A, B, G matrices, singular values, and metadata to NPZ and JSON.
        """
        self._check_fitted()
        output_dir.mkdir(parents=True, exist_ok=True)
        
        npz_path = output_dir / "dmdc_model.npz"
        np.savez_compressed(
            npz_path,
            A=self.A,
            B=self.B,
            G=self.G,
            singular_values=self.singular_values,
            state_vars=np.array(self.state_vars),
            control_vars=np.array(self.control_vars)
        )

        meta_path = output_dir / "dmdc_model_metadata.json"
        meta = {
            "rank": self.rank,
            "reg_lambda": self.reg_lambda,
            "n_states": self.n_states,
            "n_controls": self.n_controls,
            "explained_energy": self.explained_energy,
            "state_variables": self.state_vars,
            "control_variables": self.control_vars,
            "fit_history": self.fit_history
        }
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)

        logger.info(f"DMDc model successfully serialized to {output_dir}")
        return output_dir

    @classmethod
    def load(cls, output_dir: Path) -> "DMDcModel":
        """Loads serialized model from directory"""
        npz_path = output_dir / "dmdc_model.npz"
        meta_path = output_dir / "dmdc_model_metadata.json"
        
        if not npz_path.exists():
            raise FileNotFoundError(f"Missing model file {npz_path}")
            
        data = np.load(npz_path, allow_pickle=True)
        state_vars = [str(s) for s in data["state_vars"]]
        control_vars = [str(c) for c in data["control_vars"]]
        
        meta = {}
        if meta_path.exists():
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)

        model = cls(
            rank=meta.get("rank", data["A"].shape[0]),
            reg_lambda=meta.get("reg_lambda", 0.0),
            state_vars=state_vars,
            control_vars=control_vars
        )
        model.A = data["A"]
        model.B = data["B"]
        model.G = data.get("G", np.hstack([model.A, model.B]))
        model.singular_values = data.get("singular_values", None)
        model.explained_energy = meta.get("explained_energy", 1.0)
        model.fit_history = meta.get("fit_history", {})
        model.is_fitted = True
        return model
