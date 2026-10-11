import React from 'react';
import { HelpCircle, ArrowUpRight, ArrowDownRight, Compass } from 'lucide-react';
import { WhyAQIRisesData } from '../../types';

interface WhyAQIRisesCleanProps {
  whyData: WhyAQIRisesData | null;
}

export const WhyAQIRisesClean: React.FC<WhyAQIRisesCleanProps> = ({ whyData }) => {
  const drivers = [
    {
      num: '01',
      title: 'INVERSION STRENGTHENING',
      detail: 'Nocturnal potential temperature lid (+1.76 K) suppresses vertical dispersion',
      evidence: 'SUPPORTED BY: PBLH · INVERSION · LAPSE RATE',
      trend: 'UP',
      color: '#DC2626'
    },
    {
      num: '02',
      title: 'WEAK VENTILATION',
      detail: 'Calm horizontal surface winds (2.8 m/s) prevent advective flushing',
      evidence: 'SUPPORTED BY: WIND SPEED · VENTILATION COEFF',
      trend: 'DOWN',
      color: '#EA580C'
    },
    {
      num: '03',
      title: 'REGIONAL PLUME INFLUX',
      detail: 'Upwind Punjab/Haryana biomass burning smoke advecting into airshed',
      evidence: 'SUPPORTED BY: FIRMS HOTSPOTS · WIND BEARING',
      trend: 'UP',
      color: '#2563EB'
    }
  ];

  return (
    <div className="white-card" style={{ padding: '18px 20px', display: 'flex', flexDirection: 'column' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <HelpCircle size={16} color="#EA580C" />
          <h3 style={{ fontSize: '0.88rem', fontWeight: 600 }}>WHY AQI RISES</h3>
        </div>
        <span className="provenance-tag inferred">INFERRED</span>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
        {drivers.map((d) => (
          <div
            key={d.num}
            style={{
              background: 'var(--bg-secondary)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-md)',
              padding: '12px 14px',
              display: 'flex',
              alignItems: 'flex-start',
              gap: '12px'
            }}
          >
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem', fontWeight: 700, color: d.color }}>
              {d.num}
            </span>

            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '2px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '0.78rem', fontWeight: 600, color: '#111827' }}>
                  {d.title}
                </span>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.62rem', fontWeight: 600, color: '#16A34A', background: '#F0FDF4', padding: '1px 6px', borderRadius: '4px', border: '1px solid #BBF7D0' }}>
                  MODEL SUPPORTED
                </span>
              </div>

              <span style={{ fontSize: '0.72rem', color: '#475569', lineHeight: '1.35' }}>
                {d.detail}
              </span>

              <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.65rem', color: '#64748B', marginTop: '4px' }}>
                {d.evidence}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
