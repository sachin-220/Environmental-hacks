import React from 'react';
import { PieChart, Layers } from 'lucide-react';
import { SourceAttributionClean } from '../components/attribution/SourceAttributionClean';
import { AttributionData } from '../types';

interface SourcesPageProps {
  attribution: AttributionData | null;
}

export const SourcesPage: React.FC<SourcesPageProps> = ({ attribution }) => {
  const sectors = attribution?.sector_contributions || [
    { sector: 'agricultural_fires', displayName: 'Stubble Burning', share_percent: 37.8, pm25_equivalent_ugm3: 89.0, zero_out_reduction_ugm3: 37.8, provenance: 'COUNTERFACTUAL' },
    { sector: 'road_transport', displayName: 'Vehicular Transport', share_percent: 28.4, pm25_equivalent_ugm3: 66.8, zero_out_reduction_ugm3: 28.4, provenance: 'COUNTERFACTUAL' },
    { sector: 'heavy_industry', displayName: 'Industrial Point Sources', share_percent: 18.6, pm25_equivalent_ugm3: 43.8, zero_out_reduction_ugm3: 18.6, provenance: 'COUNTERFACTUAL' },
    { sector: 'power_plants', displayName: 'Thermal Power Plants', share_percent: 14.2, pm25_equivalent_ugm3: 33.4, zero_out_reduction_ugm3: 14.2, provenance: 'COUNTERFACTUAL' },
    { sector: 'construction_dust', displayName: 'Construction Fugitive Dust', share_percent: 11.5, pm25_equivalent_ugm3: 27.1, zero_out_reduction_ugm3: 11.5, provenance: 'COUNTERFACTUAL' }
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '22px' }}>
      <div className="white-card" style={{ padding: '20px 24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#111827' }}>SOURCE ATTRIBUTION & EMISSION RESPONSE</h2>
            <p style={{ fontSize: '0.78rem', color: '#64748B', marginTop: '2px' }}>
              Counterfactual sensitivity analysis disaggregating local urban emissions from regional stubble burning
            </p>
          </div>
          <span className="provenance-tag counterfactual">MODELLED COUNTERFACTUAL</span>
        </div>
      </div>

      <SourceAttributionClean attribution={attribution} />

      {/* Sector Zero-Out Sensitivity Matrix */}
      <div className="white-card" style={{ padding: '20px' }}>
        <h3 style={{ fontSize: '0.9rem', fontWeight: 600, marginBottom: '14px' }}>
          SECTOR-BY-SECTOR ZERO-OUT SENSITIVITY TABLE
        </h3>

        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.76rem', fontFamily: 'var(--font-mono)' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--border-subtle)', textAlign: 'left', color: '#64748B' }}>
              <th style={{ padding: '8px 12px' }}>SECTOR NAME</th>
              <th style={{ padding: '8px 12px' }}>MODELED SHARE</th>
              <th style={{ padding: '8px 12px' }}>PM2.5 EQUIVALENT</th>
              <th style={{ padding: '8px 12px' }}>ZERO-OUT REDUCTION</th>
              <th style={{ padding: '8px 12px', textAlign: 'right' }}>PROVENANCE</th>
            </tr>
          </thead>
          <tbody>
            {sectors.map((s, idx) => (
              <tr key={idx} style={{ borderBottom: '1px solid #F1F5F9' }}>
                <td style={{ padding: '10px 12px', fontWeight: 600, color: '#1E293B' }}>
                  {s.displayName || s.sector.replace('_', ' ').toUpperCase()}
                </td>
                <td style={{ padding: '10px 12px', color: '#2563EB', fontWeight: 700 }}>
                  {s.share_percent}%
                </td>
                <td style={{ padding: '10px 12px' }}>
                  {s.pm25_equivalent_ugm3} µg/m³
                </td>
                <td style={{ padding: '10px 12px', color: '#16A34A', fontWeight: 700 }}>
                  -{s.zero_out_reduction_ugm3} µg/m³
                </td>
                <td style={{ padding: '10px 12px', textAlign: 'right' }}>
                  <span className="provenance-tag counterfactual">COUNTERFACTUAL</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
