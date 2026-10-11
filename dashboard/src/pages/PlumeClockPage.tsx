import React from 'react';
import { Clock, Flame, Wind } from 'lucide-react';
import { PlumeClockClean } from '../components/plume/PlumeClockClean';
import { PlumeData } from '../types';

interface PlumeClockPageProps {
  plumes: PlumeData | null;
}

export const PlumeClockPage: React.FC<PlumeClockPageProps> = ({ plumes }) => {
  const estimates = plumes?.plume_estimates || [];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '22px' }}>
      <div className="white-card" style={{ padding: '20px 24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#111827' }}>REGIONAL BIOMASS PLUME ARRIVAL CLOCK</h2>
            <p style={{ fontSize: '0.78rem', color: '#64748B', marginTop: '2px' }}>
              Dynamic plume tracking integrating NASA FIRMS active fire satellite detections with trajectory wind vectors
            </p>
          </div>
          <span className="provenance-tag modelled">MODELLED</span>
        </div>
      </div>

      <PlumeClockClean plumes={plumes} />

      {/* Fire Clusters Table */}
      <div className="white-card" style={{ padding: '20px' }}>
        <h3 style={{ fontSize: '0.9rem', fontWeight: 600, marginBottom: '14px' }}>
          UPWIND ACTIVE SATELLITE FIRE CLUSTERS (PUNJAB & HARYANA)
        </h3>

        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.76rem', fontFamily: 'var(--font-mono)' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--border-subtle)', textAlign: 'left', color: '#64748B' }}>
              <th style={{ padding: '8px 12px' }}>CLUSTER ID</th>
              <th style={{ padding: '8px 12px' }}>CENTROID (LAT, LON)</th>
              <th style={{ padding: '8px 12px' }}>TOTAL FRP</th>
              <th style={{ padding: '8px 12px' }}>DISTANCE</th>
              <th style={{ padding: '8px 12px' }}>EST. ARRIVAL</th>
              <th style={{ padding: '8px 12px' }}>WIND ALIGNMENT</th>
              <th style={{ padding: '8px 12px', textAlign: 'right' }}>URGENCY</th>
            </tr>
          </thead>
          <tbody>
            {estimates.map((p) => (
              <tr key={p.cluster_id} style={{ borderBottom: '1px solid #F1F5F9' }}>
                <td style={{ padding: '10px 12px', fontWeight: 600, color: '#1E293B' }}>
                  {p.cluster_id.replace('CLUSTER_', '')}
                </td>
                <td style={{ padding: '10px 12px', color: '#64748B' }}>
                  {p.centroid_lat.toFixed(2)}°N, {p.centroid_lon.toFixed(2)}°E
                </td>
                <td style={{ padding: '10px 12px', color: '#DC2626', fontWeight: 700 }}>
                  {Math.round(p.total_frp_mw)} MW
                </td>
                <td style={{ padding: '10px 12px' }}>
                  {p.distance_to_delhi_km} km
                </td>
                <td style={{ padding: '10px 12px', color: '#2563EB', fontWeight: 700 }}>
                  +{p.estimated_arrival_hours}h
                </td>
                <td style={{ padding: '10px 12px', color: p.aligned_with_wind ? '#16A34A' : '#D97706', fontWeight: 600 }}>
                  {p.aligned_with_wind ? 'INFLOW ALIGNED' : 'CROSS-WIND'}
                </td>
                <td style={{ padding: '10px 12px', textAlign: 'right' }}>
                  <span style={{
                    padding: '2px 6px',
                    borderRadius: '4px',
                    fontSize: '0.68rem',
                    fontWeight: 700,
                    background: p.urgency === 'CRITICAL' ? '#FEF2F2' : '#FFFBEB',
                    color: p.urgency === 'CRITICAL' ? '#DC2626' : '#D97706'
                  }}>
                    {p.urgency}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
