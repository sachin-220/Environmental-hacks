"""
SAMEER Phase 4 — Unit Tests for Source Attribution & Counterfactual Intelligence
Tests:
- Sector control mapping & perturbation vectors
- Synthetic controlled source attribution tests (Section 34)
- Fire clustering, plume arrival clock & upwind filtering (Sections 7-10)
- Regional vs. Local vs. Background spatial disaggregation (Section 13)
- CPCB NAQI calculation & counterfactual what-if simulation (Sections 15-16)
- Provenance tagging & non-linear residual quantification
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path

from models.dmdc.dmdc_model import DMDcModel
from models.dmdc.preprocessing import DMDcPreprocessor
from models.attribution.attribution_schema import (
    ProvenanceType,
    AttributionSector,
    SourcePerturbation,
    FireCluster,
    PlumeArrivalEstimate,
    SectorContribution,
    RegionalAttribution,
    AttributionResult
)
from models.attribution.sector_attribution import SectorAttributionEngine
from models.attribution.fire_attribution import FireAttributionEngine
from models.attribution.regional_attribution import RegionalAttributionEngine
from models.attribution.counterfactual import CounterfactualEngine
from models.attribution.attribution_engine import SourceAttributionEngine
from models.attribution.validation import AttributionValidator


@pytest.fixture
def loaded_dmdc():
    """Loads verified Phase 3.2 production DMDc model and scaler"""
    model_dir = Path("models/artifacts/dmdc")
    if not (model_dir / "dmdc_model.npz").exists() or not (model_dir / "scaler.json").exists():
        pytest.skip("Verified Phase 3.2 model artifacts not present")
    model = DMDcModel.load(model_dir)
    preprocessor = DMDcPreprocessor.load(model_dir / "scaler.json")
    return model, preprocessor


def test_attribution_schema_validation():
    """Validates schema constraints, data types, and provenance enforcement"""
    pert = SourcePerturbation(
        sector="road_transport",
        species="anthro_nox",
        baseline_value=30.0,
        perturbation_fraction=0.25,
        perturbed_value=22.5,
        provenance=ProvenanceType.SCENARIO
    )
    assert pert.perturbed_value == 22.5
    assert pert.provenance == ProvenanceType.SCENARIO

    sc = SectorContribution(
        sector="industry",
        delta_pm25=12.5,
        delta_pm10=18.0,
        percentage_pm25=28.5,
        method="MODELLED COUNTERFACTUAL ZERO-OUT",
        provenance=ProvenanceType.COUNTERFACTUAL
    )
    assert sc.percentage_pm25 == 28.5
    assert sc.provenance == ProvenanceType.COUNTERFACTUAL

    reg = RegionalAttribution(
        local_pm25=99.0,
        regional_pm25=54.0,
        background_pm25=27.0,
        local_percentage=55.0,
        regional_percentage=30.0,
        background_percentage=15.0,
        total_pm25=180.0,
        provenance=ProvenanceType.INFERRED
    )
    assert reg.local_percentage + reg.regional_percentage + reg.background_percentage == 100.0


def test_sector_control_mapping(loaded_dmdc):
    """Verifies mapping from 6 sectors to 8 Phase 3 control variables"""
    model, preprocessor = loaded_dmdc
    sector_engine = SectorAttributionEngine(model, preprocessor)

    # Road transport should reduce anthro_nox, anthro_co, anthro_voc
    u_base = np.array([20.0, 10.0, 40.0, 15.0, 50.0, 65.0, 200.0, 0.0])
    delta_trans = sector_engine.get_sectoral_reduction_vector(
        AttributionSector.ROAD_TRANSPORT.value, reduction_fraction=1.0, baseline_u=u_base
    )
    assert delta_trans.shape == (8,)
    # anthro_nox index 0, anthro_co index 2, anthro_voc index 3
    assert delta_trans[0] > 0.0  # anthro_nox
    assert delta_trans[2] > 0.0  # anthro_co
    assert delta_trans[3] > 0.0  # anthro_voc

    # Power plants should predominantly reduce anthro_so2 (index 1) and anthro_nox (index 0)
    delta_power = sector_engine.get_sectoral_reduction_vector(
        AttributionSector.POWER_PLANTS.value, reduction_fraction=1.0, baseline_u=u_base
    )
    assert delta_power[1] > 0.0  # anthro_so2
    assert delta_power[0] > 0.0  # anthro_nox

    # Agriculture should affect fire_frp (index 4) and plume_transport_score (index 5)
    delta_agri = sector_engine.get_sectoral_reduction_vector(
        AttributionSector.AGRICULTURE.value, reduction_fraction=0.5, baseline_u=u_base
    )
    assert delta_agri[4] == 25.0  # 50% of 50.0
    assert delta_agri[5] == 32.5  # 50% of 65.0


def test_synthetic_controlled_attribution():
    """
    Section 34 Validation: Synthetic controlled tests where ground truth is known.
    Verifies that the attribution logic correctly identifies dominant sources under synthetic settings.
    """
    res1 = AttributionValidator.test_single_source_dominance()
    assert res1["passed"] is True
    assert res1["percentages"][AttributionSector.ROAD_TRANSPORT.value] == 100.0

    res2 = AttributionValidator.test_equal_source_parity()
    assert res2["passed"] is True
    assert res2["percentages"][AttributionSector.ROAD_TRANSPORT.value] == 50.0

    res3 = AttributionValidator.test_nonlinear_interaction_residual()
    assert res3["passed"] is True
    assert res3["interaction_residual"] == 5.0


def test_fire_clustering_and_plume_clock(loaded_dmdc):
    """
    Sections 7 & 8: Verifies FIRMS fire clustering and plume arrival clock calculation.
    """
    model, preprocessor = loaded_dmdc
    fire_engine = FireAttributionEngine(model, preprocessor)

    # Synthetic FIRMS fires in Punjab (NW of Delhi ~28.61, 77.21)
    fires_data = {
        "latitude": [30.4, 30.5, 30.45, 27.5],  # 3 in Punjab (NW), 1 in Agra/South
        "longitude": [75.8, 75.9, 75.85, 78.0],
        "frp": [120.0, 150.0, 90.0, 50.0],
        "acq_date": ["2026-11-01", "2026-11-01", "2026-11-01", "2026-11-01"],
        "acq_time": ["1330", "1330", "1330", "1330"],
        "confidence": [85, 90, 80, 75]
    }
    df_fires = pd.DataFrame(fires_data)

    # Wind blowing from NW towards SE: u > 0, v < 0 (e.g. u = 3.0 m/s eastward, v = -3.0 m/s southward)
    # Wind vector (u=3.0, v=-3.0) blows FROM 315 deg (North-West)
    clusters = fire_engine.cluster_fires(df_fires)
    assert len(clusters) >= 1

    estimates = fire_engine.estimate_plume_arrivals(
        clusters, u_wind=3.0, v_wind=-3.0
    )

    assert len(estimates) >= 1
    # At least one cluster should be flagged as upwind from the NW direction
    affecting = [e for e in estimates if e.is_upwind]
    assert len(affecting) >= 1

    first = affecting[0]
    assert first.total_frp >= 90.0
    assert first.estimated_distance_km > 100.0  # Punjab to Delhi is > 100km
    assert first.estimated_transport_time_hours > 0.0
    assert 0.0 <= first.transport_confidence <= 1.0
    assert first.provenance == ProvenanceType.INFERRED or first.provenance == ProvenanceType.MODELLED


def test_upwind_filter_exclusion(loaded_dmdc):
    """
    Section 9: Upwind filter should exclude downwind fire sources.
    If wind blows from North-West (u=3.0, v=-3.0), fires to the South-East should be rejected.
    """
    model, preprocessor = loaded_dmdc
    fire_engine = FireAttributionEngine(model, preprocessor)

    # Fire strictly South-East of Delhi (e.g. lat=27.0, lon=79.0)
    se_fires = pd.DataFrame({
        "latitude": [27.0],
        "longitude": [79.0],
        "frp": [300.0],
        "acq_date": ["2026-11-01"],
        "acq_time": ["1400"],
        "confidence": [95]
    })
    clusters = fire_engine.cluster_fires(se_fires)
    assert len(clusters) == 1

    # Wind from NW (u=3.0, v=-3.0) carries smoke SE-ward away from Delhi
    estimates = fire_engine.estimate_plume_arrivals(clusters, u_wind=3.0, v_wind=-3.0)
    assert len(estimates) == 1
    assert estimates[0].is_upwind is False
    assert estimates[0].transport_confidence <= 0.2


def test_regional_vs_local_disaggregation(loaded_dmdc):
    """
    Section 13: Verifies Local vs. Regional vs. Background percentage disaggregation.
    """
    model, preprocessor = loaded_dmdc
    reg_engine = RegionalAttributionEngine(model, preprocessor)

    x0 = np.full(15, 50.0)
    x0[preprocessor.state_vars.index("pm25")] = 200.0
    u_seq = np.zeros((24, 8))
    u_seq[:, 5] = 65.0

    res = reg_engine.disaggregate_spatial_scales(
        x0_physical=x0,
        u_sequence_physical=u_seq,
        horizon=24
    )
    assert isinstance(res, RegionalAttribution)
    assert abs((res.local_percentage + res.regional_percentage + res.background_percentage) - 100.0) < 1e-4
    assert res.local_percentage >= 0.0
    assert res.regional_percentage >= 0.0
    assert res.background_percentage >= 0.0
    assert res.provenance == ProvenanceType.INFERRED


def test_counterfactual_cpcb_naqi(loaded_dmdc):
    """
    Section 16: Verifies standard CPCB NAQI calculation breakpoints.
    """
    from models.dmdc.aqi import NationalAQICalculator

    # Good: 0-30 -> 0-50
    sub_good = NationalAQICalculator.calculate_sub_index("pm25", 15.0)
    assert 0 <= sub_good <= 50

    # Satisfactory: 31-60 -> 51-100
    sub_sat = NationalAQICalculator.calculate_sub_index("pm25", 45.0)
    assert 51 <= sub_sat <= 100

    # Moderate: 61-90 -> 101-200
    sub_mod = NationalAQICalculator.calculate_sub_index("pm25", 75.0)
    assert 101 <= sub_mod <= 200

    # Poor: 91-120 -> 201-300
    sub_poor = NationalAQICalculator.calculate_sub_index("pm25", 105.0)
    assert 201 <= sub_poor <= 300

    # Very Poor: 121-250 -> 301-400
    sub_vpoor = NationalAQICalculator.calculate_sub_index("pm25", 180.0)
    assert 301 <= sub_vpoor <= 400

    # Severe: 250+ -> 401-500
    sub_sev = NationalAQICalculator.calculate_sub_index("pm25", 320.0)
    assert 401 <= sub_sev <= 500


def test_source_attribution_engine_analyze(loaded_dmdc):
    """
    End-to-end integration test of SourceAttributionEngine.analyze
    """
    model, preprocessor = loaded_dmdc
    engine = SourceAttributionEngine(model, preprocessor)

    # Realistic initial state & control sequence
    x0 = np.full(15, 50.0)
    x0[preprocessor.state_vars.index("pm25")] = 200.0
    u_seq = np.zeros((24, 8))
    u_seq[:, 5] = 65.0  # plume_transport_score
    u_seq[:, 6] = 200.0 # solar_radiation

    result = engine.analyze(
        x0_physical=x0,
        u_sequence_physical=u_seq,
        fires_df=None,
        u_wind=-2.0,
        v_wind=-1.5,
        horizon=24
    )

    assert isinstance(result, AttributionResult)
    assert result.target_cell == "D03_R30_C30"
    assert len(result.sector_contributions) >= 6
    assert result.regional_breakdown.local_percentage + result.regional_breakdown.regional_percentage + result.regional_breakdown.background_percentage == 100.0
    assert result.baseline_pm25 > 0.0
    assert result.provenance == ProvenanceType.COUNTERFACTUAL
