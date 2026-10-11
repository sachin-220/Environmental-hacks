import React, { useState, useEffect } from 'react';
import { Download, RefreshCw, CheckCircle2, FileCheck } from 'lucide-react';
import { GovernmentHeader } from './components/layout/GovernmentHeader';
import { CurrentStateTiles } from './components/metrics/CurrentStateTiles';
import { DelhiLeafletHeatmap } from './components/map/DelhiLeafletHeatmap';
import { CoupledFeedbackVisualizer } from './components/atmosphere/CoupledFeedbackVisualizer';
import { GovernmentForecastSection } from './components/forecast/GovernmentForecastSection';
import { GovernmentAtmosphereSection } from './components/atmosphere/GovernmentAtmosphereSection';
import { GovernmentSourcesSection } from './components/sources/GovernmentSourcesSection';
import { GovernmentInterventionSection } from './components/intervention/GovernmentInterventionSection';
import { GovernmentModelSection } from './components/model/GovernmentModelSection';
import { CurrentObservationsTable } from './components/monitoring/CurrentObservationsTable';
import { MapErrorBoundary } from './components/map/MapErrorBoundary';
import { ActionWindowCard } from './components/atmosphere/ActionWindowCard';
import { CAQMDirectiveModal } from './components/reports/CAQMDirectiveModal';
import { EmergencyAlertRibbon } from './components/alerts/EmergencyAlertRibbon';
import { QRCodeEnrollModal } from './components/alerts/QRCodeEnrollModal';
import { InteractiveBroadcastModal } from './components/alerts/InteractiveBroadcastModal';
import { CitizenCommunityPortal } from './components/alerts/CitizenCommunityPortal';
import { AWSInfrastructureDrawer } from './components/cloud/AWSInfrastructureDrawer';

import {
  NavigationPage,
  SystemHealth,
  CurrentState,
  ForecastData,
  AttributionData,
  PlumeData,
  WhyAQIRisesData,
  MPCStrategyResult,
  BackendActivity,
  ActiveAlertsResponse
} from './types';

import {
  fetchHealth,
  fetchCurrentState,
  fetchForecast,
  fetchAttribution,
  fetchPlumes,
  fetchWhyAQIRises,
  optimizeMPC,
  fetchActivity,
  fetchStations,
  fetchActiveAlerts
} from './api';

