import React, { useState } from 'react';
import { TrendingUp, Clock, Info, AlertCircle, Zap } from 'lucide-react';
import { ForecastData } from '../types';

interface ForecastChartProps {
  forecast: ForecastData | null;
}

export const ForecastChart: React.FC<ForecastChartProps> = ({ forecast }) => {
  const [activeTab, setActiveTab] = useState<'pm25' | 'aqi'>('pm25');
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);

  const timeline = forecast?.hourly_timeline || [];
  const latency = forecast?.rollout_latency_ms ?? 32.2;

  // Chart coordinate configuration
  const width = 800;
  const height = 280;
  const padding = { top: 30, right: 30, bottom: 40, left: 55 };

  const chartWidth = width - padding.left - padding.right;
  const chartHeight = height - padding.top - padding.bottom;

  // Compute scales
  const maxVal = activeTab === 'pm25'
    ? Math.max(...timeline.map(t => t.pm25_upper || t.pm25), 350) * 1.1
    : 500;

  const minVal = 0;

  const getX = (i: number) => padding.left + (i / Math.max(timeline.length - 1, 1)) * chartWidth;
  const getY = (val: number) => padding.top + chartHeight - ((val - minVal) / (maxVal - minVal)) * chartHeight;

  // Build SVG path strings
  let linePath = '';
  let upperPath = '';
  let lowerPath = '';

  if (timeline.length > 0) {
    if (activeTab === 'pm25') {
      linePath = timeline.reduce((acc, pt, i) => `${acc} ${i === 0 ? 'M' : 'L'} ${getX(i)} ${getY(pt.pm25)}`, '');
      upperPath = timeline.reduce((acc, pt, i) => `${acc} ${i === 0 ? 'M' : 'L'} ${getX(i)} ${getY(pt.pm25_upper)}`, '');
      // Reverse lower path to form closed polygon ribbon
      lowerPath = [...timeline].reverse().reduce((acc, pt, i) => {
        const revIdx = timeline.length - 1 - i;
        return `${acc} L ${getX(revIdx)} ${getY(pt.pm25_lower)}`;
      }, '');
    } else {
      linePath = timeline.reduce((acc, pt, i) => `${acc} ${i === 0 ? 'M' : 'L'} ${getX(i)} ${getY(pt.aqi)}`, '');
    }
  }

  const ribbonPath = activeTab === 'pm25' && timeline.length > 0 ? `${upperPath} ${lowerPath} Z` : '';

  const hoveredPoint = hoveredIndex !== null && timeline[hoveredIndex] ? timeline[hoveredIndex] : null;

  return (
    <div className="glass-card" style={{ display: 'flex', flexDirection: 'column' }}>
      <div className="card-header">
        <div className="card-title-group">
          <TrendingUp size={16} color="#06b6d4" />
          <h3>72-Hour Coupled Forward Forecast</h3>
          <div style={{ display: 'flex', gap: '6px', marginLeft: '12px' }}>
            <button
              onClick={() => setActiveTab('pm25')}
              style={{
                background: activeTab === 'pm25' ? 'rgba(6, 182, 212, 0.2)' : 'transparent',
                color: activeTab === 'pm25' ? '#38bdf8' : '#64748b',
                border: activeTab === 'pm25' ? '1px solid #06b6d4' : '1px solid transparent',
                borderRadius: '4px',
                padding: '3px 10px',
                fontSize: '0.72rem',
                cursor: 'pointer',
                fontFamily: 'var(--font-mono)'
              }}
            >
              PM2.5 (µg/m³)
            </button>
            <button
              onClick={() => setActiveTab('aqi')}
              style={{
                background: activeTab === 'aqi' ? 'rgba(239, 68, 68, 0.2)' : 'transparent',
                color: activeTab === 'aqi' ? '#f87171' : '#64748b',
                border: activeTab === 'aqi' ? '1px solid #ef4444' : '1px solid transparent',
                borderRadius: '4px',
                padding: '3px 10px',
                fontSize: '0.72rem',
                cursor: 'pointer',
                fontFamily: 'var(--font-mono)'
              }}
            >
              CPCB NAQI
            </button>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.72rem', color: '#10b981', fontFamily: 'var(--font-mono)' }}>
            <Zap size={13} />
            <span>Rollout Latency: {latency} ms</span>
          </div>
          <span className="provenance-tag modelled">MODELLED</span>
        </div>
      </div>

      <div className="card-body" style={{ padding: '16px 20px 10px 20px' }}>
        <div style={{ position: 'relative', width: '100%', overflowX: 'auto' }}>
          <svg
            viewBox={`0 0 ${width} ${height}`}
            style={{ width: '100%', height: 'auto', display: 'block' }}
            onMouseLeave={() => setHoveredIndex(null)}
          >
            <defs>
              <linearGradient id="lineGrad" x1="0" y1="0" x2="1" y2="0">
                <stop offset="0%" stopColor="#06b6d4" />
                <stop offset="50%" stopColor="#f59e0b" />
                <stop offset="100%" stopColor="#ef4444" />
              </linearGradient>
              <linearGradient id="ribbonGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="rgba(6, 182, 212, 0.25)" />
                <stop offset="100%" stopColor="rgba(6, 182, 212, 0.03)" />
              </linearGradient>
            </defs>

            {/* Grid horizontal lines */}
            {[0, 0.25, 0.5, 0.75, 1].map((ratio, idx) => {
              const val = Math.round(minVal + ratio * (maxVal - minVal));
              const yPos = getY(val);
              return (
                <g key={idx}>
                  <line
                    x1={padding.left}
                    y1={yPos}
                    x2={width - padding.right}
                    y2={yPos}
                    stroke="rgba(255, 255, 255, 0.06)"
                    strokeDasharray="4 4"
                  />
                  <text
                    x={padding.left - 10}
                    y={yPos + 4}
                    textAnchor="end"
                    fill="#64748b"
                    fontSize="10"
                    fontFamily="var(--font-mono)"
                  >
                    {val}
                  </text>
                </g>
              );
            })}

            {/* Threshold line for CPCB Severe */}
            {activeTab === 'pm25' && maxVal >= 250 && (
              <g>
                <line
                  x1={padding.left}
                  y1={getY(250)}
                  x2={width - padding.right}
                  y2={getY(250)}
                  stroke="rgba(239, 68, 68, 0.45)"
                  strokeWidth="1.5"
                  strokeDasharray="2 2"
                />
                <text
                  x={width - padding.right}
                  y={getY(250) - 5}
                  textAnchor="end"
                  fill="#ef4444"
                  fontSize="9"
                  fontFamily="var(--font-mono)"
                  fontWeight="600"
                >
                  CPCB Severe Threshold (250 µg/m³)
                </text>
              </g>
            )}

            {/* Uncertainty Ribbon */}
            {activeTab === 'pm25' && ribbonPath && (
              <path d={ribbonPath} fill="url(#ribbonGrad)" />
            )}

            {/* Main Rollout Curve */}
            {linePath && (
              <path
                d={linePath}
                fill="none"
                stroke="url(#lineGrad)"
                strokeWidth="2.5"
                strokeLinecap="round"
              />
            )}

            {/* Horizon Checkpoints (1h, 12h, 24h, 48h, 72h) */}
            {[0, 11, 23, 47, 71].map((hIdx) => {
              if (!timeline[hIdx]) return null;
              const pt = timeline[hIdx];
              const cx = getX(hIdx);
              const cy = getY(activeTab === 'pm25' ? pt.pm25 : pt.aqi);
              return (
                <g key={hIdx}>
                  <circle
                    cx={cx}
                    cy={cy}
                    r="4"
                    fill="#06b6d4"
                    stroke="#080c14"
                    strokeWidth="2"
                  />
                  <text
                    x={cx}
                    y={height - padding.bottom + 18}
                    textAnchor="middle"
                    fill="#94a3b8"
                    fontSize="10"
                    fontFamily="var(--font-mono)"
                  >
                    +{hIdx + 1}h
                  </text>
                </g>
              );
            })}

            {/* Interactive hover line and cursor */}
            {hoveredIndex !== null && timeline[hoveredIndex] && (
              <g>
                <line
                  x1={getX(hoveredIndex)}
                  y1={padding.top}
                  x2={getX(hoveredIndex)}
                  y2={height - padding.bottom}
                  stroke="rgba(6, 182, 212, 0.7)"
                  strokeWidth="1.5"
                  strokeDasharray="3 3"
                />
                <circle
                  cx={getX(hoveredIndex)}
                  cy={getY(activeTab === 'pm25' ? timeline[hoveredIndex].pm25 : timeline[hoveredIndex].aqi)}
                  r="6"
                  fill="#ffffff"
                  stroke="#06b6d4"
                  strokeWidth="3"
                />
              </g>
            )}

            {/* Transparent overlay for mouse interaction */}
            {timeline.map((_, idx) => {
              const xStart = idx === 0 ? padding.left : (getX(idx - 1) + getX(idx)) / 2;
              const xEnd = idx === timeline.length - 1 ? width - padding.right : (getX(idx) + getX(idx + 1)) / 2;
              return (
                <rect
                  key={idx}
                  x={xStart}
                  y={padding.top}
                  width={xEnd - xStart}
                  height={chartHeight}
                  fill="transparent"
                  style={{ cursor: 'crosshair' }}
                  onMouseEnter={() => setHoveredIndex(idx)}
                />
              );
            })}
          </svg>
        </div>

        {/* Hover Inspector Tooltip Bar */}
        {hoveredPoint ? (
          <div style={{
            background: 'rgba(15, 23, 42, 0.9)',
            border: '1px solid #06b6d4',
            borderRadius: '8px',
            padding: '8px 16px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginTop: '8px',
            fontFamily: 'var(--font-mono)',
            fontSize: '0.78rem'
          }}>
            <div>
              <span style={{ color: '#06b6d4', fontWeight: 700 }}>Horizon: {hoveredPoint.horizon_label}</span>
              <span style={{ color: '#64748b', marginLeft: '12px' }}>PBLH: {hoveredPoint.boundary_layer_height}m</span>
              <span style={{ color: '#64748b', marginLeft: '12px' }}>Wind: {hoveredPoint.wind_speed_10m} m/s</span>
            </div>
            <div>
              <span style={{ color: '#f8fafc', fontWeight: 700 }}>PM2.5: {hoveredPoint.pm25} µg/m³</span>
              <span style={{ color: '#38bdf8', marginLeft: '8px' }}>[{hoveredPoint.pm25_lower} – {hoveredPoint.pm25_upper}]</span>
              <span style={{
                marginLeft: '12px',
                padding: '2px 8px',
                borderRadius: '4px',
                background: hoveredPoint.aqi > 400 ? 'rgba(153, 27, 27, 0.4)' : 'rgba(239, 68, 68, 0.3)',
                color: hoveredPoint.aqi > 400 ? '#fca5a5' : '#f87171',
                fontWeight: 700
              }}>
                AQI {hoveredPoint.aqi} ({hoveredPoint.category})
              </span>
            </div>
          </div>
        ) : (
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '8px', fontSize: '0.72rem', color: '#64748b', fontFamily: 'var(--font-mono)' }}>
            <span>Hover across timeline to inspect hourly state transitions & Lyapunov 95% confidence intervals</span>
            <span>Lyapunov propagation: Σ_k+1 = A Σ_k Aᵀ + Σ_w</span>
          </div>
        )}

        {/* Section 10 Disclaimer Mandatory Display */}
        <div className="section10-disclaimer" style={{ marginTop: '14px' }}>
          <AlertCircle size={18} color="#f59e0b" style={{ flexShrink: 0 }} />
          <div>
            <strong>SCIENTIFIC VERIFICATION DISCLAIMER:</strong> 72h trajectory: <strong>MODEL ROLLOUT</strong> | Held-out empirical accuracy: <strong>VALIDATED OVER AVAILABLE 1–10H TEST HORIZONS</strong> (Rank-12 Operator, SVD λ=0).
          </div>
        </div>
      </div>
    </div>
  );
};
