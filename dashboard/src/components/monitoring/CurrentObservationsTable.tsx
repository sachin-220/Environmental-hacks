import React from 'react';
import { CurrentState } from '../../types';

interface CurrentObservationsTableProps {
  state: CurrentState | null;
}

export const CurrentObservationsTable: React.FC<CurrentObservationsTableProps> = ({ state }) => {
  if (!state) {
    return (
      <div className="portal-section">
        <div style={{ padding: '20px', textAlign: 'center', color: 'var(--text-muted)' }}>
          Loading current atmospheric and air quality observations...
        </div>
      </div>
    );
  }

  const getAqiClass = (cat: string) => {
    const c = cat.toLowerCase();
    if (c.includes('good')) return 'status-good';
    if (c.includes('satisfactory')) return 'status-satisfactory';
    if (c.includes('moderate')) return 'status-moderate';
    if (c.includes('very poor')) return 'status-very-poor';
    if (c.includes('poor')) return 'status-poor';
    return 'status-severe';
  };

  const aqiClass = getAqiClass(state.aqi_category || 'Severe');

  // Wind direction calculation from U and V components
  const windDirDeg = Math.round((Math.atan2(-state.u_wind_10m, -state.v_wind_10m) * 180 / Math.PI + 360) % 360);
  const getWindCardinal = (deg: number) => {
    const directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW'];
    return directions[Math.round(deg / 22.5) % 16];
  };

  return (
    <div className="portal-section">
      <div className="portal-section-title">
        <span>CURRENT AIR QUALITY OBSERVATIONS — DELHI NCR AIRSHED</span>
        <span className="portal-section-subtitle">Station: Central Delhi Baseline (28.61N, 77.21E)</span>
      </div>

      {/* Primary AQI Indicator Card & Meta */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'auto 1fr',
          gap: '24px',
          padding: '16px',
          background: '#F8F9FA',
          border: '1px solid var(--border-color)',
          marginBottom: '16px',
          alignItems: 'center'
        }}
      >
        {/* Large Primary AQI Display */}
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '12px 28px',
            background: '#FFFFFF',
            border: '2px solid var(--border-color)',
            minWidth: '170px'
          }}
        >
          <span style={{ fontSize: '11px', fontWeight: 'bold', color: 'var(--text-secondary)' }}>
            NATIONAL AQI (CPCB)
          </span>
          <span style={{ fontSize: '42px', fontWeight: 'bold', color: '#202122', lineHeight: 1.1 }}>
            {state.aqi}
          </span>
          <span className={`status-tag ${aqiClass}`} style={{ marginTop: '4px', fontSize: '12px' }}>
            {(state.category || state.aqi_category || 'Severe').toUpperCase()}
          </span>
        </div>

        {/* Observation Summary Metrics */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '12px' }}>
          <div>
            <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>Dominant Pollutant</div>
            <div style={{ fontSize: '16px', fontWeight: 'bold', color: '#003366' }}>{state.dominant_pollutant}</div>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>CPCB Standard Sub-Index</div>
          </div>
          <div>
            <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>Observation Timestamp</div>
            <div style={{ fontSize: '13px', fontWeight: 'bold', color: '#202122' }}>{state.timestamp}</div>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Hourly Validated Cycle</div>
          </div>
          <div>
            <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>Atmospheric Ventilation</div>
            <div style={{ fontSize: '14px', fontWeight: 'bold', color: state.inversion_strength > 1.0 ? '#DC2626' : '#16A34A' }}>
              {state.inversion_strength > 1.0 ? 'CRITICAL TRAPPING' : 'NORMAL DISPERSION'}
            </div>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>PBL: {state.boundary_layer_height.toFixed(0)} m · Inversion: +{state.inversion_strength.toFixed(2)} K</div>
          </div>
          <div>
            <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>Data Provenance</div>
            <div><span className="prov-badge observed">OBSERVED / REANALYSIS</span></div>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '2px' }}>CPCB Ground + ERA5 Surface</div>
          </div>
        </div>
      </div>

      {/* Structured Government Observation Table */}
      <div className="table-responsive">
        <table className="portal-table">
          <thead>
            <tr>
              <th style={{ width: '22%' }}>Parameter</th>
              <th className="num" style={{ width: '15%' }}>Current Value</th>
              <th style={{ width: '12%' }}>Unit</th>
              <th style={{ width: '18%' }}>Air Quality Status</th>
              <th style={{ width: '18%' }}>Provenance</th>
              <th style={{ width: '15%' }}>Reference Timestamp</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><strong>CPCB Air Quality Index (AQI)</strong></td>
              <td className="num"><strong>{state.aqi}</strong></td>
              <td>Index (0–500)</td>
              <td><span className={`status-tag ${aqiClass}`}>{state.category || state.aqi_category || 'Severe'}</span></td>
              <td><span className="prov-badge observed">OBSERVED</span></td>
              <td>{state.timestamp}</td>
            </tr>
            <tr>
              <td>Particulate Matter (PM2.5)</td>
              <td className="num">{state.pm25.toFixed(1)}</td>
              <td>µg/m³</td>
              <td><span className="status-tag status-severe">Severe ({state.pm25 > 120 ? 'Above Standard' : 'Normal'})</span></td>
              <td><span className="prov-badge observed">OBSERVED</span></td>
              <td>{state.timestamp}</td>
            </tr>
            <tr>
              <td>Particulate Matter (PM10)</td>
              <td className="num">{state.pm10.toFixed(1)}</td>
              <td>µg/m³</td>
              <td><span className="status-tag status-very-poor">Very Poor</span></td>
              <td><span className="prov-badge observed">OBSERVED</span></td>
              <td>{state.timestamp}</td>
            </tr>
            <tr>
              <td>Ozone (O3)</td>
              <td className="num">{state.o3.toFixed(1)}</td>
              <td>ppb</td>
              <td><span className="status-tag status-good">Good</span></td>
              <td><span className="prov-badge observed">OBSERVED</span></td>
              <td>{state.timestamp}</td>
            </tr>
            <tr>
              <td>Nitrogen Oxides (NOx / NO2)</td>
              <td className="num">{state.no2.toFixed(1)}</td>
              <td>ppb</td>
              <td><span className="status-tag status-moderate">Moderate</span></td>
              <td><span className="prov-badge observed">OBSERVED</span></td>
              <td>{state.timestamp}</td>
            </tr>
            <tr>
              <td>Air Temperature (2m)</td>
              <td className="num">{state.temperature_2m_c.toFixed(1)}</td>
              <td>°C</td>
              <td>Normal Lapse Rate Baseline</td>
              <td><span className="prov-badge observed">ERA5 REANALYSIS</span></td>
              <td>{state.timestamp}</td>
            </tr>
            <tr>
              <td>Planetary Boundary Layer Height (PBLH)</td>
              <td className="num">{state.boundary_layer_height.toFixed(0)}</td>
              <td>m</td>
              <td><strong style={{ color: '#DC2626' }}>Compressed Shallow Boundary Layer</strong></td>
              <td><span className="prov-badge modelled">WRF-CHEM COUPLED</span></td>
              <td>{state.timestamp}</td>
            </tr>
            <tr>
              <td>Surface Wind Speed (10m)</td>
              <td className="num">{state.wind_speed_10m.toFixed(1)}</td>
              <td>m/s</td>
              <td>Stagnant / Weak Dispersion (&lt; 2.5 m/s)</td>
              <td><span className="prov-badge observed">ERA5 REANALYSIS</span></td>
              <td>{state.timestamp}</td>
            </tr>
            <tr>
              <td>Wind Direction</td>
              <td className="num">{windDirDeg}° ({getWindCardinal(windDirDeg)})</td>
              <td>Degrees</td>
              <td>North-West Inflow (Upwind Transport Alignment)</td>
              <td><span className="prov-badge observed">ERA5 REANALYSIS</span></td>
              <td>{state.timestamp}</td>
            </tr>
            <tr>
              <td>Thermal Inversion Strength (dTheta/dz)</td>
              <td className="num">+{state.inversion_strength.toFixed(2)}</td>
              <td>K / 100m</td>
              <td><strong style={{ color: '#DC2626' }}>Strong Capping Lid Present</strong></td>
              <td><span className="prov-badge modelled">HYPSOMETRIC DIAGNOSTIC</span></td>
              <td>{state.timestamp}</td>
            </tr>
          </tbody>
        </table>
      </div>

      {/* Visual Parameter Benchmark Chart (Plotted Below Table) */}
      <div style={{ marginTop: '16px', background: '#F8FAFC', border: '1px solid #E2E8F0', borderRadius: '8px', padding: '14px 16px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
          <strong style={{ fontSize: '12px', color: 'var(--forest-900)', textTransform: 'uppercase' }}>
            Observed In-Situ Pollutants vs NAAQS Regulatory Limits
          </strong>
            <span style={{ fontSize: '10px', color: '#64748B' }}>
              Standard: 24-Hour Average CPCB Thresholds
            </span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '14px' }}>
            {[
              { name: 'PM2.5 Aerosol', obs: state.pm25, limit: 60, unit: 'µg/m³', color: state.pm25 > 60 ? '#DC2626' : '#16A34A' },
              { name: 'PM10 Respirable', obs: state.pm10, limit: 100, unit: 'µg/m³', color: state.pm10 > 100 ? '#DC2626' : '#16A34A' },
              { name: 'NO2 Precursor', obs: state.no2, limit: 80, unit: 'µg/m³', color: state.no2 > 80 ? '#EA580C' : '#16A34A' },
              { name: 'Ozone (O3)', obs: state.o3, limit: 100, unit: 'µg/m³', color: state.o3 > 100 ? '#EA580C' : '#16A34A' },
              { name: 'Carbon Monoxide', obs: state.co, limit: 2.0, unit: 'mg/m³', color: state.co > 2.0 ? '#DC2626' : '#16A34A' },
              { name: 'Sulfur Dioxide (SO2)', obs: state.so2, limit: 80, unit: 'µg/m³', color: state.so2 > 80 ? '#DC2626' : '#16A34A' }
            ].map((p) => {
              const maxScale = Math.max(p.limit * 2, p.obs * 1.25);
              const obsPct = Math.min(100, Math.round((p.obs / maxScale) * 100));
              const limitPct = Math.min(100, Math.round((p.limit / maxScale) * 100));
              return (
                <div key={p.name} style={{ background: '#FFFFFF', border: '1px solid #E2E8F0', borderRadius: '4px', padding: '8px 10px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', marginBottom: '4px' }}>
                    <span style={{ fontWeight: 700, color: '#0F172A' }}>{p.name}</span>
                    <span style={{ fontWeight: 800, color: p.color, fontFamily: 'monospace' }}>
                      {p.obs.toFixed(1)} {p.unit}
                    </span>
                  </div>
                  <div style={{ position: 'relative', height: '8px', background: '#E2E8F0', borderRadius: '4px', overflow: 'hidden' }}>
                    <div style={{ width: `${obsPct}%`, height: '100%', background: p.color, borderRadius: '4px' }} />
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '9px', color: '#64748B', marginTop: '3px' }}>
                    <span>0</span>
                    <span style={{ color: '#16A34A', fontWeight: 'bold' }}>Limit: {p.limit}</span>
                    <span>{Math.round(maxScale)}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
  );
};
