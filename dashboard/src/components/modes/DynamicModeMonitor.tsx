import React, { useState } from 'react';
import { Cpu, ChevronDown, ChevronUp } from 'lucide-react';

export const DynamicModeMonitor: React.FC = () => {
  const [expanded, setExpanded] = useState<boolean>(false);

  const keyModes = [
    {
      name: 'Inversion-associated',
      status: 'Oscillatory',
      period: '6.92 h',
      color: '#EA580C',
      eigenvalue: '0.982 ± 0.165j',
      dominant: 'inversion_strength (+0.84), pblh (-0.78)'
    },
    {
      name: 'Ventilation-associated',
      status: 'Stable / Decaying',
      period: 'Non-oscillatory',
      color: '#2563EB',
      eigenvalue: '0.842',
      dominant: 'wind_speed_10m (+0.79), u_wind (+0.65)'
    },
    {
      name: 'Persistent Stagnation',
      status: 'Stable Equilibrium',
      period: 'Infinite (DC mode)',
      color: '#16A34A',
      eigenvalue: '1.000',
      dominant: 'pm25 (+0.72), pm10 (+0.68)'
    }
  ];

  return (
    <div className="white-card" style={{ padding: '18px 20px', display: 'flex', flexDirection: 'column' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Cpu size={16} color="#2563EB" />
          <h3 style={{ fontSize: '0.88rem', fontWeight: 600 }}>DYNAMIC MODES</h3>
        </div>
        <span className="provenance-tag modelled">MODELLED</span>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {keyModes.map((m, idx) => (
          <div
            key={idx}
            style={{
              background: 'var(--bg-secondary)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-sm)',
              padding: '10px 12px',
              display: 'flex',
              flexDirection: 'column',
              gap: '4px'
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span className="status-dot" style={{ backgroundColor: m.color }} />
                <span style={{ fontSize: '0.78rem', fontWeight: 600, color: '#1E293B' }}>{m.name}</span>
              </div>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.7rem', color: '#64748B' }}>
                {m.status} {m.period !== 'Non-oscillatory' && m.period !== 'Infinite (DC mode)' ? `• ${m.period}` : ''}
              </span>
            </div>

            {expanded && (
              <div style={{ marginTop: '4px', paddingTop: '6px', borderTop: '1px dashed var(--border-subtle)', fontFamily: 'var(--font-mono)', fontSize: '0.68rem', color: '#475569', display: 'flex', flexDirection: 'column', gap: '2px' }}>
                <div>Eigenvalue λ: <strong>{m.eigenvalue}</strong></div>
                <div>Dominant Loadings: <span>{m.dominant}</span></div>
              </div>
            )}
          </div>
        ))}
      </div>

      <button
        onClick={() => setExpanded(!expanded)}
        style={{
          background: 'transparent',
          border: 'none',
          color: '#2563EB',
          fontSize: '0.72rem',
          fontWeight: 600,
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          gap: '4px',
          marginTop: '10px',
          alignSelf: 'flex-start'
        }}
      >
        <span>{expanded ? 'Hide Technical Parameters' : 'Show Mathematical Mode Loadings'}</span>
        {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
      </button>
    </div>
  );
};
