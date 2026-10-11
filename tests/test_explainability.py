"""
SAMEER Phase 4 — Unit Tests for Explainability & "Why AQI Rises" Engine
Tests:
- Diagnosis of physical/chemical degradation mechanisms (Section 17)
- Koopman mode-based physical explanation (Section 18)
- Driver scoring formula: normalized_change * sensitivity * confidence (Section 19)
- Structured output schemas and provenance enforcement (Section 40)
"""
import pytest
import numpy as np
from pathlib import Path

from models.dmdc.preprocessing import DMDcPreprocessor
from models.explainability.why_aqi_rises import (
    AtmosphericDriver,
    WhyAQIRisesResult,
    WhyAQIRisesEngine
)
from models.attribution.attribution_schema import ProvenanceType


@pytest.fixture
def state_and_control_vars():
    scaler_path = Path("models/artifacts/dmdc/scaler.json")
    if not scaler_path.exists():
        pytest.skip("scaler.json not found")
    prep = DMDcPreprocessor.load(scaler_path)
    return prep.state_vars, prep.control_vars


def test_explainability_schema():
    """Validates Pydantic schema constraints and provenance"""
    ad = AtmosphericDriver(
        driver_name="inversion_strengthening",
        display_title="Thermal Inversion Strengthening",
        score=85.5,
        evidence="Inversion intensifies by 15.2 K",
        forecast_impact="Traps ground emissions under a warm capping lid.",
        associated_mode="Inversion-associated mode",
        confidence=0.95,
        provenance=ProvenanceType.INFERRED
    )
    assert ad.score == 85.5
    assert ad.provenance == ProvenanceType.INFERRED

    res = WhyAQIRisesResult(
        timestamp="2026-11-01T12:00:00Z",
        horizon_hours=24,
        initial_aqi=250.0,
        predicted_aqi=380.0,
        delta_aqi=130.0,
        dominant_driver="Thermal Inversion Strengthening",
        driver_scores=[ad],
        spectral_mode_association=[{"mode": "Inversion mode", "status": "ACTIVE"}],
        narrative_summary="AQI rises due to severe nocturnal inversion.",
        provenance=ProvenanceType.INFERRED
    )
    assert res.delta_aqi == 130.0
    assert len(res.driver_scores) == 1
    assert res.driver_scores[0].driver_name == "inversion_strengthening"


def test_why_aqi_rises_thermal_inversion_dominant(state_and_control_vars):
    """
    Simulates a scenario where thermal inversion strongly intensifies and PBL collapses,
    verifying that the engine identifies Thermal Inversion or Boundary Layer Collapse as dominant.
    """
    state_vars, control_vars = state_and_control_vars
    engine = WhyAQIRisesEngine(state_vars, control_vars)

    horizon = 24
    traj = np.zeros((horizon, len(state_vars)))
    u_seq = np.zeros((horizon, len(control_vars)))

    inv_idx = state_vars.index("inversion_strength")
    pbl_idx = state_vars.index("boundary_layer_height")
    pm25_idx = state_vars.index("pm25")

    # Initial state
    x0 = np.full(len(state_vars), 50.0)
    x0[inv_idx] = 2.0
    x0[pbl_idx] = 800.0
    x0[pm25_idx] = 120.0

    # Trajectory: Inversion jumps from 2.0 K to 22.0 K (+20 K), PBL drops from 800m to 120m
    for h in range(horizon):
        traj[h] = x0.copy()
        traj[h, inv_idx] = 2.0 + (20.0 * (h / (horizon - 1)))
        traj[h, pbl_idx] = 800.0 - (680.0 * (h / (horizon - 1)))
        traj[h, pm25_idx] = 120.0 + (150.0 * (h / (horizon - 1)))

    result = engine.diagnose(
        initial_state=x0,
        forecast_trajectory=traj,
        control_trajectory=u_seq,
        initial_aqi=280.0,
        final_aqi=420.0
    )

    assert isinstance(result, WhyAQIRisesResult)
    # The dominant driver must be related to inversion strengthening or boundary layer collapse
    assert result.dominant_driver in [
        "Thermal Inversion Strengthening",
        "Boundary Layer Collapse"
    ]
    assert result.driver_scores[0].score > 60.0

    # Scores must be sorted descending
    scores = [d.score for d in result.driver_scores]
    assert scores == sorted(scores, reverse=True)
    assert all(0.0 <= s <= 100.0 for s in scores)
    assert result.provenance == ProvenanceType.INFERRED

    # Check spectral mode association
    assert len(result.spectral_mode_association) >= 2
    inversion_mode = next(m for m in result.spectral_mode_association if "Inversion" in m["mode"])
    assert inversion_mode["status"] == "ACTIVE"


def test_why_aqi_rises_photochemical_ozone(state_and_control_vars):
    """
    Simulates high solar radiation and rapid ozone production,
    verifying that Photochemical Ozone Formation is diagnosed with a high impact score.
    """
    state_vars, control_vars = state_and_control_vars
    engine = WhyAQIRisesEngine(state_vars, control_vars)

    horizon = 24
    traj = np.zeros((horizon, len(state_vars)))
    u_seq = np.zeros((horizon, len(control_vars)))

    o3_idx = state_vars.index("o3")
    sol_idx = control_vars.index("solar_radiation")

    x0 = np.full(len(state_vars), 50.0)
    x0[o3_idx] = 30.0

    for h in range(horizon):
        traj[h] = x0.copy()
        traj[h, o3_idx] = 30.0 + (180.0 * (h / (horizon - 1)))  # O3 rises sharply
        u_seq[h, sol_idx] = 600.0  # High noon sun

    result = engine.diagnose(
        initial_state=x0,
        forecast_trajectory=traj,
        control_trajectory=u_seq,
        initial_aqi=100.0,
        final_aqi=250.0
    )

    o3_driver = next(d for d in result.driver_scores if d.driver_name == "photochemical_ozone")
    assert o3_driver.score >= 50.0
    assert "Ozone increases" in o3_driver.evidence


def test_why_aqi_rises_weak_ventilation(state_and_control_vars):
    """
    Simulates calm wind (< 1.5 m/s) and compressed PBL, verifying weak ventilation diagnosis.
    """
    state_vars, control_vars = state_and_control_vars
    engine = WhyAQIRisesEngine(state_vars, control_vars)

    horizon = 24
    traj = np.zeros((horizon, len(state_vars)))
    u_seq = np.zeros((horizon, len(control_vars)))

    ws_idx = state_vars.index("wind_speed_10m")
    pbl_idx = state_vars.index("boundary_layer_height")

    x0 = np.full(len(state_vars), 50.0)
    x0[ws_idx] = 1.0  # Calm wind
    x0[pbl_idx] = 300.0  # Shallow PBL -> ventilation coefficient = 300 m2/s << 2000

    for h in range(horizon):
        traj[h] = x0.copy()

    result = engine.diagnose(
        initial_state=x0,
        forecast_trajectory=traj,
        control_trajectory=u_seq,
        initial_aqi=200.0,
        final_aqi=300.0
    )

    vent_driver = next(d for d in result.driver_scores if d.driver_name == "weak_ventilation")
    assert vent_driver.score >= 40.0
    assert "ventilation coefficient" in vent_driver.evidence.lower()
