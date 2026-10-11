import React from 'react';
import { Clock, Flame, Wind, ArrowRight } from 'lucide-react';
import { PlumeData } from '../../types';

interface PlumeClockCleanProps {
  plumes: PlumeData | null;
}

export const PlumeClockClean: React.FC<PlumeClockCleanProps> = ({ plumes }) => {
  const estimates = plumes?.plume_estimates || [];
  const primaryPlume = estimates[0] || {
    cluster_id: 'PUNJAB_NW_01',
    distance_to_delhi_km: 245.0,
    total_frp_mw: 820.5,
    estimated_arrival_hours: 13.5,
    aligned_with_wind: true,
    transit_speed_kmh: 18.2
  };

  return (
    <div className="white-card" style={{ padding: '18px 20px', display: 'flex', flexDirection: 'column' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Clock size={16} color="#DC2626" />
          <h3 style={{ fontSize: '0.88rem', fontWeight: 600 }}>PLUME CLOCK</h3>
        </div>
        <span className="provenance-tag modelled">MODELLED</span>
      </div>

      {/* Visual Timeline Graphic */}
      <div style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-md)', padding: '14px 16px', marginBottom: '12px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.72rem', fontWeight: 700, color: '#DC2626' }}>
            <Flame size={14} />
            <span>FIRE DETECTED</span>
          </div>
          <div style={{ fontSize: '0.72rem', fontWeight: 700, color: '#2563EB' }}>
            DELHI NCR ARRIVAL
          </div>
        </div>

        {/* Timeline track */}
        <div style={{ position: 'relative', width: '100%', height: '24px', display: 'flex', alignItems: 'center' }}>
          <div style={{ position: 'absolute', left: 0, right: 0, height: '3px', background: '#E2E8F0' }} />
          <div style={{ position: 'absolute', left: 0, width: '65%', height: '3px', background: '#2563EB' }} />

          {/* Points */}
          <div style={{ position: 'absolute', left: '0%', transform: 'translateX(-50%)', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
            <div style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#DC2626', border: '2px solid #FFFFFF', boxShadow: 'var(--shadow-subtle)' }} />
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.62rem', color: '#64748B', marginTop: '4px' }}>NOW</span>
          </div>

          <div style={{ position: 'absolute', left: '45%', transform: 'translateX(-50%)', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
            <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#2563EB', border: '2px solid #FFFFFF' }} />
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.62rem', color: '#64748B', marginTop: '4px' }}>+6H</span>
          </div>

          <div style={{ position: 'absolute', left: '100%', transform: 'translateX(-50%)', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
            <div style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#16A34A', border: '2px solid #FFFFFF', boxShadow: 'var(--shadow-subtle)' }} />
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.62rem', color: '#16A34A', fontWeight: 700, marginTop: '4px' }}>
              +{primaryPlume.estimated_arrival_hours}H
            </span>
          </div>
        </div>
      </div>

      {/* Telemetry metrics row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '8px', fontFamily: 'var(--font-mono)', fontSize: '0.72rem' }}>
        <div style={{ background: 'var(--bg-secondary)', padding: '6px 8px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
          <span style={{ color: '#64748B', fontSize: '0.62rem', display: 'block' }}>FRP ENERGY</span>
          <span style={{ fontWeight: 700, color: '#DC2626' }}>{Math.round(primaryPlume.total_frp_mw)} MW</span>
        </div>

        <div style={{ background: 'var(--bg-secondary)', padding: '6px 8px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
          <span style={{ color: '#64748B', fontSize: '0.62rem', display: 'block' }}>DISTANCE</span>
          <span style={{ fontWeight: 700, color: '#1E293B' }}>{primaryPlume.distance_to_delhi_km} km</span>
        </div>

        <div style={{ background: 'var(--bg-secondary)', padding: '6px 8px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
          <span style={{ color: '#64748B', fontSize: '0.62rem', display: 'block' }}>TRANSIT SPEED</span>
          <span style={{ fontWeight: 700, color: '#1E293B' }}>{primaryPlume.transit_speed_kmh} km/h</span>
        </div>

        <div style={{ background: 'var(--bg-secondary)', padding: '6px 8px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
          <span style={{ color: '#64748B', fontSize: '0.62rem', display: 'block' }}>WIND ALIGN</span>
          <span style={{ fontWeight: 700, color: primaryPlume.aligned_with_wind ? '#16A34A' : '#D97706' }}>
            {primaryPlume.aligned_with_wind ? 'DIRECT' : 'CROSS'}
          </span>
        </div>
      </div>
    </div>
  );
};
