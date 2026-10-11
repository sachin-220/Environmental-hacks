import sys
from pathlib import Path

# Add repository root to sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import time
import json
from datetime import datetime
from fastapi.testclient import TestClient
from api.server import app, state

client = TestClient(app)

results = []

def test_endpoint(name, method, url, **kwargs):
    t0 = time.perf_counter()
    try:
        if method == "GET":
            resp = client.get(url, **kwargs)
        elif method == "POST":
            resp = client.post(url, **kwargs)
        else:
            raise ValueError(f"Unknown method {method}")
        latency_ms = (time.perf_counter() - t0) * 1000
        
        status = resp.status_code
        data = None
        error_msg = None
        content_type = resp.headers.get("content-type", "")
        if "application/json" in content_type:
            try:
                data = resp.json()
            except Exception as e:
                error_msg = f"JSON parse error: {e}"
        else:
            data = resp.text[:200]
            
        success = (status == 200) and (error_msg is None)
        res = {
            "name": name,
            "method": method,
            "url": url,
            "status_code": status,
            "latency_ms": round(latency_ms, 2),
            "success": success,
            "error": error_msg,
            "summary": ""
        }
        return res, data
    except Exception as e:
        latency_ms = (time.perf_counter() - t0) * 1000
        return {
            "name": name,
            "method": method,
            "url": url,
            "status_code": 0,
            "latency_ms": round(latency_ms, 2),
            "success": False,
            "error": str(e),
            "summary": "Exception raised"
        }, None

print("=== STARTING FULL API ENDPOINT SUITE ===")

# 1. Root SPA
r, data = test_endpoint("Root SPA", "GET", "/")
r["summary"] = f"HTML page length: {len(data) if data else 0} chars"
results.append(r)

# 2. OpenAPI Spec
r, data = test_endpoint("OpenAPI Schema", "GET", "/openapi.json")
r["summary"] = f"Paths count: {len(data.get('paths', {})) if data else 0}"
results.append(r)

# 3. Health
r, data = test_endpoint("Health Check", "GET", "/api/health")
if data:
    r["summary"] = f"Status: {data.get('status')}, Model Rank: {data.get('dmdc_model', {}).get('rank')}, Operating Mode: {data.get('operating_mode')}"
results.append(r)

# 4. State
r, data = test_endpoint("Current Atmospheric State", "GET", "/api/state")
if data:
    r["summary"] = f"AQI: {data.get('aqi')}, PM2.5: {data.get('pm25')}, Category: {data.get('category')}, Provenance: {data.get('provenance')}"
results.append(r)

# 5. Forecast 24h
r, data = test_endpoint("Forecast (24h)", "GET", "/api/forecast?horizon=24")
if data:
    pts = len(data.get('hourly_timeline', []))
    r["summary"] = f"Timeline points: {pts}, Provenance: {data.get('provenance')}, Latency reported: {data.get('rollout_latency_ms')} ms"
results.append(r)

# 6. Forecast 72h
r, data = test_endpoint("Forecast (72h)", "GET", "/api/forecast?horizon=72")
if data:
    pts = len(data.get('hourly_timeline', []))
    r["summary"] = f"Timeline points: {pts}, Provenance: {data.get('provenance')}"
results.append(r)

# 7. Spatial Grid (PM2.5)
r, data = test_endpoint("Spatial Grid (PM2.5)", "GET", "/api/grid?variable=pm25&time_step=0")
if data:
    cells = len(data.get('cells', []))
    res_km = data.get('grid_resolution_km')
    r["summary"] = f"Cells: {cells}, Resolution: {res_km} km, Provenance: {data.get('provenance')}"
results.append(r)

# 8. Spatial Grid (NO2)
r, data = test_endpoint("Spatial Grid (NO2)", "GET", "/api/grid?variable=no2&time_step=0")
if data:
    cells = len(data.get('cells', []))
    r["summary"] = f"Cells: {cells}, Provenance: {data.get('provenance')}"
results.append(r)

# 9. Ground Monitoring Stations
r, data = test_endpoint("Ground Monitoring Stations", "GET", "/api/stations")
if data:
    st_count = data.get('count', len(data.get('stations', [])))
    r["summary"] = f"Active stations: {st_count}, Domain: {data.get('domain')}"
results.append(r)

# 10. Live Sync (GET)
r, data = test_endpoint("Live Sync (GET)", "GET", "/api/live/sync")
if data:
    r["summary"] = f"Success: {data.get('success')}, Stations: {data.get('stations_count')}, Fires: {data.get('fires_count')}"
results.append(r)

# 11. Live Sync (POST)
r, data = test_endpoint("Live Sync (POST)", "POST", "/api/live/sync")
if data:
    r["summary"] = f"Success: {data.get('success')}, Stations: {data.get('stations_count')}, Fires: {data.get('fires_count')}"
results.append(r)

# 12. Attribution
r, data = test_endpoint("Source Attribution", "GET", "/api/attribution")
if data:
    rb = data.get('regional_breakdown', {})
    r["summary"] = f"Local: {rb.get('local_percentage')}%, Regional: {rb.get('regional_percentage')}%, Background: {rb.get('background_percentage')}%, Dominant: {data.get('dominant_sector')}"
results.append(r)

# 13. Fire Plume Clock
r, data = test_endpoint("Fire Plume Clock", "GET", "/api/plumes")
if data:
    clusters = data.get('active_fire_clusters_count', 0)
    estimates = len(data.get('plume_estimates', []))
    r["summary"] = f"Active Clusters: {clusters}, Plume Estimates: {estimates}"
results.append(r)

