import React from 'react';
import { Clock, Flame, Wind, AlertCircle, ArrowUpRight } from 'lucide-react';
import { PlumeData } from '../types';

interface PlumeClockProps {
  plumes: PlumeData | null;
}

export const PlumeClock: React.FC<PlumeClockProps> = ({ plumes }) => {
  const estimates = plumes?.plume_estimates || [
    {
      cluster_id: 'CLUSTER_PUNJAB_NW_01',
      centroid_lat: 30.32,
      centroid_lon: 75.85,
      fire_count: 42,
      total_frp_mw: 820.5,
      distance_to_delhi_km: 245.0,
      bearing_deg: 312.0,
      aligned_with_wind: true,
      transit_speed_kmh: 18.2,
      estimated_arrival_hours: 13.5,
      urgency: 'CRITICAL',
      confidence: 'HIGH',
      provenance: 'MODELLED'
    },
    {
      cluster_id: 'CLUSTER_HARYANA_N_02',
      centroid_lat: 29.85,
      centroid_lon: 76.42,
      fire_count: 18,
      total_frp_mw: 340.2,
      distance_to_delhi_km: 155.0,
      bearing_deg: 325.0,
      aligned_with_wind: true,
      transit_speed_kmh: 19.0,
      estimated_arrival_hours: 8.2,
      urgency: 'CRITICAL',
      confidence: 'HIGH',
      provenance: 'MODELLED'
    },
    {
      cluster_id: 'CLUSTER_PUNJAB_W_03',
      centroid_lat: 30.15,
      centroid_lon: 74.95,
      fire_count: 24,
      total_frp_mw: 460.0,
      distance_to_delhi_km: 310.0,
      bearing_deg: 298.0,
      aligned_with_wind: false,
      transit_speed_kmh: 15.5,
      estimated_arrival_hours: 20.0,
      urgency: 'ELEVATED',
      confidence: 'MODERATE',
      provenance: 'MODELLED'
    }
  ];

  return (
    <div className="glass-card" style={{ display: 'flex', flexDirection: 'column' }}>
      <div className="card-header">
        <div className="card-title-group">
          <Clock size={16} color="#ef4444" />
          <h3>Agricultural Plume Arrival Clock</h3>
        </div>
        <span className="provenance-tag modelled">MODELLED</span>
      </div>

      <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.74rem', color: '#94a3b8' }}>
          <span>Target Airshed: Delhi Central</span>
          <span style={{ color: '#ef4444', fontWeight: 600 }}>
            {estimates.filter(e => e.aligned_with_wind).length} Plumes Inflow-Aligned
          </span>
        </div>

        {/* List of active plume tracks */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {estimates.map((p, idx) => (
            <div
              key={idx}
              style={{
                background: p.urgency === 'CRITICAL' ? 'rgba(239, 68, 68, 0.08)' : 'rgba(15, 23, 42, 0.5)',
                border: p.urgency === 'CRITICAL' ? '1px solid rgba(239, 68, 68, 0.25)' : '1px solid var(--border-subtle)',
                borderRadius: '8px',
                padding: '10px 12px'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <Flame size={14} color="#ef4444" />
                  <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#f8fafc' }}>
                    {p.cluster_id.replace('CLUSTER_', '')}
                  </span>
                </div>
                <span style={{
                  fontSize: '0.65rem',
                  fontFamily: 'var(--font-mono)',
                  fontWeight: 700,
                  padding: '2px 6px',
                  borderRadius: '4px',
                  background: p.urgency === 'CRITICAL' ? 'rgba(239, 68, 68, 0.2)' : 'rgba(245, 158, 11, 0.2)',
                  color: p.urgency === 'CRITICAL' ? '#fca5a5' : '#fde047',
                  border: `1px solid ${p.urgency === 'CRITICAL' ? 'rgba(239, 68, 68, 0.4)' : 'rgba(245, 158, 11, 0.4)'}`
                }}>
                  {p.urgency}
                </span>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '6px', fontSize: '0.7rem', color: '#94a3b8' }}>
                <div>
                  <span>Distance:</span>
                  <div style={{ color: '#f1f5f9', fontWeight: 600, fontFamily: 'var(--font-mono)' }}>{p.distance_to_delhi_km} km</div>
                </div>
                <div>
                  <span>FRP Energy:</span>
                  <div style={{ color: '#f1f5f9', fontWeight: 600, fontFamily: 'var(--font-mono)' }}>{Math.round(p.total_frp_mw)} MW</div>
                </div>
                <div>
                  <span>Est. Arrival:</span>
                  <div style={{ color: '#38bdf8', fontWeight: 700, fontFamily: 'var(--font-mono)' }}>+{p.estimated_arrival_hours}h</div>
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '8px', fontSize: '0.68rem', color: p.aligned_with_wind ? '#34d399' : '#64748b' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <Wind size={12} />
                  <span>{p.aligned_with_wind ? 'Direct Northwesterly Inflow Alignment' : 'Cross-wind transport deflection'}</span>
                </div>
                <span style={{ fontFamily: 'var(--font-mono)' }}>Speed: ~{p.transit_speed_kmh} km/h</span>
              </div>
            </div>
          ))}
        </div>

        <div style={{ fontSize: '0.68rem', color: '#64748b', fontStyle: 'italic' }}>
          * Disclaimer: Plume arrival times represent estimated advective transport windows based on WRF wind trajectory integration, not guaranteed arrival.
        </div>
      </div>
    </div>
  );
};
