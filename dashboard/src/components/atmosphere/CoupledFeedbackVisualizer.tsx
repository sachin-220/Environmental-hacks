import React, { useState } from 'react';
import {
  RefreshCw,
  Sun,
  CloudRain,
  Activity,
  Layers,
  TrendingUp,
  AlertOctagon,
  ArrowRight,
  ArrowDown,
  ArrowUp
} from 'lucide-react';
import { ForecastData } from '../../types';

interface CoupledFeedbackVisualizerProps {
  forecast: ForecastData | null;
  currentHour: number;
}

export const CoupledFeedbackVisualizer: React.FC<CoupledFeedbackVisualizerProps> = ({
  forecast,
  currentHour
}) => {
  const [activeTab, setActiveTab] = useState<'loops' | 'correlation'>('loops');

  const timeline = forecast?.hourly_timeline || [];
  const hourData = timeline[Math.min(currentHour, timeline.length - 1)] || {
    pm25: 225.2,
    boundary_layer_height: 845.5,
    inversion_strength: 0.0,
    aqi: 381
  };

  const pblHeight = hourData.boundary_layer_height ?? 845;
  const pm25 = hourData.pm25 ?? 225;
  const invStrength = hourData.inversion_strength ?? 2.5;

  // Feedback state indicators
  const solarDimmingPercent = Math.min(65, Math.round((pm25 / 450) * 58));
  const trappingMultiplier = (1000 / Math.max(150, pblHeight)).toFixed(1);

  return (
    <div
      style={{
        background: '#FFFFFF',
        borderRadius: '12px',
        border: '1px solid #D9DDE1',
        overflow: 'hidden',
        boxShadow: '0 4px 16px rgba(0, 0, 0, 0.05)',
        marginBottom: '20px'
      }}
    >
      {/* Header */}
      <div
        style={{
          background: '#003366',
          color: '#FFFFFF',
          padding: '12px 20px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '10px'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <RefreshCw size={18} color="#38BDF8" />
          <span style={{ fontSize: '14px', fontWeight: 800, letterSpacing: '0.04em' }}>
            TWO-WAY COUPLED METEOROLOGY–CHEMISTRY FEEDBACK ENGINE
          </span>
        </div>

        <div style={{ display: 'flex', gap: '6px' }}>
          <button
            onClick={() => setActiveTab('loops')}
            style={{
              background: activeTab === 'loops' ? '#38BDF8' : 'rgba(255,255,255,0.15)',
              color: activeTab === 'loops' ? '#0F172A' : '#FFFFFF',
              border: 'none',
              borderRadius: '4px',
              padding: '4px 10px',
              fontSize: '11px',
              fontWeight: 700,
              cursor: 'pointer'
            }}
          >
            Feedback Loop Flow
          </button>
          <button
            onClick={() => setActiveTab('correlation')}
            style={{
              background: activeTab === 'correlation' ? '#38BDF8' : 'rgba(255,255,255,0.15)',
              color: activeTab === 'correlation' ? '#0F172A' : '#FFFFFF',
              border: 'none',
              borderRadius: '4px',
              padding: '4px 10px',
              fontSize: '11px',
              fontWeight: 700,
              cursor: 'pointer'
            }}
          >
            PBL vs. PM2.5 Trapping Curve
          </button>
        </div>
      </div>

      {/* Main Body */}
      <div style={{ padding: '16px 20px' }}>
        {activeTab === 'loops' ? (
          <div>
            {/* Real-time feedback state tiles */}
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                gap: '12px',
                marginBottom: '16px'
              }}
            >
              <div
                style={{
                  background: '#F8FAFC',
                  borderRadius: '8px',
                  padding: '12px',
                  border: '1px solid #E2E8F0',
                  borderLeft: '4px solid #F59E0B'
                }}
              >
                <div style={{ fontSize: '11px', color: '#64748B', fontWeight: 600 }}>
                  AEROSOL SOLAR DIMMING
                </div>
                <div style={{ fontSize: '20px', fontWeight: 800, color: '#D97706', marginTop: '2px' }}>
                  -{solarDimmingPercent}% Sunlight
                </div>
                <div style={{ fontSize: '11px', color: '#475569', marginTop: '4px' }}>
                  Dense PM2.5 aerosols scatter downwelling radiation
                </div>
              </div>

              <div
                style={{
                  background: '#F8FAFC',
                  borderRadius: '8px',
                  padding: '12px',
                  border: '1px solid #E2E8F0',
                  borderLeft: '4px solid #8B5CF6'
                }}
              >
                <div style={{ fontSize: '11px', color: '#64748B', fontWeight: 600 }}>
                  BOUNDARY LAYER (PBL) COLLAPSE
                </div>
                <div style={{ fontSize: '20px', fontWeight: 800, color: '#7C3AED', marginTop: '2px' }}>
                  {Math.round(pblHeight)} m
                </div>
                <div style={{ fontSize: '11px', color: '#475569', marginTop: '4px' }}>
                  Surface cooling crushes mixing volume by {trappingMultiplier}x
                </div>
              </div>

              <div
                style={{
                  background: '#F8FAFC',
                  borderRadius: '8px',
                  padding: '12px',
                  border: '1px solid #E2E8F0',
                  borderLeft: '4px solid #EF4444'
                }}
              >
                <div style={{ fontSize: '11px', color: '#64748B', fontWeight: 600 }}>
                  THERMAL INVERSION LID
                </div>
                <div style={{ fontSize: '20px', fontWeight: 800, color: '#DC2626', marginTop: '2px' }}>
                  +{invStrength.toFixed(1)} °C Inversion
                </div>
                <div style={{ fontSize: '11px', color: '#475569', marginTop: '4px' }}>
                  Warmer air aloft caps and seals ground pollution
                </div>
              </div>

              <div
                style={{
                  background: '#F8FAFC',
                  borderRadius: '8px',
                  padding: '12px',
                  border: '1px solid #E2E8F0',
                  borderLeft: '4px solid #B91C1C'
                }}
              >
                <div style={{ fontSize: '11px', color: '#64748B', fontWeight: 600 }}>
                  POLLUTION TRAPPING AMPLIFICATION
                </div>
                <div style={{ fontSize: '20px', fontWeight: 800, color: '#991B1B', marginTop: '2px' }}>
                  {trappingMultiplier}x Concentration
                </div>
                <div style={{ fontSize: '11px', color: '#475569', marginTop: '4px' }}>
                  Stubble smoke + urban emissions trapped in lid
                </div>
              </div>
            </div>

            {/* Circular Coupled Interaction Diagram */}
            <div
              style={{
                background: '#0F172A',
                borderRadius: '8px',
                padding: '20px',
                color: '#FFFFFF'
              }}
            >
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  flexWrap: 'wrap',
                  gap: '12px',
                  textAlign: 'center'
                }}
              >
                {/* Node 1 */}
                <div style={{ flex: 1, minWidth: '160px', background: '#1E293B', padding: '12px', borderRadius: '8px' }}>
                  <div style={{ color: '#F87171', fontWeight: 800, fontSize: '13px' }}>1. EMISSION INFLOW</div>
                  <div style={{ fontSize: '11px', color: '#94A3B8', marginTop: '4px' }}>
                    Stubble-burning smoke plumes + local vehicles emit PM2.5 & NOx
                  </div>
                </div>

                <ArrowRight size={22} color="#38BDF8" />

                {/* Node 2 */}
                <div style={{ flex: 1, minWidth: '160px', background: '#1E293B', padding: '12px', borderRadius: '8px' }}>
                  <div style={{ color: '#FBBF24', fontWeight: 800, fontSize: '13px' }}>2. SOLAR DIMMING</div>
                  <div style={{ fontSize: '11px', color: '#94A3B8', marginTop: '4px' }}>
                    Aerosols scatter solar radiation (-{solarDimmingPercent}%), rapidly cooling ground
                  </div>
                </div>

                <ArrowRight size={22} color="#38BDF8" />

                {/* Node 3 */}
                <div style={{ flex: 1, minWidth: '160px', background: '#1E293B', padding: '12px', borderRadius: '8px' }}>
                  <div style={{ color: '#C084FC', fontWeight: 800, fontSize: '13px' }}>3. PBL LID COLLAPSE</div>
                  <div style={{ fontSize: '11px', color: '#94A3B8', marginTop: '4px' }}>
                    Mixing height drops to {Math.round(pblHeight)}m; capping inversion forms
                  </div>
                </div>

                <ArrowRight size={22} color="#38BDF8" />

                {/* Node 4 */}
                <div style={{ flex: 1, minWidth: '160px', background: '#1E293B', padding: '12px', borderRadius: '8px' }}>
                  <div style={{ color: '#EF4444', fontWeight: 800, fontSize: '13px' }}>4. PRESSURE COOKER SPIKE</div>
                  <div style={{ fontSize: '11px', color: '#94A3B8', marginTop: '4px' }}>
                    Trapped smoke can't escape; PM2.5 & Ozone surge to SEVERE (AQI &gt; 380)
                  </div>
                </div>
              </div>
            </div>
          </div>
        ) : (
          /* Correlation Graph */
          <div>
            <div style={{ fontSize: '12px', fontWeight: 700, color: '#003366', marginBottom: '8px' }}>
              72-HOUR DYNAMICS: PLANETARY BOUNDARY LAYER HEIGHT (PBL) vs. PM2.5 ACCUMULATION
            </div>

            {/* SVG Correlation Line Chart */}
            <svg viewBox="0 0 860 220" style={{ width: '100%', height: 'auto', display: 'block' }}>
              <rect width="860" height="220" fill="#0A0F1D" rx="6" />

              {/* Grid Lines */}
              {[40, 90, 140, 190].map((y) => (
                <line key={y} x1="50" y1={y} x2="830" y2={y} stroke="#1E293B" strokeWidth="1" strokeDasharray="3 3" />
              ))}

              {/* Left Y Axis (PM2.5: 0 to 400) */}
              <text x="40" y="45" fill="#EF4444" fontSize="10" textAnchor="end">400</text>
              <text x="40" y="115" fill="#EF4444" fontSize="10" textAnchor="end">200</text>
              <text x="40" y="185" fill="#EF4444" fontSize="10" textAnchor="end">0 µg/m³</text>

              {/* Right Y Axis (PBL Height: 0 to 1000m) */}
              <text x="840" y="45" fill="#38BDF8" fontSize="10">1000m</text>
              <text x="840" y="115" fill="#38BDF8" fontSize="10">500m</text>
              <text x="840" y="185" fill="#38BDF8" fontSize="10">0m</text>

              {/* PM2.5 Curve (Red) */}
              {timeline.length > 1 && (
                <polyline
                  fill="none"
                  stroke="#EF4444"
                  strokeWidth="2.5"
                  points={timeline
                    .map((d, i) => {
                      const x = 50 + (i / (timeline.length - 1)) * 780;
                      const y = 190 - (Math.min(400, d.pm25) / 400) * 150;
                      return `${x},${y}`;
                    })
                    .join(' ')}
                />
              )}

              {/* PBL Height Curve (Cyan) */}
              {timeline.length > 1 && (
                <polyline
                  fill="none"
                  stroke="#38BDF8"
                  strokeWidth="2"
                  strokeDasharray="4 4"
                  points={timeline
                    .map((d, i) => {
                      const x = 50 + (i / (timeline.length - 1)) * 780;
                      const y = 190 - (Math.min(1000, d.boundary_layer_height) / 1000) * 150;
                      return `${x},${y}`;
                    })
                    .join(' ')}
                />
              )}

              {/* Active Current Hour Scrubbing Line */}
              {timeline.length > 0 && (
                <g>
                  <line
                    x1={50 + (currentHour / (timeline.length - 1)) * 780}
                    y1="30"
                    x2={50 + (currentHour / (timeline.length - 1)) * 780}
                    y2="195"
                    stroke="#FDE047"
                    strokeWidth="2"
                  />
                  <circle
                    cx={50 + (currentHour / (timeline.length - 1)) * 780}
                    cy={190 - (Math.min(400, pm25) / 400) * 150}
                    r="4"
                    fill="#EF4444"
                    stroke="#FFFFFF"
                    strokeWidth="1.5"
                  />
                </g>
              )}
            </svg>

            <div style={{ display: 'flex', justifyContent: 'center', gap: '24px', marginTop: '10px', fontSize: '11px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span style={{ width: '12px', height: '3px', background: '#EF4444', display: 'inline-block' }} />
                <span style={{ color: '#202122' }}>PM2.5 Concentration (Severe Trapping Spikes)</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span style={{ width: '12px', height: '2px', borderTop: '2px dashed #38BDF8', display: 'inline-block' }} />
                <span style={{ color: '#202122' }}>Planetary Boundary Layer Height (Thermal Lid Collapse)</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span style={{ width: '10px', height: '10px', background: '#FDE047', borderRadius: '50%', display: 'inline-block' }} />
                <span style={{ color: '#202122' }}>Current Simulation Hour (+{currentHour}h)</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
