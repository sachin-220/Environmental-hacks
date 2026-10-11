import {
  SystemHealth,
  CurrentState,
  ForecastData,
  SpatialGridData,
  AttributionData,
  PlumeData,
  WhyAQIRisesData,
  MPCStrategyResult,
  DemoStep
} from './types';

const API_BASE = '/api';

export async function fetchHealth(): Promise<SystemHealth> {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error(`Health fetch failed: ${res.statusText}`);
  return res.json();
}

export async function fetchCurrentState(): Promise<CurrentState> {
  const res = await fetch(`${API_BASE}/state`);
  if (!res.ok) throw new Error(`State fetch failed: ${res.statusText}`);
  return res.json();
}

export async function fetchForecast(horizon = 72): Promise<ForecastData> {
  const res = await fetch(`${API_BASE}/forecast?horizon=${horizon}`);
  if (!res.ok) throw new Error(`Forecast fetch failed: ${res.statusText}`);
  return res.json();
}

export async function fetchSpatialGrid(variable = 'pm25', timeStep = 0): Promise<SpatialGridData> {
  const res = await fetch(`${API_BASE}/grid?variable=${variable}&time_step=${timeStep}`);
  if (!res.ok) throw new Error(`Grid fetch failed: ${res.statusText}`);
  return res.json();
}

export async function fetchAttribution(): Promise<AttributionData> {
  const res = await fetch(`${API_BASE}/attribution`);
  if (!res.ok) throw new Error(`Attribution fetch failed: ${res.statusText}`);
  return res.json();
}

export async function fetchPlumes(): Promise<PlumeData> {
  const res = await fetch(`${API_BASE}/plumes`);
  if (!res.ok) throw new Error(`Plumes fetch failed: ${res.statusText}`);
  return res.json();
}

export async function fetchWhyAQIRises(): Promise<WhyAQIRisesData> {
  const res = await fetch(`${API_BASE}/explain`);
  if (!res.ok) throw new Error(`Explain fetch failed: ${res.statusText}`);
  return res.json();
}

export async function fetchSensitivities(): Promise<any> {
  const res = await fetch(`${API_BASE}/sensitivity`);
  if (!res.ok) throw new Error(`Sensitivity fetch failed: ${res.statusText}`);
  return res.json();
}

export async function optimizeMPC(strategy = 'BALANCED', horizon = 24, targetAqi?: number): Promise<MPCStrategyResult> {
  const payload: any = { strategy, horizon };
  if (targetAqi !== undefined && targetAqi !== null) {
    payload.target_aqi = targetAqi;
  }
  const res = await fetch(`${API_BASE}/mpc`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!res.ok) throw new Error(`MPC fetch failed: ${res.statusText}`);
  return res.json();
}

export async function fetchDemoSteps(): Promise<DemoStep[]> {
  const res = await fetch(`${API_BASE}/demo/steps`);
  if (!res.ok) throw new Error(`Demo steps fetch failed: ${res.statusText}`);
  return res.json();
}

export async function fetchActivity(): Promise<any> {
  const res = await fetch(`${API_BASE}/activity`);
  if (!res.ok) throw new Error(`Activity fetch failed: ${res.statusText}`);
  return res.json();
}

export async function fetchModes(): Promise<any> {
  const res = await fetch(`${API_BASE}/modes`);
  if (!res.ok) throw new Error(`Modes fetch failed: ${res.statusText}`);
  return res.json();
}

export async function fetchProvenance(): Promise<any> {
  const res = await fetch(`${API_BASE}/provenance`);
  if (!res.ok) throw new Error(`Provenance fetch failed: ${res.statusText}`);
  return res.json();
}

export async function fetchStations(): Promise<any> {
  const res = await fetch(`${API_BASE}/stations`);
  if (!res.ok) throw new Error(`Stations fetch failed: ${res.statusText}`);
  return res.json();
}

export async function triggerLiveSync(): Promise<any> {
  const res = await fetch(`${API_BASE}/live/sync`, { method: 'POST' });
  if (!res.ok) throw new Error(`Live sync failed: ${res.statusText}`);
  return res.json();
}

export async function fetchActionWindow(): Promise<any> {
  const res = await fetch(`${API_BASE}/action-window`);
  if (!res.ok) throw new Error(`Action window fetch failed: ${res.statusText}`);
  return res.json();
}

export async function fetchAirshedFederalism(): Promise<any> {
  const res = await fetch(`${API_BASE}/federalism`);
  if (!res.ok) throw new Error(`Federalism fetch failed: ${res.statusText}`);
  return res.json();
}

export async function fetchCAQMDirective(): Promise<any> {
  const res = await fetch(`${API_BASE}/reports/caqm-directive`);
  if (!res.ok) throw new Error(`CAQM directive fetch failed: ${res.statusText}`);
  return res.json();
}

export async function fetchActiveAlerts(): Promise<any> {
  const res = await fetch(`${API_BASE}/alerts/active`);
  if (!res.ok) throw new Error(`Alerts fetch failed: ${res.statusText}`);
  return res.json();
}

export async function fetchWards(): Promise<any> {
  const res = await fetch(`${API_BASE}/alerts/wards`);
  if (!res.ok) throw new Error(`Wards fetch failed: ${res.statusText}`);
  return res.json();
}

export async function broadcastAlert(payload: any): Promise<any> {
  const res = await fetch(`${API_BASE}/alerts/broadcast`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!res.ok) throw new Error(`Broadcast alert failed: ${res.statusText}`);
  return res.json();
}

export async function subscribeCitizen(payload: any): Promise<any> {
  const res = await fetch(`${API_BASE}/alerts/subscribe`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!res.ok) throw new Error(`Citizen subscribe failed: ${res.statusText}`);
  return res.json();
}

export async function fetchSchoolSafety(): Promise<any> {
  const res = await fetch(`${API_BASE}/alerts/schools`);
  if (!res.ok) throw new Error(`School safety fetch failed: ${res.statusText}`);
  return res.json();
}

export async function fetchAWSHealth(): Promise<any> {
  const res = await fetch(`${API_BASE}/aws/health`);
  if (!res.ok) throw new Error(`AWS health fetch failed: ${res.statusText}`);
  return res.json();
}

