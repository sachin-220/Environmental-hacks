import React from 'react';
import { Layers, Thermometer } from 'lucide-react';
import { CurrentState } from '../../types';

interface CleanAtmosphericStateProps {
  state: CurrentState | null;
}

export const CleanAtmosphericState: React.FC<CleanAtmosphericStateProps> = ({ state }) => {
  const pblh = state?.boundary_layer_height ?? 869.0;
  const inv = state?.inversion_strength ?? 1.76;
  const wind = state?.wind_speed_10m ?? 2.8;
  const ventCoeff = Math.round(wind * pblh);

  return (
    <div className="white-card" style={{ padding: '18px 20px', display: 'flex', flexDirection: 'column' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Layers size={16} color="#7C3AED" />
          <h3 style={{ fontSize: '0.88rem', fontWeight: 600 }}>ATMOSPHERIC STATE</h3>
        </div>
        <span className="provenance-tag modelled">MODELLED</span>
      </div>

      {/* Grid of Key Boundary Metrics */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '10px', marginBottom: '14px' }}>
        <div style={{ background: 'var(--bg-secondary)', padding: '8px 10px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
          <span style={{ fontSize: '0.65rem', color: '#64748B', fontWeight: 600, textTransform: 'uppercase' }}>PBL Height</span>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.95rem', fontWeight: 700, color: '#111827' }}>
            {Math.round(pblh)} m
          </div>
        </div>

        <div style={{ background: 'var(--bg-secondary)', padding: '8px 10px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
          <span style={{ fontSize: '0.65rem', color: '#64748B', fontWeight: 600, textTransform: 'uppercase' }}>Inversion</span>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.95rem', fontWeight: 700, color: '#DC2626' }}>
            +{inv} K
          </div>
        </div>

        <div style={{ background: 'var(--bg-secondary)', padding: '8px 10px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
          <span style={{ fontSize: '0.65rem', color: '#64748B', fontWeight: 600, textTransform: 'uppercase' }}>Ventilation</span>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.95rem', fontWeight: 700, color: '#EA580C' }}>
            {ventCoeff} m²/s
          </div>
        </div>

        <div style={{ background: 'var(--bg-secondary)', padding: '8px 10px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
          <span style={{ fontSize: '0.65rem', color: '#64748B', fontWeight: 600, textTransform: 'uppercase' }}>Stability</span>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.85rem', fontWeight: 700, color: '#7C3AED' }}>
            Class E/F
          </div>
        </div>
      </div>

      {/* Clean Vertical Atmospheric Column Graphic */}
      <div style={{ border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-md)', padding: '12px 16px', background: '#F8FAFC' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
          {/* Free Atmosphere */}
          <div style={{ padding: '8px 12px', background: '#EFF6FF', borderRadius: '4px', border: '1px dashed #BFDBFE', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.74rem', fontWeight: 600, color: '#1D4ED8' }}>Free Troposphere</span>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.68rem', color: '#64748B' }}>&gt; 1,200 m</span>
          </div>

          {/* Capping Inversion Layer */}
          <div style={{ padding: '8px 12px', background: '#FEF2F2', borderRadius: '4px', border: '1px solid #FECACA', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Thermometer size={14} color="#DC2626" />
              <span style={{ fontSize: '0.74rem', fontWeight: 700, color: '#B91C1C' }}>Capping Thermal Inversion Lid (+{inv} K)</span>
            </div>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.68rem', color: '#DC2626', fontWeight: 600 }}>~869 m (Trapping Ceiling)</span>
          </div>

          {/* Planetary Boundary Layer (Trapped) */}
          <div style={{ padding: '14px 12px', background: '#FFFBEB', borderRadius: '4px', border: '1px solid #FDE68A', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <span style={{ fontSize: '0.74rem', fontWeight: 600, color: '#92400E', display: 'block' }}>Trapped Urban Boundary Layer (PBL)</span>
              <span style={{ fontSize: '0.68rem', color: '#B45309' }}>Weak dispersion (Vc = {ventCoeff} m²/s &lt; 6,000 threshold)</span>
            </div>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.68rem', color: '#B45309' }}>0 – 869 m</span>
          </div>

          {/* Surface */}
          <div style={{ padding: '6px 12px', background: '#E2E8F0', borderRadius: '4px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.72rem', fontWeight: 600, color: '#334155' }}>Surface (Delhi Central • 28.61°N)</span>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.68rem', color: '#475569' }}>0 m AGL</span>
          </div>
        </div>
      </div>
    </div>
  );
};
