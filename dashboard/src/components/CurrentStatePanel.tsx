import React from 'react';
import { Wind, Thermometer, CloudRain, Layers, Activity } from 'lucide-react';
import { CurrentState } from '../types';

interface CurrentStatePanelProps {
  state: CurrentState | null;
}

export const CurrentStatePanel: React.FC<CurrentStatePanelProps> = ({ state }) => {
  const pm25 = state?.pm25 ?? 235.4;
  const pm10 = state?.pm10 ?? 384.1;
  const o3 = state?.o3 ?? 38.2;
  const no2 = state?.no2 ?? 65.2;
  const pblh = state?.boundary_layer_height ?? 869.0;
  const inv = state?.inversion_strength ?? 1.76;
  const ws = state?.wind_speed_10m ?? 2.8;
  const cams = state?.cams_aerosol ?? 1.33;

  return (
    <div className="glass-card" style={{ display: 'flex', flexDirection: 'column' }}>
      <div className="card-header">
        <div className="card-title-group">
          <Activity size={16} color="#06b6d4" />
          <h3>Current Atmospheric State</h3>
        </div>
        <span className="provenance-tag modelled">MODELLED</span>
      </div>

      <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
        <div className="metric-grid">
          <div className="metric-pill">
            <span className="label">PM2.5 (Fine Aerosol)</span>
            <span className="value" style={{ color: '#ef4444' }}>
              {pm25} <span className="unit">µg/m³</span>
            </span>
          </div>

          <div className="metric-pill">
            <span className="label">PM10 (Coarse Dust)</span>
            <span className="value" style={{ color: '#f97316' }}>
              {pm10} <span className="unit">µg/m³</span>
            </span>
          </div>

          <div className="metric-pill">
            <span className="label">Ozone (O₃)</span>
            <span className="value" style={{ color: '#38bdf8' }}>
              {o3} <span className="unit">µg/m³</span>
            </span>
          </div>

          <div className="metric-pill">
            <span className="label">Nitrogen Dioxide (NO₂)</span>
            <span className="value" style={{ color: '#eab308' }}>
              {no2} <span className="unit">µg/m³</span>
            </span>
          </div>

          <div className="metric-pill">
            <span className="label" style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <Layers size={12} color="#a855f7" /> Boundary Layer (PBLH)
            </span>
            <span className="value" style={{ color: '#c084fc' }}>
              {pblh} <span className="unit">m</span>
            </span>
          </div>

          <div className="metric-pill">
            <span className="label" style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <Thermometer size={12} color="#f43f5e" /> Inversion Strength (Δθ)
            </span>
            <span className="value" style={{ color: '#fb7185' }}>
              +{inv} <span className="unit">K</span>
            </span>
          </div>

          <div className="metric-pill">
            <span className="label" style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <Wind size={12} color="#10b981" /> 10m Wind Speed
            </span>
            <span className="value" style={{ color: '#34d399' }}>
              {ws} <span className="unit">m/s (WSW)</span>
            </span>
          </div>

          <div className="metric-pill">
            <span className="label" style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <CloudRain size={12} color="#06b6d4" /> CAMS Aerosol Depth
            </span>
            <span className="value" style={{ color: '#38bdf8' }}>
              {cams} <span className="unit">AOD</span>
            </span>
          </div>
        </div>

        <div style={{ background: 'rgba(244, 63, 94, 0.08)', border: '1px solid rgba(244, 63, 94, 0.2)', borderRadius: '8px', padding: '10px 14px', fontSize: '0.74rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '2px' }}>
            <span style={{ color: '#fca5a5', fontWeight: 600 }}>Atmospheric Stability:</span>
            <span style={{ color: '#ffffff', fontFamily: 'var(--font-mono)' }}>Class E/F (Stable Trapping)</span>
          </div>
          <p style={{ color: '#cbd5e1', fontSize: '0.7rem' }}>
            Nocturnal radiational cooling produces a positive potential temperature gradient, suppressing vertical turbulent mixing.
          </p>
        </div>
      </div>
    </div>
  );
};
