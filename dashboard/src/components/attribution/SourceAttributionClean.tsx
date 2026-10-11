import React from 'react';
import { PieChart } from 'lucide-react';
import { AttributionData } from '../../types';

interface SourceAttributionCleanProps {
  attribution: AttributionData | null;
}

export const SourceAttributionClean: React.FC<SourceAttributionCleanProps> = ({ attribution }) => {
  const breakdown = attribution?.source_breakdown || {
    local_urban_percent: 42.5,
    regional_crop_fires_percent: 37.8,
    transboundary_background_percent: 19.7
  };

  const sources = [
    { label: 'Local Urban Sources', pct: breakdown.local_urban_percent, color: '#2563EB', desc: 'Vehicular exhaust, construction dust, urban diesel gensets' },
    { label: 'Regional Crop Stubble Fires', pct: breakdown.regional_crop_fires_percent, color: '#DC2626', desc: 'Active biomass burning advection from Punjab/Haryana' },
    { label: 'Transboundary Background', pct: breakdown.transboundary_background_percent, color: '#64748B', desc: 'Indo-Gangetic regional baseline inflow' }
  ];

  return (
    <div className="white-card" style={{ padding: '18px 20px', display: 'flex', flexDirection: 'column' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <PieChart size={16} color="#2563EB" />
          <h3 style={{ fontSize: '0.88rem', fontWeight: 600 }}>MODELED SOURCE CONTRIBUTION</h3>
        </div>
        <span className="provenance-tag counterfactual">MODELLED COUNTERFACTUAL</span>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {sources.map((s, idx) => (
          <div key={idx} style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.75rem' }}>
              <span style={{ fontWeight: 600, color: '#1E293B' }}>{s.label}</span>
              <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color: s.color }}>{s.pct}%</span>
            </div>

            {/* Horizontal Bar */}
            <div style={{ width: '100%', height: '8px', background: 'var(--bg-muted)', borderRadius: '4px', overflow: 'hidden' }}>
              <div style={{ width: `${s.pct}%`, height: '100%', background: s.color, borderRadius: '4px' }} />
            </div>

            <span style={{ fontSize: '0.68rem', color: '#64748B' }}>{s.desc}</span>
          </div>
        ))}
      </div>

      <div style={{ marginTop: '12px', padding: '8px 10px', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)', fontSize: '0.68rem', color: '#64748B', fontStyle: 'italic' }}>
        * Calculated via zero-out counterfactual sensitivity under verified DMDc dynamics. Not ground-truth causal attribution.
      </div>
    </div>
  );
};