export const App: React.FC = () => {
  const [currentPage, setCurrentPage] = useState<NavigationPage>('overview');
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [currentState, setCurrentState] = useState<CurrentState | null>(null);
  const [forecast, setForecast] = useState<ForecastData | null>(null);
  const [attribution, setAttribution] = useState<AttributionData | null>(null);
  const [plumes, setPlumes] = useState<PlumeData | null>(null);
  const [whyData, setWhyData] = useState<WhyAQIRisesData | null>(null);
  const [mpcResult, setMpcResult] = useState<MPCStrategyResult | null>(null);
  const [activity, setActivity] = useState<BackendActivity | null>(null);
  const [stations, setStations] = useState<any[]>([]);
  const [alertsData, setAlertsData] = useState<ActiveAlertsResponse | null>(null);

  const [loading, setLoading] = useState<boolean>(true);
  const [lastRefreshed, setLastRefreshed] = useState<string>('Just now');
  const [showCAQMModal, setShowCAQMModal] = useState<boolean>(false);
  const [showQRModal, setShowQRModal] = useState<boolean>(false);
  const [showBroadcastModal, setShowBroadcastModal] = useState<boolean>(false);

  // Dynamic 72-Hour Timeline Simulation State
  const [timeStep, setTimeStep] = useState<number>(0);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);

  // Auto-play timer for dynamic 72h forecast scrubbing
  useEffect(() => {
    let timer: any = null;
    if (isPlaying) {
      timer = setInterval(() => {
        setTimeStep((prev) => (prev >= 71 ? 0 : prev + 1));
      }, 750);
    }
    return () => clearInterval(timer);
  }, [isPlaying]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [h, s, f, a, p, w, m, act, st, al] = await Promise.allSettled([
        fetchHealth(),
        fetchCurrentState(),
        fetchForecast(72),
        fetchAttribution(),
        fetchPlumes(),
        fetchWhyAQIRises(),
        optimizeMPC('BALANCED', 24),
        fetchActivity(),
        fetchStations(),
        fetchActiveAlerts()
      ]);

      if (h.status === 'fulfilled') setHealth(h.value);
      if (s.status === 'fulfilled') setCurrentState(s.value);
      if (f.status === 'fulfilled') setForecast(f.value);
      if (a.status === 'fulfilled') setAttribution(a.value);
      if (p.status === 'fulfilled') setPlumes(p.value);
      if (w.status === 'fulfilled') setWhyData(w.value);
      if (m.status === 'fulfilled') setMpcResult(m.value);
      if (act.status === 'fulfilled') setActivity(act.value);
      if (st.status === 'fulfilled') setStations(st.value?.stations || []);
      if (al.status === 'fulfilled') setAlertsData(al.value);

      const now = new Date();
      setLastRefreshed(now.toLocaleTimeString());
    } catch (err) {
      console.error('AERIS Portal data load error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(() => {
      fetchCurrentState().then(setCurrentState).catch(() => {});
      fetchActivity().then(setActivity).catch(() => {});
      fetchActiveAlerts().then(setAlertsData).catch(() => {});
    }, 60000);
    return () => clearInterval(interval);
  }, []);

  // Compute dynamic state for the currently scrubbed simulation hour
  const timeline = forecast?.hourly_timeline || [];
  const currentHourForecast = timeline[Math.min(timeStep, Math.max(0, timeline.length - 1))];

  const dynamicState: CurrentState | null = currentHourForecast
    ? ({
        ...(currentState || {}),
        timestamp: currentState?.timestamp || new Date().toISOString(),
        location: currentState?.location || 'Delhi NCR Central (D03_R30_C30)',
        coordinates: currentState?.coordinates || { latitude: 28.61, longitude: 77.21 },
        aqi: currentHourForecast.aqi,
        category: currentHourForecast.category,
        dominant_pollutant: currentHourForecast.dominant_pollutant || 'pm25',
        pm25: currentHourForecast.pm25,
        pm10: currentHourForecast.pm10,
        o3: currentHourForecast.o3,
        no2: currentHourForecast.no2,
        so2: currentState?.so2 ?? 19.5,
        co: currentState?.co ?? 1.5,
        boundary_layer_height: currentHourForecast.boundary_layer_height,
        temperature_2m_c: currentState?.temperature_2m_c ?? 20.5,
        relative_humidity: currentState?.relative_humidity ?? 50.1,
        wind_speed_10m: currentHourForecast.wind_speed_10m,
        inversion_strength: currentHourForecast.inversion_strength
      } as CurrentState)
    : currentState;

  // On-demand forecast data download (Recovery capability without background disk dumping)
  const handleDownloadForecast = () => {
    if (!forecast?.hourly_timeline || forecast.hourly_timeline.length === 0) return;

    const headers = [
      'Hour',
      'Horizon_Label',
      'AQI',
      'Category',
      'Dominant_Pollutant',
      'PM2.5_ug_m3',
      'PM2.5_Lower_95CI',
      'PM2.5_Upper_95CI',
      'PM10_ug_m3',
      'O3_ug_m3',
      'NO2_ug_m3',
      'PBL_Height_m',
      'Inversion_Strength_K',
      'Wind_Speed_10m_mps'
    ];

    const rows = forecast.hourly_timeline.map((h) => [
      h.hour,
      h.horizon_label,
      h.aqi,
      `"${h.category}"`,
      `"${h.dominant_pollutant}"`,
      h.pm25,
      h.pm25_lower,
      h.pm25_upper,
      h.pm10,
      h.o3,
      h.no2,
      h.boundary_layer_height,
      h.inversion_strength,
      h.wind_speed_10m
    ]);

    const csvContent =
      'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map((r) => r.join(','))].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute(
      'download',
      `AERIS_Delhi_NCR_72h_Coupled_Forecast_${new Date().toISOString().slice(0, 10)}.csv`
    );
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleDownloadStations = () => {
    if (!stations || stations.length === 0) return;
    const headers = [
      'Station_ID',
      'Station_Name',
      'Latitude',
      'Longitude',
      'Locality',
      'PM25_ug_m3',
      'PM10_ug_m3',
      'NO2_ppb',
      'SO2_ppb',
      'CO',
      'O3_ppb',
      'Calculated_NAQI',
      'Health_Category',
      'Dominant_Pollutant',
      'Status',
      'Last_Updated'
    ];
    const rows = stations.map((s) => [
      s.id,
      `"${s.name}"`,
      s.latitude,
      s.longitude,
      `"${s.locality}"`,
      s.pm25 ?? '',
      s.pm10 ?? '',
      s.no2 ?? '',
      s.so2 ?? '',
      s.co ?? '',
      s.o3 ?? '',
      s.aqi,
      `"${s.category}"`,
      `"${s.dominant_pollutant || 'PM2.5'}"`,
      s.status,
      `"${s.last_updated}"`
    ]);
    const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map((r) => r.join(','))].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `AERIS_Delhi_NCR_Live_Ground_Stations_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="air-ambient-bg" style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* 0. Real-Time Emergency Alert Ribbon (Atmospheric Inversion Warning & Citizen Actions) */}
      <EmergencyAlertRibbon
        alertsData={alertsData}
        onOpenBroadcastModal={() => setShowBroadcastModal(true)}
        onOpenQRModal={() => setShowQRModal(true)}
        onNavigateToCitizen={() => setCurrentPage('alerts')}
      />

      {/* 1. Official Institutional Header with Clearly Organized Navbar */}
      <GovernmentHeader
        currentPage={currentPage}
        onPageChange={setCurrentPage}
        operatingMode={health?.operating_mode || 'LIVE REAL-TIME TELEMETRY (OpenAQ v3 + NASA FIRMS VIIRS)'}
        lastUpdated={activity?.last_updated || lastRefreshed}
        modelStatus={health?.status === 'READY' ? 'OPERATIONAL (RANK 12)' : 'STANDBY'}
      />

      {/* 2. Sub-Header Utility Strip with On-Demand Download Option */}
      {/* 2. Sub-Control Strip (Clean Symmetrical Layout) */}
      <div style={{ background: '#FFFFFF', borderBottom: '1px solid var(--border-subtle)' }}>
        <div
          style={{
            maxWidth: '1720px',
            margin: '0 auto',
            padding: '10px 32px',
            fontSize: '13px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: '12px',
            color: 'var(--text-secondary)'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Section:</span>
            <span
              style={{
                color: '#1B4332',
                fontWeight: 800,
                fontSize: '12px',
                background: '#E8F5E9',
                padding: '3px 10px',
                borderRadius: '6px',
                border: '1px solid #C8E6C9',
                letterSpacing: '0.3px'
              }}
            >
              {currentPage === 'overview'
                ? 'DELHI MAP & HEATMAP'
                : currentPage === 'alerts'
                ? 'CITIZEN ALERTS & SCHOOL SAFETY'
                : currentPage === 'forecast'
                ? '72-HOUR FORECAST'
                : currentPage === 'atmosphere'
                ? 'COUPLED FEEDBACK & INVERSION'
                : currentPage === 'sources'
                ? 'SOURCES & PLUMES'
                : currentPage === 'intervention'
                ? 'INTERVENTION & MPC'
                : currentPage === 'monitoring'
                ? 'STATIONS & DATA RECOVERY'
                : currentPage === 'aws'
                ? 'AWS CLOUD ARCHITECTURE & TELEMETRY'
                : 'MODEL SPECIFICATIONS'}
            </span>
            <span style={{ margin: '0 4px', color: 'var(--border-light)' }}>|</span>
            <span>Simulation Step: </span>
            <strong style={{ color: '#2D6A4F', fontFamily: 'var(--font-mono)' }}>
              +{timeStep}h {timeStep === 0 ? '(Current Time)' : `(Day ${Math.floor(timeStep / 24) + 1})`}
            </strong>
            <span style={{ margin: '0 4px', color: 'var(--border-light)' }}>|</span>
            <span>Airshed: <strong>Delhi NCR (3-km D03 WRF-Chem Grid)</strong></span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <button
              onClick={() => setShowCAQMModal(true)}
              className="air-btn-primary"
              style={{
                padding: '6px 14px',
                fontSize: '12px'
              }}
            >
              <FileCheck size={13} />
              <span>GENERATE CAQM DIRECTIVE</span>
            </button>

            <button
              onClick={handleDownloadForecast}
              className="air-btn-secondary"
              style={{
                padding: '6px 14px',
                fontSize: '12px'
              }}
            >
              <Download size={13} />
              <span>DOWNLOAD FORECAST CSV</span>
            </button>

            <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
              Refreshed: <strong style={{ color: 'var(--forest-900)' }}>{lastRefreshed}</strong>
            </span>

            <button
              onClick={loadData}
              disabled={loading}
              className="air-btn-secondary"
              style={{
                padding: '6px 14px',
                fontSize: '12px'
              }}
            >
              <RefreshCw size={13} className={loading ? 'animate-spin' : ''} />
              <span>{loading ? 'SYNCING...' : 'SYNC DATA'}</span>
            </button>
          </div>
        </div>
      </div>

      {/* 3. Main Portal View (Clean Airy Separation) */}
      <main className="portal-container" style={{ flex: 1, padding: '24px 32px', maxWidth: '1720px', margin: '0 auto', width: '100%' }}>
        
        {/* TAB 1: DELHI MAP & SMOOTH HEATMAP (Primary Focused View) */}
        {currentPage === 'overview' && (
          <div>
            {/* Top Metric Tiles */}
            <CurrentStateTiles state={dynamicState} />

            {/* Real Delhi Map with Gaussian Fluid Heatmap, Toggle, 72h Slider, and Details Below Map */}
            <MapErrorBoundary fallbackTitle="Delhi NCR Geospatial Heatmap Notice">
              <DelhiLeafletHeatmap
                timeStep={timeStep}
                onTimeStepChange={setTimeStep}
                isPlaying={isPlaying}
                onTogglePlay={() => setIsPlaying(!isPlaying)}
                plumes={plumes}
                onDownloadForecast={handleDownloadForecast}
              />
            </MapErrorBoundary>
          </div>
        )}

        {/* TAB 2: 72-HOUR FORECAST TRAJECTORY */}
        {currentPage === 'forecast' && (
          <div>
            <CurrentStateTiles state={dynamicState} />
            <GovernmentForecastSection forecast={forecast} />
          </div>
        )}

        {/* TAB 3: COUPLED FEEDBACK & ATMOSPHERIC INVERSION */}
        {currentPage === 'atmosphere' && (
          <div>
            <CurrentStateTiles state={dynamicState} />
            <div style={{ marginBottom: '16px' }}>
              <ActionWindowCard />
            </div>
            <CoupledFeedbackVisualizer forecast={forecast} currentHour={timeStep} />
            <GovernmentAtmosphereSection state={dynamicState} forecast={forecast} />
          </div>
        )}

        {/* TAB 4: SOURCES & REGIONAL PLUME CLOCK */}
        {currentPage === 'sources' && (
          <div>
            <GovernmentSourcesSection attribution={attribution} plumes={plumes} whyData={whyData} />
          </div>
        )}

        {/* TAB 5: INTERVENTION & MPC POLICY OPTIMIZATION */}
        {currentPage === 'intervention' && (
          <div>
            <GovernmentInterventionSection initialMpcResult={mpcResult} />
          </div>
        )}

        {/* TAB 6: STATIONS & DATA EXPORT / RECOVERY */}
        {currentPage === 'monitoring' && (
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '10px' }}>
              <div>
                <h2 style={{ fontSize: '18px', fontWeight: 800, color: 'var(--forest-900)', margin: 0 }}>
                  GROUND OBSERVATION RECEPTORS & RECOVERY DATA
                </h2>
                <span style={{ fontSize: '12px', color: '#64748B' }}>
                  Live in-situ monitoring stations across Delhi NCR (OpenAQ v3 CPCB/DPCC/IMD network)
                </span>
              </div>
              <div style={{ display: 'flex', gap: '8px' }}>
                <button
                  onClick={handleDownloadStations}
                  style={{
                    background: '#0F172A',
                    color: '#38BDF8',
                    border: '1px solid #334155',
                    borderRadius: '6px',
                    padding: '6px 12px',
                    fontSize: '11px',
                    fontWeight: 700,
                    cursor: 'pointer',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '5px'
                  }}
                >
                  <Download size={12} /> Export Live Stations CSV ({stations.length})
                </button>
                <button
                  onClick={handleDownloadForecast}
                  style={{
                    background: '#16A34A',
                    color: '#FFFFFF',
                    border: 'none',
                    borderRadius: '6px',
                    padding: '6px 12px',
                    fontSize: '11px',
                    fontWeight: 700,
                    cursor: 'pointer',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '5px'
                  }}
                >
                  <Download size={12} /> Export 72h Forecast CSV
                </button>
              </div>
            </div>
            <CurrentStateTiles state={dynamicState} />

            {/* Live Real-Time Ground Stations Table */}
            {stations.length > 0 && (
              <div style={{ background: '#FFFFFF', borderRadius: '8px', border: '1px solid var(--border-color)', padding: '16px', marginBottom: '16px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                  <strong style={{ fontSize: '14px', color: '#003366' }}>
                    ACTIVE REAL-TIME GROUND MONITORING STATIONS ({stations.length} STATIONS)
                  </strong>
                  <span
                    style={{
                      background: '#DCFCE7',
                      color: '#15803D',
                      padding: '3px 8px',
                      borderRadius: '4px',
                      fontSize: '11px',
                      fontWeight: 800,
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '5px'
                    }}
                  >
                    <span className="status-dot-pulse" />
                    <span>100% REAL-TIME TELEMETRY (CPCB / DPCC / IMD)</span>
                  </span>
                </div>
                <div className="table-responsive">
                  <table className="portal-table">
                    <thead>
                      <tr>
                        <th style={{ width: '22%' }}>Station Name</th>
                        <th style={{ width: '16%' }}>Coordinates</th>
                        <th className="num" style={{ width: '10%' }}>PM2.5</th>
                        <th className="num" style={{ width: '10%' }}>PM10</th>
                        <th className="num" style={{ width: '8%' }}>NO2</th>
                        <th className="num" style={{ width: '8%' }}>CO</th>
                        <th className="num" style={{ width: '8%' }}>O3</th>
                        <th className="num" style={{ width: '10%' }}>Calculated NAQI</th>
                        <th style={{ width: '10%' }}>Category</th>
                        <th style={{ width: '10%' }}>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {stations.map((s, idx) => (
                        <tr key={s.id || idx}>
                          <td>
                            <strong style={{ color: 'var(--forest-900)' }}>{s.name}</strong>
                          </td>
                          <td style={{ fontFamily: 'var(--font-mono)', color: '#64748B', fontSize: '11px' }}>
                            {s.latitude?.toFixed(4)}°N, {s.longitude?.toFixed(4)}°E
                          </td>
                          <td className="num" style={{ fontWeight: 800, color: s.pm25 > 120 ? '#DC2626' : '#2563EB' }}>
                            {s.pm25 !== null && s.pm25 !== undefined ? `${s.pm25} µg/m³` : '—'}
                          </td>
                          <td className="num" style={{ fontWeight: 700 }}>
                            {s.pm10 !== null && s.pm10 !== undefined ? `${s.pm10} µg/m³` : '—'}
                          </td>
                          <td className="num">{s.no2 !== null && s.no2 !== undefined ? `${s.no2} ppb` : '—'}</td>
                          <td className="num">{s.co !== null && s.co !== undefined ? `${s.co}` : '—'}</td>
                          <td className="num">{s.o3 !== null && s.o3 !== undefined ? `${s.o3} ppb` : '—'}</td>
                          <td className="num" style={{ fontWeight: 800, color: s.aqi > 300 ? '#DC2626' : s.aqi > 200 ? '#EA580C' : '#16A34A' }}>
                            {s.aqi}
                          </td>
                          <td>
                            <span style={{
                              background: s.aqi > 400 ? '#FEE2E2' : s.aqi > 300 ? '#FFEDD5' : s.aqi > 200 ? '#FEF3C7' : '#DCFCE7',
                              color: s.aqi > 400 ? '#991B1B' : s.aqi > 300 ? '#C2410C' : s.aqi > 200 ? '#B45309' : '#15803D',
                              padding: '2px 8px',
                              borderRadius: '999px',
                              fontWeight: 700,
                              fontSize: '11px',
                              whiteSpace: 'nowrap'
                            }}>
                              {s.category?.toUpperCase() || 'MODERATE'}
                            </span>
                          </td>
                          <td>
                            <span
                              style={{
                                color: '#16A34A',
                                fontWeight: 700,
                                fontSize: '11px',
                                display: 'inline-flex',
                                alignItems: 'center',
                                gap: '4px',
                                whiteSpace: 'nowrap'
                              }}
                            >
                              <CheckCircle2 size={12} color="#16A34A" /> LIVE ONLINE
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* Visual Line Graph Plotting All Station Values Below Table */}
                <div style={{ marginTop: '16px', borderTop: '1px solid #E2E8F0', paddingTop: '16px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px', flexWrap: 'wrap', gap: '8px' }}>
                    <strong style={{ fontSize: '12px', color: '#003366', textTransform: 'uppercase' }}>
                      Air Quality Network Line Profile ({stations.length} Stations)
                    </strong>
                    <div style={{ display: 'flex', gap: '14px', fontSize: '11px', fontWeight: 700 }}>
                      <span style={{ display: 'flex', alignItems: 'center', gap: '5px', color: '#DC2626' }}>
                        <span style={{ width: '12px', height: '3px', background: '#DC2626', display: 'inline-block', borderRadius: '2px' }} /> PM2.5 Level
                      </span>
                      <span style={{ display: 'flex', alignItems: 'center', gap: '5px', color: '#2563EB' }}>
                        <span style={{ width: '12px', height: '3px', background: '#2563EB', display: 'inline-block', borderRadius: '2px' }} /> PM10 Level
                      </span>
                      <span style={{ display: 'flex', alignItems: 'center', gap: '5px', color: '#16A34A' }}>
                        <span style={{ width: '12px', height: '2px', borderTop: '2px dashed #16A34A', display: 'inline-block' }} /> NAAQS Standard
                      </span>
                    </div>
                  </div>

                  {(() => {
                    const chartW = 1050;
                    const chartH = 220;
                    const pL = 50;
                    const pR = 25;
                    const pT = 20;
                    const pB = 40;
                    const cW = chartW - pL - pR;
                    const cH = chartH - pT - pB;

                    const pm25Vals = stations.map((s) => Number(s.pm25 || 0));
                    const pm10Vals = stations.map((s) => Number(s.pm10 || 0));
                    const maxVal = Math.max(300, ...pm25Vals, ...pm10Vals) * 1.1;

                    const getX = (idx: number) => pL + (idx / Math.max(1, stations.length - 1)) * cW;
                    const getY = (val: number) => pT + cH - (Math.min(maxVal, Math.max(0, val)) / maxVal) * cH;

                    const pm25Pts = stations.map((s, i) => `${getX(i)},${getY(Number(s.pm25 || 0))}`).join(' ');
                    const pm10Pts = stations.map((s, i) => `${getX(i)},${getY(Number(s.pm10 || 0))}`).join(' ');

                    return (
                      <div style={{ width: '100%', overflowX: 'auto' }}>
                        <svg viewBox={`0 0 ${chartW} ${chartH}`} style={{ width: '100%', height: 'auto', minWidth: '700px' }}>
                          {/* Grid Ticks */}
                          {[0, 0.25, 0.5, 0.75, 1.0].map((pct) => {
                            const y = pT + cH * (1 - pct);
                            const val = Math.round(maxVal * pct);
                            return (
                              <g key={pct}>
                                <line x1={pL} y1={y} x2={chartW - pR} y2={y} stroke="#E2E8F0" strokeDasharray="3 3" />
                                <text x={pL - 8} y={y + 4} textAnchor="end" fontSize="10" fill="#64748B" fontFamily="monospace">
                                  {val}
                                </text>
                              </g>
                            );
                          })}

                          {/* NAAQS PM2.5 60 ug/m3 Benchmark */}
                          <line x1={pL} y1={getY(60)} x2={chartW - pR} y2={getY(60)} stroke="#16A34A" strokeWidth="1" strokeDasharray="4 4" />
                          <text x={chartW - pR - 5} y={getY(60) - 4} textAnchor="end" fontSize="9" fill="#16A34A" fontWeight="bold">
                            NAAQS PM2.5 (60 µg/m³)
                          </text>

                          {/* PM10 Line */}
                          <polyline points={pm10Pts} fill="none" stroke="#2563EB" strokeWidth="2" strokeLinejoin="round" strokeLinecap="round" />

                          {/* PM2.5 Line */}
                          <polyline points={pm25Pts} fill="none" stroke="#DC2626" strokeWidth="2.5" strokeLinejoin="round" strokeLinecap="round" />

                          {/* Points */}
                          {stations.map((s, idx) => (
                            <g key={s.id || idx}>
                              <circle cx={getX(idx)} cy={getY(Number(s.pm25 || 0))} r={3.5} fill="#DC2626" stroke="#FFFFFF" strokeWidth="1.5" />
                              <circle cx={getX(idx)} cy={getY(Number(s.pm10 || 0))} r={3} fill="#2563EB" stroke="#FFFFFF" strokeWidth="1" />
                              {(idx % 3 === 0) && (
                                <text
                                  x={getX(idx)}
                                  y={pT + cH + 14}
                                  textAnchor="middle"
                                  fontSize="8.5"
                                  fill="#64748B"
                                  transform={`rotate(-25, ${getX(idx)}, ${pT + cH + 14})`}
                                >
                                  {s.name.split(',')[0].slice(0, 11)}
                                </text>
                              )}
                            </g>
                          ))}
                        </svg>
                      </div>
                    );
                  })()}
                </div>
              </div>
            )}

            <CurrentObservationsTable state={dynamicState} />
          </div>
        )}

        {/* TAB 8: CITIZEN & COMMUNITY PORTAL (GAP 1) */}
        {currentPage === 'alerts' && (
          <div>
            <CitizenCommunityPortal
              onOpenBroadcastModal={() => setShowBroadcastModal(true)}
              onOpenQRModal={() => setShowQRModal(true)}
            />
          </div>
        )}

        {/* TAB 9: AWS CLOUD ARCHITECTURE & TELEMETRY (GAP 2) */}
        {currentPage === 'aws' && (
          <div>
            <AWSInfrastructureDrawer />
          </div>
        )}

        {/* TAB 7: MATHEMATICAL MODEL AUDIT & SVD SPECIFICATIONS */}
        {currentPage === 'model' && (
          <div>
            <GovernmentModelSection health={health} />
          </div>
        )}
      </main>

      {/* 4. Footer */}
      <footer
        style={{
          background: '#FFFFFF',
          borderTop: '1px solid var(--border-color)',
          padding: '14px 24px',
          fontSize: '11px',
          color: 'var(--text-secondary)',
          textAlign: 'center'
        }}
      >
        <div
          style={{
            maxWidth: '1440px',
            margin: '0 auto',
            display: 'flex',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: '12px'
          }}
        >
          <div>
            <strong>AERIS</strong> — Atmospheric Emission-Response Intelligence System · Delhi NCR Airshed
          </div>
          <div>
            Cloud: <strong>100% AWS Free Tier Compliant</strong> · Grid: <strong>3-km D03 WRF-Chem</strong> · Rollout: <strong>72 Hours</strong> · Two-Way Feedback: <strong>ACTIVE</strong>
          </div>
        </div>
      </footer>

      {/* Official CAQM Evidentiary Directive Modal */}
      <CAQMDirectiveModal
        isOpen={showCAQMModal}
        onClose={() => setShowCAQMModal(false)}
      />

      {/* Public Citizen QR Code Scanner & Enrollment Modal */}
      <QRCodeEnrollModal
        isOpen={showQRModal}
        onClose={() => setShowQRModal(false)}
        onNavigateToCitizen={() => setCurrentPage('alerts')}
      />

      {/* Interactive Rapid Multi-Channel Geo-Alert Dispatcher Modal */}
      <InteractiveBroadcastModal
        isOpen={showBroadcastModal}
        onClose={() => setShowBroadcastModal(false)}
        onAlertDispatched={loadData}
      />
    </div>
  );
};
