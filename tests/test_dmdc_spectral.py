"""
Unit tests for Koopman Spectral Decomposition, Stability, and Physical Mode Classification
"""
import pytest
import numpy as np
from models.dmdc.spectral_analysis import KoopmanSpectralAnalyzer


def test_spectral_decomposition_and_frequencies():
    state_vars = ["boundary_layer_height", "temperature_2m", "pm25"]
    analyzer = KoopmanSpectralAnalyzer(state_vars=state_vars, dt_hours=1.0)

    # 3x3 stable matrix with 1 complex conjugate pair (oscillation) and 1 real decaying mode
    # Eigenvalues: 0.9*exp(i*pi/12) (24h period) and 0.8
    theta = 2.0 * np.pi / 24.0
    r = 0.95
    A = np.array([
        [r * np.cos(theta), -r * np.sin(theta), 0.0],
        [r * np.sin(theta),  r * np.cos(theta), 0.0],
        [0.0,                0.0,               0.85]
    ])

    report = analyzer.analyze_operator(A)
    summary = report["stability_summary"]
    modes = report["modes"]

    assert summary["is_spectrally_stable"]
    assert summary["spectral_radius"] == pytest.approx(0.95, abs=1e-3)
    assert len(modes) == 3

    # Check oscillation period for the complex modes (~24h)
    oscillatory_modes = [m for m in modes if m["oscillation_period_hours"] != "INF"]
    assert len(oscillatory_modes) >= 2
    for m in oscillatory_modes:
        assert m["oscillation_period_hours"] == pytest.approx(24.0, abs=0.5)


def test_controlled_spectral_stabilization():
    # Matrix with unstable eigenvalue magnitude 1.2
    A_unstable = np.array([
        [1.20, 0.00],
        [0.00, 0.80]
    ])

    analyzer = KoopmanSpectralAnalyzer(state_vars=["s1", "s2"])
    A_stab, info = analyzer.stabilize_operator(A_unstable, max_radius=1.0)

    assert info["stabilization_applied"]
    assert info["original_spectral_radius"] == 1.20
    assert info["stabilized_spectral_radius"] == pytest.approx(1.0, abs=1e-3)
    assert info["modified_modes_count"] == 1

    # Check new eigenvalues
    new_eigvals = np.abs(np.linalg.eigvals(A_stab))
    assert np.all(new_eigvals <= 1.0001)


def test_mode_physical_classification():
    state_vars = [
        "boundary_layer_height", "temperature_2m", "u_wind_10m", "v_wind_10m",
        "wind_speed_10m", "relative_humidity", "surface_pressure", "inversion_strength",
        "pm25", "pm10", "o3", "no2", "so2", "co", "cams_aerosol"
    ]
    analyzer = KoopmanSpectralAnalyzer(state_vars=state_vars)

    # Inversion mode test
    top_feats_inv = [
        {"variable": "inversion_strength", "loading": 0.45},
        {"variable": "temperature_2m", "loading": 0.20}
    ]
    cat_inv, _ = analyzer._classify_mode(top_feats_inv, period_hours=float("inf"), stability="STABLE", growth_rate=-0.05)
    assert cat_inv == "Inversion-associated"

    # Ventilation mode test
    top_feats_vent = [
        {"variable": "boundary_layer_height", "loading": 0.50},
        {"variable": "wind_speed_10m", "loading": 0.25}
    ]
    cat_vent, _ = analyzer._classify_mode(top_feats_vent, period_hours=24.0, stability="STABLE", growth_rate=-0.02)
    assert cat_vent == "Ventilation-associated"

    # Unclassified mode fallback
    top_feats_unclass = [
        {"variable": "surface_pressure", "loading": 0.15},
        {"variable": "relative_humidity", "loading": 0.12}
    ]
    cat_unclass, _ = analyzer._classify_mode(top_feats_unclass, period_hours=12.0, stability="STABLE", growth_rate=-0.01)
    assert cat_unclass == "UNCLASSIFIED MODE"
