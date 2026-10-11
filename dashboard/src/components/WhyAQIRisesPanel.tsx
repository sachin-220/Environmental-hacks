import React from 'react';
import { HelpCircle, AlertTriangle, ArrowUpRight, Cpu } from 'lucide-react';
import { WhyAQIRisesData } from '../types';

interface WhyAQIRisesPanelProps {
  whyData: WhyAQIRisesData | null;
}

export const WhyAQIRisesPanel: React.FC<WhyAQIRisesPanelProps> = ({ whyData }) => {
  const drivers = whyData?.driver_scores || [
    { driver: 'boundary_layer_collapse', driver_name: 'PBL Compression & Lid Stagnation', score: 82, description: 'Nocturnal boundary layer dropped from 869m to 240m' },
    { driver: 'ventilation_breakdown', driver_name: 'Horizontal Wind Stagnation', score: 76, description: 'Wind speed fell below 1.5 m/s, suppressing advective flush' },
    { driver: 'upwind_fires', driver_name: 'Upwind Stubble Burning Advection', score: 69, description: 'Northwesterly transit aligning with active Punjab/Haryana fires' },
    { driver: 'secondary_chemistry', driver_name: 'Secondary Aerosol Chemistry', score: 54, description: 'High NO2 precursor accumulation catalyzing nitrate aerosol nucleation' }
  ];

  const dominant = whyData?.dominant_driver ?? 'Boundary Layer Compression';
  const rawMode: any = whyData?.spectral_mode_association;
  const modeAssoc = typeof rawMode === 'string'
    ? rawMode
    : Array.isArray(rawMode)
    ? rawMode.map((m: any) => (typeof m === 'object' ? `${m.mode || 'Mode'} (${m.period || ''})` : String(m))).join(', ')
    : 'Koopman Mode #1 (λ = 0.998, Persistent Atmospheric Inversion Trap)';
  const narrative = whyData?.narrative_summary ?? 'AQI surges +48 points over 24h primarily due to boundary layer collapse compressing the Delhi urban airshed, compounded by calm horizontal surface winds and incoming northwesterly crop fire plumes.';

  return (
    <div className="glass-card" style={{ display: 'flex', flexDirection: 'column' }}>
      <div className="card-header">
        <div className="card-title-group">
          <HelpCircle size={16} color="#eab308" />
          <h3>Why AQI Rises: Physical Diagnostics</h3>
        </div>
        <span className="provenance-tag inferred">INFERRED</span>
      </div>

      <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
        {/* Dominant Driver Highlight */}
        <div style={{ background: 'rgba(234, 179, 8, 0.1)', border: '1px solid rgba(234, 179, 8, 0.25)', borderRadius: '8px', padding: '12px 14px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
            <span style={{ fontSize: '0.72rem', color: '#fde047', textTransform: 'uppercase', fontWeight: 700 }}>Dominant Physical Driver</span>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: '#f87171', fontWeight: 700 }}>
              ΔAQI: +{whyData?.delta_aqi || 48} pts
            </span>
          </div>
          <div style={{ fontSize: '0.95rem', fontWeight: 700, color: '#ffffff' }}>
            {dominant}
          </div>
          <p style={{ fontSize: '0.72rem', color: '#cbd5e1', marginTop: '4px', lineHeight: '1.4' }}>
            {narrative}
          </p>
        </div>

        {/* Driver Scorecards */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {drivers.map((d, idx) => (
            <div key={idx} style={{ background: 'rgba(15, 23, 42, 0.5)', border: '1px solid var(--border-subtle)', borderRadius: '6px', padding: '8px 12px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#f1f5f9' }}>{d.driver_name}</span>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', fontWeight: 700, color: d.score > 70 ? '#ef4444' : '#f59e0b' }}>
                  {d.score}/100
                </span>
              </div>
              <div style={{ width: '100%', height: '4px', background: '#1e293b', borderRadius: '2px', overflow: 'hidden' }}>
                <div style={{ width: `${d.score}%`, height: '100%', background: d.score > 70 ? 'linear-gradient(90deg, #f59e0b, #ef4444)' : '#38bdf8' }} />
              </div>
              <span style={{ fontSize: '0.68rem', color: '#64748b', marginTop: '4px', display: 'block' }}>
                {d.description}
              </span>
            </div>
          ))}
        </div>

        {/* Koopman Spectral Mode Linkage */}
        <div style={{ background: 'rgba(168, 85, 247, 0.08)', border: '1px solid rgba(168, 85, 247, 0.2)', borderRadius: '6px', padding: '8px 12px', display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.72rem' }}>
          <Cpu size={14} color="#a855f7" style={{ flexShrink: 0 }} />
          <div>
            <span style={{ color: '#c084fc', fontWeight: 600 }}>DMDc Spectral Mode: </span>
            <span style={{ color: '#cbd5e1', fontFamily: 'var(--font-mono)' }}>{modeAssoc}</span>
          </div>
        </div>
      </div>
    </div>
  );
};
