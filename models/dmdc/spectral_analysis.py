"""
Koopman Spectral Decomposition, Stability Analysis, and Physical Mode Interpretation
"""
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import json
import numpy as np
import scipy.linalg as la

from config.logging_config import get_logger
from models.dmdc.config import DMDcFeatureConfig

logger = get_logger("models.dmdc.spectral_analysis")


class KoopmanSpectralAnalyzer:
    """
    Performs spectral eigendecomposition on the learned discrete Koopman state operator A.
    Quantifies eigenvalues, continuous frequencies, mode energies, stability bounds,
    and assigns evidence-based physical interpretation categories.
    """

    def __init__(self, state_vars: Optional[List[str]] = None, dt_hours: float = 1.0):
        self.state_vars = state_vars or list(DMDcFeatureConfig.STATE_VARIABLES)
        self.dt_hours = dt_hours
        self.n_states = len(self.state_vars)

    def analyze_operator(
        self,
        A: np.ndarray,
        x0_reference: Optional[np.ndarray] = None
    ) -> Dict[str, Any]:
        """
        Decomposes state-transition operator A into eigenvalues, Koopman modes, and spectral diagnostics.
        """
        if A.shape != (self.n_states, self.n_states):
            raise ValueError(f"Operator A shape {A.shape} does not match ({self.n_states}, {self.n_states})")

        # Eigendecomposition: A * W = W * Lambda
        eigvals, eigvecs = la.eig(A)

        # Spectral radius
        magnitudes = np.abs(eigvals)
        spectral_radius = float(np.max(magnitudes))

        # Default reference state for mode amplitude calculation (unit norm or mean state)
        if x0_reference is None or len(x0_reference) != self.n_states:
            x0 = np.ones(self.n_states, dtype=np.float64) / np.sqrt(self.n_states)
        else:
            x0 = np.nan_to_num(x0_reference, nan=0.0).astype(np.float64)

        # Mode amplitudes: b = W^(-1) * x0
        try:
            b_amplitudes = la.solve(eigvecs, x0)
        except la.LinAlgError:
            b_amplitudes = la.pinv(eigvecs) @ x0

        # Sort modes by energy contribution: E_i = ||Phi_i||_2^2 * |b_i|^2
        mode_energies = np.array([
            float(np.linalg.norm(eigvecs[:, i])**2 * np.abs(b_amplitudes[i])**2)
            for i in range(len(eigvals))
        ])
        total_energy = float(np.sum(mode_energies))
        rel_energies = mode_energies / total_energy if total_energy > 0 else np.ones(len(eigvals)) / len(eigvals)

        sorted_indices = np.argsort(mode_energies)[::-1]

        # Analyze individual modes
        mode_records = []
        stable_count = 0
        near_unit_count = 0
        unstable_count = 0

        for rank_idx, i in enumerate(sorted_indices):
            lam = eigvals[i]
            mag = float(np.abs(lam))
            phase = float(np.angle(lam))

            # Continuous eigenvalue: mu = ln(lambda) / dt = sigma + i*omega
            # Add small epsilon to prevent log(0)
            log_lam = np.log(lam if mag > 1e-12 else 1e-12)
            sigma = float(np.real(log_lam) / self.dt_hours)       # growth/decay rate (1/h)
            omega = float(np.imag(log_lam) / self.dt_hours)       # angular frequency (rad/h)
            
            # Period (hours)
            period_hours = float(2.0 * np.pi / abs(omega)) if abs(omega) > 1e-5 else float("inf")
            freq_cycles_per_day = float(abs(omega) * 24.0 / (2.0 * np.pi))

            # Stability classification
            if mag < 0.995:
                stability = "STABLE"
                stable_count += 1
            elif mag <= 1.005:
                stability = "PERSISTENT"
                near_unit_count += 1
            else:
                stability = "UNSTABLE"
                unstable_count += 1

            # Feature loadings: |w_i|
            loadings = np.abs(eigvecs[:, i])
            total_loading = np.sum(loadings)
            norm_loadings = loadings / total_loading if total_loading > 0 else loadings
            
            # Top contributing variables
            top_var_indices = np.argsort(norm_loadings)[::-1]
            top_features = [
                {"variable": self.state_vars[v_idx], "loading": round(float(norm_loadings[v_idx]), 4)}
                for v_idx in top_var_indices[:4]
            ]

            # Evidence-based physical mode classification
            classification, rationale = self._classify_mode(
                top_features=top_features,
                period_hours=period_hours,
                stability=stability,
                growth_rate=sigma
            )

            mode_records.append({
                "mode_id": int(i),
                "energy_rank": int(rank_idx + 1),
                "eigenvalue_real": round(float(np.real(lam)), 5),
                "eigenvalue_imag": round(float(np.imag(lam)), 5),
                "magnitude": round(mag, 5),
                "phase_radians": round(phase, 4),
                "growth_rate_per_hour": round(sigma, 5),
                "frequency_rad_per_hour": round(omega, 5),
                "oscillation_period_hours": round(period_hours, 2) if period_hours != float("inf") else "INF",
                "frequency_cycles_per_day": round(freq_cycles_per_day, 3),
                "mode_energy": round(float(mode_energies[i]), 5),
                "relative_energy_fraction": round(float(rel_energies[i]), 5),
                "stability_class": stability,
                "top_features": top_features,
                "physical_classification": classification,
                "classification_rationale": rationale
            })

        stability_summary = {
            "spectral_radius": round(spectral_radius, 4),
            "is_spectrally_stable": bool(spectral_radius <= 1.005),
            "stable_mode_count": stable_count,
            "near_unit_mode_count": near_unit_count,
            "unstable_mode_count": unstable_count,
            "total_modes": len(eigvals)
        }

        report = {
            "stability_summary": stability_summary,
            "modes": mode_records
        }
        logger.info(
            f"Spectral analysis completed: Spectral radius={spectral_radius:.4f}, "
            f"Stable={stable_count}, Persistent={near_unit_count}, Unstable={unstable_count}"
        )
        return report

    def _classify_mode(
        self,
        top_features: List[Dict[str, Any]],
        period_hours: float,
        stability: str,
        growth_rate: float
    ) -> Tuple[str, str]:
        """
        Assigns physical classification based strictly on quantitative loading evidence and temporal periodicity.
        """
        top_var_names = [f["variable"] for f in top_features]
        primary_var = top_var_names[0] if top_var_names else ""
        primary_loading = top_features[0]["loading"] if top_features else 0.0

        # Criterion 1: Inversion Mode (thermal inversion, vertical temperature structure)
        if "inversion_strength" in top_var_names[:2] and primary_loading > 0.25:
            return (
                "Inversion-associated",
                f"High loading on inversion_strength ({primary_loading:.2f}) with {stability.lower()} dynamics."
            )

        # Criterion 2: Ventilation Mode (PBL height, surface wind speed)
        if ("boundary_layer_height" in top_var_names[:2] or "wind_speed_10m" in top_var_names[:2]) and primary_loading > 0.25:
            return (
                "Ventilation-associated",
                f"Dominant loading on boundary_layer_height/wind ({primary_loading:.2f}) governing vertical mixing."
            )

        # Criterion 3: Regional Transport Mode (wind directional components U/V)
        if ("u_wind_10m" in top_var_names[:2] or "v_wind_10m" in top_var_names[:2]) and primary_loading > 0.25:
            return (
                "Regional transport-associated",
                f"Dominant horizontal wind component loading ({primary_loading:.2f}) controlling advection."
            )

        # Criterion 4: Photochemistry / Ozone Mode (O3, diurnal ~20-28h periodicity)
        if "o3" in top_var_names[:2] and (18.0 <= period_hours <= 30.0 or primary_loading > 0.30):
            return (
                "Ozone/photochemistry-associated",
                f"High loading on O3 ({primary_loading:.2f}) with diurnal photolytic oscillation period ({period_hours:.1f}h)."
            )

        # Criterion 5: Aerosol-Radiation Mode (PM2.5, AOD / cams_aerosol)
        if ("pm25" in top_var_names[:2] or "cams_aerosol" in top_var_names[:2]) and primary_loading > 0.25:
            return (
                "Aerosol-radiation-associated",
                f"Dominant particulate loading ({primary_loading:.2f}) with radiative extinction feedback."
            )

        # Default fallback: strictly label unclassified when evidence threshold is not met
        return (
            "UNCLASSIFIED MODE",
            f"Mixed loadings across {', '.join(top_var_names[:3])} without single dominant physical driver."
        )

    @staticmethod
    def stabilize_operator(A: np.ndarray, max_radius: float = 1.0) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Controlled spectral stabilization:
        Projects eigenvalues with magnitude > max_radius onto the bounding circle |lambda| = max_radius.
        Guarantees discrete Lyapunov stability without silently altering stable modes.
        """
        eigvals, eigvecs = la.eig(A)
        original_radius = float(np.max(np.abs(eigvals)))
        
        if original_radius <= max_radius:
            return A.copy(), {
                "stabilization_applied": False,
                "original_spectral_radius": round(original_radius, 4),
                "stabilized_spectral_radius": round(original_radius, 4),
                "modified_modes_count": 0
            }

        # Project unstable eigenvalues
        stabilized_eigvals = np.zeros_like(eigvals)
        modified_count = 0

        for i, lam in enumerate(eigvals):
            mag = np.abs(lam)
            if mag > max_radius:
                # Scale to boundary: (lam / mag) * max_radius
                stabilized_eigvals[i] = (lam / mag) * max_radius
                modified_count += 1
            else:
                stabilized_eigvals[i] = lam

        # Reconstruct stabilized operator: A_stab = Re(W * Lambda_stab * W^(-1))
        Lambda_stab = np.diag(stabilized_eigvals)
        try:
            A_stab = np.real(eigvecs @ Lambda_stab @ la.inv(eigvecs))
        except la.LinAlgError:
            A_stab = np.real(eigvecs @ Lambda_stab @ la.pinv(eigvecs))

        new_radius = float(np.max(np.abs(la.eigvals(A_stab))))
        
        info = {
            "stabilization_applied": True,
            "original_spectral_radius": round(original_radius, 4),
            "stabilized_spectral_radius": round(new_radius, 4),
            "modified_modes_count": modified_count
        }
        logger.info(
            f"Operator stabilized: Spectral radius {original_radius:.4f} -> {new_radius:.4f} "
            f"({modified_count} modes projected)"
        )
        return A_stab, info