# 14. Explainability (Why AQI Rises)
r, data = test_endpoint("Why AQI Rises Diagnostics", "GET", "/api/explain")
if data:
    drivers = len(data.get('driver_scores', []))
    mode_assoc = data.get('spectral_mode_association', {}).get('mode_name', 'N/A')
    r["summary"] = f"Diagnostic Drivers: {drivers}, Mode Association: {mode_assoc}"
results.append(r)

# 15. Counterfactual POST
cf_payload = {
    "horizon": 24,
    "perturbations": [
        {"sector": "road_transport", "reduction_fraction": 0.40},
        {"sector": "stubble_burning", "reduction_fraction": 0.50}
    ]
}
r, data = test_endpoint("Counterfactual Simulation (POST)", "POST", "/api/counterfactual", json=cf_payload)
if data:
    r["summary"] = f"Baseline PM2.5: {data.get('baseline_pm25', 0):.1f}, Counterfactual: {data.get('counterfactual_pm25', 0):.1f}, Reduction: {data.get('total_pm25_reduction', 0):.1f}"
results.append(r)

# 16. Counterfactual GET
r, data = test_endpoint("Counterfactual Simulation (GET)", "GET", "/api/counterfactual?sector=road_transport&reduction_fraction=0.3&horizon=24")
if data:
    r["summary"] = f"Total PM2.5 reduction: {data.get('total_pm25_reduction', 0):.1f}"
results.append(r)

# 17. MPC POST (LOW_COST)
r, data = test_endpoint("MPC Optimization (LOW_COST)", "POST", "/api/mpc", json={"strategy": "LOW_COST", "horizon": 24})
if data:
    r["summary"] = f"Optim Success: {data.get('optimization_success')}, Mean PM2.5 Red: {data.get('mean_pm25_reduction', 0):.2f}, Cost: {data.get('relative_intervention_cost', 0):.2f}"
results.append(r)

# 18. MPC POST (BALANCED)
r, data = test_endpoint("MPC Optimization (BALANCED)", "POST", "/api/mpc", json={"strategy": "BALANCED", "horizon": 24})
if data:
    r["summary"] = f"Optim Success: {data.get('optimization_success')}, Mean PM2.5 Red: {data.get('mean_pm25_reduction', 0):.2f}, Cost: {data.get('relative_intervention_cost', 0):.2f}"
results.append(r)

# 19. MPC POST (AGGRESSIVE)
r, data = test_endpoint("MPC Optimization (AGGRESSIVE)", "POST", "/api/mpc", json={"strategy": "AGGRESSIVE", "horizon": 24})
if data:
    r["summary"] = f"Optim Success: {data.get('optimization_success')}, Mean PM2.5 Red: {data.get('mean_pm25_reduction', 0):.2f}, Cost: {data.get('relative_intervention_cost', 0):.2f}"
results.append(r)

# 20. MPC POST (Target AQI Infeasible)
r, data = test_endpoint("MPC Target AQI (Infeasible Target)", "POST", "/api/mpc", json={"target_aqi": 40.0, "horizon": 12})
if data:
    r["summary"] = f"Feasibility: {data.get('feasibility_status')}, Msg: {data.get('message')}"
results.append(r)

# 21. MPC GET
r, data = test_endpoint("MPC Policy (GET)", "GET", "/api/mpc?strategy=BALANCED&horizon=24")
if data:
    r["summary"] = f"Strategy: {data.get('strategy')}, Curtailments: {data.get('curtailment_percent')}"
results.append(r)

# 22. Sensitivity
r, data = test_endpoint("Control Sensitivities", "GET", "/api/sensitivity")
if data:
    sens_count = len(data.get('sensitivities', []))
    r["summary"] = f"Sensitivities count: {sens_count}, Method: {data.get('method')}"
results.append(r)

# 23. Spectral Modes
r, data = test_endpoint("Koopman Spectral Modes", "GET", "/api/modes")
if data:
    modes = len(data.get('modes', []))
    r["summary"] = f"Retained Rank: {data.get('retained_rank')}, Modes count: {modes}"
results.append(r)

# 24. Provenance Registry
r, data = test_endpoint("Provenance Registry", "GET", "/api/provenance")
if data:
    reg_count = len(data.get('registry', []))
    r["summary"] = f"Components registered: {reg_count}"
results.append(r)

# 25. Activity & Telemetry
r, data = test_endpoint("Backend Activity & Subsystem Status", "GET", "/api/activity")
if data:
    ev_count = len(data.get('events', []))
    r["summary"] = f"System: {data.get('system_status')}, Events: {ev_count}"
results.append(r)

# 26. Demo Narrative Tour Steps
r, data = test_endpoint("Demo Tour Steps", "GET", "/api/demo/steps")
if data:
    steps_count = len(data.get('steps', []))
    r["summary"] = f"Tour: {data.get('tour_title')}, Steps: {steps_count}"
results.append(r)

print("\n" + "="*80)
print(f"{'ENDPOINT':<35} | {'METHOD':<6} | {'STATUS':<6} | {'LATENCY':<9} | {'RESULT'}")
print("="*80)
all_pass = True
for r in results:
    status_str = f"HTTP {r['status_code']}" if r['status_code'] > 0 else "FAILED"
    res_str = "PASS" if r['success'] else f"FAIL ({r['error']})"
    if not r['success']:
        all_pass = False
    print(f"{r['name']:<35} | {r['method']:<6} | {status_str:<6} | {r['latency_ms']:>6.1f} ms | {res_str}")
    if r['summary']:
        print(f"   --> {r['summary']}")

print("="*80)
print(f"Total endpoints tested: {len(results)}")
print(f"All passed: {all_pass}")

with open("test_api_report.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)

if not all_pass:
    sys.exit(1)
