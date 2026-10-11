import React from 'react';
import { CloudSun, Layers, Thermometer, Wind } from 'lucide-react';
import { CleanAtmosphericState } from '../components/atmosphere/CleanAtmosphericState';
import { ActionWindowCard } from '../components/atmosphere/ActionWindowCard';
import { CurrentState } from '../types';

interface AtmospherePageProps {
  state: CurrentState | null;
}

export const AtmospherePage: React.FC<AtmospherePageProps> = ({ state }) => {
  const pblh = state?.boundary_layer_height ?? 869.0;
  const inv = state?.inversion_strength ?? 1.76;
  const wind = state?.wind_speed_10m ?? 2.8;
  const tempK = state?.temperature_2m_k ?? 298.15;
  const tempC = state?.temperature_2m_c ?? 25.0;
  const rh = state?.relative_humidity ?? 65.0;
  const psfc = state?.surface_pressure ?? 1012.0;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '22px' }}>
      <div className="white-card" style={{ padding: '20px 24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#111827' }}>ATMOSPHERIC COLUMN & BOUNDARY DYNAMICS</h2>
            <p style={{ fontSize: '0.78rem', color: '#64748B', marginTop: '2px' }}>
              Boundary layer compression, nocturnal radiation inversion, and ventilation breakdown in Delhi NCR
            </p>
          </div>
          <span className="provenance-tag modelled">MODELLED</span>
        </div>
      </div>

      {/* Atmospheric Action Window Countdown */}
      <ActionWindowCard />

      <CleanAtmosphericState state={state} />

      {/* Atmospheric Physics Metrics Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px' }}>
        <div className="white-card" style={{ padding: '16px' }}>
          <span style={{ fontSize: '0.7rem', fontWeight: 600, color: '#64748B', textTransform: 'uppercase' }}>Surface Temperature</span>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: '1.4rem', fontWeight: 700, color: '#111827', marginTop: '4px' }}>
            {tempC}°C <span style={{ fontSize: '0.75rem', fontWeight: 400, color: '#64748B' }}>({tempK} K)</span>
          </div>
          <span style={{ fontSize: '0.68rem', color: '#64748B', marginTop: '4px', display: 'block' }}>2m Air Temperature</span>
        </div>

        <div className="white-card" style={{ padding: '16px' }}>
          <span style={{ fontSize: '0.7rem', fontWeight: 600, color: '#64748B', textTransform: 'uppercase' }}>Relative Humidity</span>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: '1.4rem', fontWeight: 700, color: '#2563EB', marginTop: '4px' }}>
            {rh}%
          </div>
          <span style={{ fontSize: '0.68rem', color: '#64748B', marginTop: '4px', display: 'block' }}>Aerosol Hygroscopic Growth</span>
        </div>

        <div className="white-card" style={{ padding: '16px' }}>
          <span style={{ fontSize: '0.7rem', fontWeight: 600, color: '#64748B', textTransform: 'uppercase' }}>Surface Pressure</span>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: '1.4rem', fontWeight: 700, color: '#111827', marginTop: '4px' }}>
            {psfc} <span style={{ fontSize: '0.75rem', fontWeight: 400, color: '#64748B' }}>hPa</span>
          </div>
          <span style={{ fontSize: '0.68rem', color: '#64748B', marginTop: '4px', display: 'block' }}>High Pressure Ridge</span>
        </div>

        <div className="white-card" style={{ padding: '16px' }}>
          <span style={{ fontSize: '0.7rem', fontWeight: 600, color: '#64748B', textTransform: 'uppercase' }}>Richardson Number</span>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: '1.4rem', fontWeight: 700, color: '#DC2626', marginTop: '4px' }}>
            Ri &gt; 0.25
          </div>
          <span style={{ fontSize: '0.68rem', color: '#DC2626', fontWeight: 600, marginTop: '4px', display: 'block' }}>Laminar Trapped Flow</span>
        </div>
      </div>
    </div>
  );
};
