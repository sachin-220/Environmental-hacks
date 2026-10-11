import React from 'react';
import { ShieldAlert, AlertTriangle } from 'lucide-react';
import { CurrentState } from '../types';

interface AQICardProps {
  state: CurrentState | null;
}

export const AQICard: React.FC<AQICardProps> = ({ state }) => {
  const aqi = state?.aqi ?? 385;
  const category = state?.category ?? 'Very Poor';
  const dominant = state?.dominant_pollutant ?? 'PM2.5';

  const getAQIColor = (val: number): string => {
    if (val <= 50) return '#10b981';
    if (val <= 100) return '#84cc16';
    if (val <= 200) return '#eab308';
    if (val <= 300) return '#f97316';
    if (val <= 400) return '#ef4444';
    return '#991b1b';
  };

  const aqiColor = getAQIColor(aqi);

  // SVG circular gauge calculation
  const radius = 72;
  const circumference = 2 * Math.PI * radius;
  const pct = Math.min(Math.max(aqi / 500, 0), 1);
  const strokeDashoffset = circumference - pct * circumference;

  return (
    <div className="glass-card naqi-card">
      <div style={{ width: '100%', display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <ShieldAlert size={16} color={aqiColor} />
          <span style={{ fontSize: '0.78rem', fontWeight: 700, letterSpacing: '0.05em', color: '#94a3b8' }}>CPCB NAQI INDEX</span>
        </div>
        <span className="provenance-tag modelled">MODELLED</span>
      </div>

      <div className="naqi-gauge-wrap">
        <svg className="naqi-svg-ring" width="180" height="180">
          <circle
            cx="90"
            cy="90"
            r={radius}
            stroke="rgba(255, 255, 255, 0.08)"
            strokeWidth="12"
            fill="transparent"
          />
          <circle
            cx="90"
            cy="90"
            r={radius}
            stroke={aqiColor}
            strokeWidth="12"
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            fill="transparent"
            style={{
              transition: 'stroke-dashoffset 0.8s cubic-bezier(0.16, 1, 0.3, 1)',
              filter: `drop-shadow(0 0 10px ${aqiColor})`
            }}
          />
        </svg>

        <div className="naqi-inner-content">
          <span className="naqi-value" style={{ color: aqiColor }}>{aqi}</span>
          <span className="naqi-sublabel">AIR QUALITY INDEX</span>
        </div>
      </div>

      <div
        className="naqi-badge-pill"
        style={{
          background: `${aqiColor}22`,
          color: aqiColor,
          border: `1px solid ${aqiColor}66`
        }}
      >
        {category}
      </div>

      <div style={{ width: '100%', background: 'rgba(15, 23, 42, 0.4)', borderRadius: '8px', padding: '10px 14px', border: '1px solid rgba(255, 255, 255, 0.05)', marginTop: '4px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.75rem', marginBottom: '6px' }}>
          <span style={{ color: '#94a3b8' }}>Dominant Pollutant:</span>
          <span style={{ fontWeight: 700, color: '#f8fafc', fontFamily: 'var(--font-mono)' }}>{dominant}</span>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.75rem' }}>
          <span style={{ color: '#94a3b8' }}>Airshed Location:</span>
          <span style={{ color: '#38bdf8', fontFamily: 'var(--font-mono)' }}>Delhi Central (28.61°N, 77.21°E)</span>
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '12px', fontSize: '0.72rem', color: '#f87171' }}>
        <AlertTriangle size={13} />
        <span>Health Advisory: Emergency respiratory caution</span>
      </div>
    </div>
  );
};
