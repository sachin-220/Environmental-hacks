"""
SAMEER Phase 5 Integration & Decision Control Room Regression Tests
Verifies:
1. DMDc rank-12 model immutability and spectral properties.
2. REST API endpoints returning valid schemas and explicit provenance tags.
3. Analytical Lyapunov uncertainty propagation bounds (lower <= mean <= upper).
4. Constrained MPC policy optimization across strategies (Low-Cost, Balanced, Aggressive).
5. Target feasibility and infeasibility handling for unachievable constraints.
6. 3-km spatial grid slice and active fire plume estimates.
7. SPA serving integrity.
"""
import pytest
import numpy as np
from fastapi.testclient import TestClient
from api.server import app, state


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def test_dmdc_model_immutability():
    """Verify production DMDc model rank, dimension, and spectral radius remain unchanged"""
    assert state.is_ready, "Backend state should be initialized"
    assert state.model is not None, "DMDc model should be loaded"
    assert state.model.rank == 12, f"Expected rank 12, got {state.model.rank}"
    assert state.model.A.shape == (15, 15), f"Expected A shape (15, 15), got {state.model.A.shape}"
    assert state.model.B.shape == (15, 8), f"Expected B shape (15, 8), got {state.model.B.shape}"
    
    # Numerical spectral radius check
    eigvals = np.linalg.eigvals(state.model.A)
    rho_raw = float(np.max(np.abs(eigvals)))
    assert abs(rho_raw - 1.1512) < 0.01, f"Expected raw spectral radius ~1.1512, got {rho_raw}"


def test_api_health(client):
    """Verify health endpoint schema, status, and operating mode"""
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "READY"
    assert data["dmdc_model"]["rank"] == 12
    assert "MODE" in data["operating_mode"] or "TELEMETRY" in data["operating_mode"]
    assert "ROLLOUT" in data["scientific_disclaimer"]


def test_api_current_state(client):
    """Verify current atmospheric state and CPCB NAQI calculation"""
    resp = client.get("/api/state")
    assert resp.status_code == 200
    data = resp.json()
    assert "aqi" in data
    assert data["aqi"] > 0
    assert "pm25" in data
    assert "boundary_layer_height" in data
    assert data["provenance"] in ["MODELLED", "OBSERVED"]


def test_api_forecast_rollout_and_uncertainty(client):
    """Verify 72h forward forecast, Lyapunov uncertainty bounds, and section 10 disclaimer"""
    resp = client.get("/api/forecast?horizon=72")
    assert resp.status_code == 200
    data = resp.json()
    assert data["horizon_hours"] == 72
    assert "rollout_latency_ms" in data
    assert "ROLLOUT" in data["scientific_disclaimer"]
    assert "ROLLOUT" in data["provenance"] or data["provenance"] == "MODELLED"
    
    timeline = data["hourly_timeline"]
    assert len(timeline) == 72
    for item in timeline:
        assert item["pm25"] >= 0.0
        assert item["pm25_lower"] <= item["pm25"] + 1e-3, "Lower bound must be <= mean"
        assert item["pm25_upper"] >= item["pm25"] - 1e-3, "Upper bound must be >= mean"
        assert "aqi" in item
        assert "category" in item


def test_api_spatial_grid(client):
    """Verify 3-km D03 spatial grid endpoint"""
    resp = client.get("/api/grid?variable=pm25&time_step=0")
    assert resp.status_code == 200
    data = resp.json()
    assert data["variable"] == "pm25"
    assert len(data["cells"]) > 0
    assert data["grid_resolution_km"] == 3.0
    assert "ROLLOUT" in data["provenance"] or data["provenance"] == "MODELLED"


def test_api_attribution(client):
    """Verify source attribution shares and zero-out counterfactuals"""
    resp = client.get("/api/attribution")
    assert resp.status_code == 200
    data = resp.json()
    regional = data["regional_breakdown"]
    total = regional["local_percentage"] + regional["regional_percentage"] + regional["background_percentage"]
    assert abs(total - 100.0) < 0.1, f"Attribution shares must sum to 100%, got {total}"
    assert len(data["sector_contributions"]) >= 4
    for sector_name, sector in data["sector_contributions"].items():
        assert sector["provenance"] == "COUNTERFACTUAL"
        assert sector["delta_pm25"] >= 0.0


def test_api_plume_clock(client):
    """Verify agricultural fire plume tracking and ETA estimates"""
    resp = client.get("/api/plumes")
    assert resp.status_code == 200
    data = resp.json()
    assert data["active_fire_clusters_count"] > 0
    assert len(data["plume_estimates"]) > 0
    for est in data["plume_estimates"]:
        assert est["estimated_distance_km"] > 0
        assert est["estimated_transport_time_hours"] > 0
        assert est["provenance"] == "INFERRED"


def test_api_why_aqi_rises(client):
    """Verify explainability engine physical diagnostics and Koopman modes"""
    resp = client.get("/api/explain")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["driver_scores"]) > 0
    assert "spectral_mode_association" in data
    assert data["provenance"] == "INFERRED"


def test_api_mpc_optimization(client):
    """Verify constrained MPC policy optimization across strategies"""
    for strategy in ["LOW_COST", "BALANCED", "AGGRESSIVE"]:
        resp = client.post("/api/mpc", json={"strategy": strategy, "horizon": 24})
        assert resp.status_code == 200
        data = resp.json()
        assert data["optimization_success"] is True
        assert data["mean_pm25_reduction"] >= 0.0
        assert data["relative_intervention_cost"] >= 0.0
        assert len(data["hourly_timeline"]) == 24
        assert data["provenance"] == "SCENARIO"


def test_api_mpc_infeasibility_handling(client):
    """Verify unachievable target AQI returns infeasible with valid reason"""
    resp = client.post("/api/mpc", json={"target_aqi": 50.0, "horizon": 12})
    assert resp.status_code == 200
    data = resp.json()
    assert data["feasibility_status"] == "INFEASIBLE"
    assert "message" in data
    assert "cannot be fully satisfied" in data["message"].lower() or "infeasible" in data["message"].lower()


def test_api_provenance_registry(client):
    """Verify complete provenance registry returns all components"""
    resp = client.get("/api/provenance")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["registry"]) >= 7
    tags = {item["provenance"] for item in data["registry"]}
    assert "MODELLED" in tags
    assert "COUNTERFACTUAL" in tags
    assert "OBSERVED" in tags


def test_spa_serving(client):
    """Verify production SPA index.html is served at root"""
    resp = client.get("/")
    assert resp.status_code == 200
    assert "AERIS" in resp.text
    assert "root" in resp.text


def test_api_activity(client):
    """Verify /api/activity returns operational status, pipeline stages, and event log"""
    resp = client.get("/api/activity")
    assert resp.status_code == 200
    data = resp.json()
    assert "pipeline_status" in data
    assert data["pipeline_status"]["data_ingestion"] == "OPERATIONAL"
    assert data["pipeline_status"]["dmdc_forecast"] == "READY"
    assert data["pipeline_status"]["mpc_engine"] == "READY"
    assert "system_status" in data
    assert "OPERATIONAL" in data["system_status"]
    assert "events" in data
    assert len(data["events"]) >= 5
    services = [e["service"] for e in data["events"]]
    assert "DMDC" in services
    assert "WRF-CHEM" in services
    assert "operating_mode" in data


