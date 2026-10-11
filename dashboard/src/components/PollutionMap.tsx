import React, { useState, useEffect } from 'react';
import { Map, Layers, Play, Pause, Flame, Wind, Eye, Compass, X } from 'lucide-react';
import { SpatialGridData, PlumeData, PlumeEstimate } from '../types';
import { fetchSpatialGrid } from '../api';

interface PollutionMapProps {
  plumes: PlumeData | null;
}

export const PollutionMap: React.FC<PollutionMapProps> = ({ plumes }) => {
  const [variable, setVariable] = useState<'pm25' | 'pm10' | 'o3' | 'no2' | 'boundary_layer_height'>('pm25');
  const [timeStep, setTimeStep] = useState<number>(0);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [gridData, setGridData] = useState<SpatialGridData | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [selectedFire, setSelectedFire] = useState<PlumeEstimate | null>(null);

  // Fetch grid slice on variable or timeStep change
  useEffect(() => {
    let isSubscribed = true;
    setLoading(true);
    fetchSpatialGrid(variable, timeStep)
      .then((data) => {
        if (isSubscribed) setGridData(data);
      })
      .catch((err) => console.error('Grid fetch error:', err))
      .finally(() => {
        if (isSubscribed) setLoading(false);
      });
    return () => { isSubscribed = false; };
  }, [variable, timeStep]);

  // Auto-replay player
  useEffect(() => {
    let interval: any = null;
    if (isPlaying) {
      interval = setInterval(() => {
        setTimeStep((prev) => (prev >= 71 ? 0 : prev + 1));
      }, 600);
    }
    return () => clearInterval(interval);
  }, [isPlaying]);

  // Landmark reference locations in Delhi NCR
  const landmarks = [
    { name: 'Connaught Place', lat: 28.6315, lon: 77.2167 },
    { name: 'Anand Vihar', lat: 28.6508, lon: 77.3152 },
    { name: 'IGI Airport', lat: 28.5562, lon: 77.1000 },
    { name: 'Noida Sec-62', lat: 28.6280, lon: 77.3649 },
    { name: 'Gurugram CyberCity', lat: 28.4950, lon: 77.0890 }
  ];

  // Map coordinates projection to SVG (domain 28.2 to 28.9 N, 76.8 to 77.6 E)
  const latMin = 28.20;
  const latMax = 28.90;
  const lonMin = 76.80;
  const lonMax = 77.60;

  const svgWidth = 640;
  const svgHeight = 440;

  const projectX = (lon: number) => ((lon - lonMin) / (lonMax - lonMin)) * svgWidth;
  const projectY = (lat: number) => (1 - (lat - latMin) / (latMax - latMin)) * svgHeight;

  // Color mapping: Transparent for Clean/Non-contributing, Orange for Moderate, Dense Red for Severe
  const getColor = (val: number, varType: string): string => {
    if (varType === 'pm25') {
      if (val < 80) return 'transparent'; // Non-contributing / clean
      if (val < 190) return 'rgba(249, 115, 22, 0.80)'; // Moderate Orange
      return 'rgba(220, 38, 38, 0.96)'; // Severe Dense Red
    }
    if (varType === 'pm10') {
      if (val < 140) return 'transparent';
      if (val < 300) return 'rgba(249, 115, 22, 0.80)';
      return 'rgba(220, 38, 38, 0.96)';
    }
    if (varType === 'boundary_layer_height') {
      if (val < 300) return 'rgba(220, 38, 38, 0.90)';
      if (val < 600) return 'rgba(249, 115, 22, 0.75)';
      return 'transparent';
    }
    return 'rgba(249, 115, 22, 0.80)';
  };

  const activeFires = plumes?.plume_estimates || [];

  return (
    <div className="glass-card" style={{ display: 'flex', flexDirection: 'column' }}>
      <div className="card-header">
        <div className="card-title-group">
          <Map size={16} color="#06b6d4" />
          <h3>3-km D03 Spatial Dispersion Map</h3>
          <span style={{ fontSize: '0.72rem', color: '#94a3b8', marginLeft: '6px' }}>
            ({gridData?.cells?.length || 900} Active Airshed Cells)
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{ display: 'flex', background: 'rgba(15, 23, 42, 0.6)', borderRadius: '6px', padding: '2px', border: '1px solid var(--border-subtle)' }}>
            {(['pm25', 'pm10', 'no2', 'boundary_layer_height'] as const).map((v) => (
              <button
                key={v}
                onClick={() => setVariable(v)}
                style={{
                  background: variable === v ? 'rgba(6, 182, 212, 0.25)' : 'transparent',
                  color: variable === v ? '#38bdf8' : '#94a3b8',
                  border: 'none',
                  borderRadius: '4px',
                  padding: '3px 8px',
                  fontSize: '0.68rem',
                  cursor: 'pointer',
                  fontWeight: 600,
                  fontFamily: 'var(--font-mono)'
                }}
              >
                {v === 'boundary_layer_height' ? 'PBLH' : v.toUpperCase()}
              </button>
            ))}
          </div>
          <span className="provenance-tag modelled">MODELLED</span>
        </div>
      </div>

      <div className="card-body" style={{ padding: '12px 20px' }}>
        {/* Map Container */}
        <div style={{ position: 'relative', width: '100%', background: '#070b12', borderRadius: '8px', border: '1px solid rgba(255, 255, 255, 0.08)', overflow: 'hidden' }}>
          <svg viewBox={`0 0 ${svgWidth} ${svgHeight}`} style={{ width: '100%', height: 'auto', display: 'block' }}>
            <defs>
              <pattern id="gridPattern" width="32" height="32" patternUnits="userSpaceOnUse">
                <path d="M 32 0 L 0 0 0 32" fill="none" stroke="rgba(255, 255, 255, 0.03)" strokeWidth="1" />
              </pattern>
            </defs>

            <rect width={svgWidth} height={svgHeight} fill="#060a10" />

            {/* Render contributing source plumes only (Dense Red in Severe, Orange in Moderate) */}
            {gridData?.cells
              ?.filter((c) => (c.val ?? c.value ?? 0) >= 80)
              .map((c, idx) => {
                const cx = projectX(c.lon);
                const cy = projectY(c.lat);
                const val = c.val ?? c.value ?? 0;
                const color = getColor(val, variable);
                const isSevere = val >= 190;

                return (
                  <circle
                    key={idx}
                    cx={cx}
                    cy={cy}
                    r={isSevere ? 18 : 12}
                    fill={color}
                    opacity={isSevere ? 0.92 : 0.65}
                  />
                );
              })}

            {/* Wind Vector Arrows overlay */}
            {gridData?.cells?.filter((_, i) => i % 12 === 0).map((c, idx) => {
              const cx = projectX(c.lon);
              const cy = projectY(c.lat);
              const u = c.u_wind || -2.2;
              const v = c.v_wind || -1.8;
              const arrowLen = 14;
              const angle = Math.atan2(-v, u);
              const x2 = cx + arrowLen * Math.cos(angle);
              const y2 = cy + arrowLen * Math.sin(angle);

              return (
                <g key={`wind-${idx}`} opacity="0.45">
                  <line x1={cx} y1={cy} x2={x2} y2={y2} stroke="#38bdf8" strokeWidth="1.2" />
                  <circle cx={x2} cy={y2} r="1.5" fill="#38bdf8" />
                </g>
              );
            })}

            {/* Upwind Agricultural Fire Clusters (Punjab/Haryana border corridor) */}
            {activeFires.map((fire, fIdx) => {
              // Clamp lat/lon inside domain or place on northwest border edge
              const fLat = Math.min(Math.max(fire.centroid_lat, latMin + 0.05), latMax - 0.05);
              const fLon = Math.min(Math.max(fire.centroid_lon, lonMin + 0.05), lonMax - 0.05);
              const fx = projectX(fLon);
              const fy = projectY(fLat);

              return (
                <g
                  key={`fire-${fIdx}`}
                  style={{ cursor: 'pointer' }}
                  onClick={() => setSelectedFire(fire)}
                >
                  <circle cx={fx} cy={fy} r="14" fill="rgba(239, 68, 68, 0.25)" className="pulse-fire" />
                  <circle cx={fx} cy={fy} r="7" fill="#ef4444" stroke="#ffffff" strokeWidth="1.5" />
                  <text x={fx} y={fy - 12} textAnchor="middle" fill="#fca5a5" fontSize="9" fontFamily="var(--font-mono)" fontWeight="700">
                    FRP: {Math.round(fire.total_frp_mw)} MW
                  </text>
                </g>
              );
            })}

            {/* Delhi Landmark markers */}
            {landmarks.map((lm, lIdx) => {
              const lx = projectX(lm.lon);
              const ly = projectY(lm.lat);
              return (
                <g key={`lm-${lIdx}`}>
                  <circle cx={lx} cy={ly} r="3" fill="#ffffff" stroke="#06b6d4" strokeWidth="1.5" />
                  <text x={lx + 6} y={ly + 3} fill="#e2e8f0" fontSize="9" fontFamily="var(--font-sans)" fontWeight="500">
                    {lm.name}
                  </text>
                </g>
              );
            })}
          </svg>

          {/* Compass Rose */}
          <div style={{ position: 'absolute', top: '10px', right: '12px', background: 'rgba(15, 23, 42, 0.7)', padding: '6px', borderRadius: '6px', border: '1px solid var(--border-subtle)', display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.68rem', color: '#94a3b8' }}>
            <Compass size={14} color="#06b6d4" />
            <span>D03 3-km Grid</span>
          </div>

          {/* Legend */}
          <div style={{ position: 'absolute', bottom: '10px', left: '12px', background: 'rgba(15, 23, 42, 0.85)', padding: '6px 12px', borderRadius: '6px', border: '1px solid var(--border-subtle)', display: 'flex', alignItems: 'center', gap: '10px', fontSize: '0.68rem' }}>
            <span style={{ color: '#94a3b8' }}>{variable.toUpperCase()} Scale:</span>
            <div style={{ display: 'flex', gap: '4px', alignItems: 'center' }}>
              <div style={{ width: '10px', height: '10px', background: 'rgba(16, 185, 129, 0.8)', borderRadius: '2px' }} />
              <span style={{ color: '#94a3b8' }}>Low</span>
              <div style={{ width: '10px', height: '10px', background: 'rgba(234, 179, 8, 0.8)', borderRadius: '2px', marginLeft: '4px' }} />
              <div style={{ width: '10px', height: '10px', background: 'rgba(249, 115, 22, 0.8)', borderRadius: '2px' }} />
              <div style={{ width: '10px', height: '10px', background: 'rgba(239, 68, 68, 0.9)', borderRadius: '2px' }} />
              <div style={{ width: '10px', height: '10px', background: 'rgba(153, 27, 27, 0.95)', borderRadius: '2px' }} />
              <span style={{ color: '#ef4444', fontWeight: 600 }}>Severe</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '4px', marginLeft: '8px', color: '#fb7185' }}>
              <Flame size={12} />
              <span>FIRMS Fire</span>
            </div>
          </div>
        </div>

        {/* Replay Controls & Time Scrubber */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px', marginTop: '12px' }}>
          <button
            onClick={() => setIsPlaying(!isPlaying)}
            style={{
              background: isPlaying ? 'rgba(239, 68, 68, 0.2)' : 'rgba(6, 182, 212, 0.2)',
              border: isPlaying ? '1px solid #ef4444' : '1px solid #06b6d4',
              color: isPlaying ? '#f87171' : '#38bdf8',
              borderRadius: '6px',
              padding: '6px 14px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              fontSize: '0.75rem',
              fontWeight: 600
            }}
          >
            {isPlaying ? <Pause size={14} /> : <Play size={14} />}
            <span>{isPlaying ? 'Pause Replay' : 'Play 72h Loop'}</span>
          </button>

          <div style={{ flex: 1, display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.74rem', color: '#94a3b8', minWidth: '45px' }}>
              Hour {timeStep}:00
            </span>
            <input
              type="range"
              min="0"
              max="71"
              value={timeStep}
              onChange={(e) => setTimeStep(Number(e.target.value))}
              className="custom-range"
            />
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.74rem', color: '#64748b' }}>+71h</span>
          </div>
        </div>

        {/* Selected Fire Cluster Inspector Modal/Card */}
        {selectedFire && (
          <div style={{ marginTop: '10px', background: 'rgba(239, 68, 68, 0.12)', border: '1px solid rgba(239, 68, 68, 0.3)', borderRadius: '8px', padding: '10px 14px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.75rem' }}>
            <div>
              <span style={{ color: '#fca5a5', fontWeight: 700 }}>Active Crop Fire Cluster: {selectedFire.cluster_id}</span>
              <span style={{ color: '#cbd5e1', marginLeft: '12px' }}>FRP: {selectedFire.total_frp_mw} MW ({selectedFire.fire_count} hotspots)</span>
              <span style={{ color: '#cbd5e1', marginLeft: '12px' }}>Distance: {selectedFire.distance_to_delhi_km} km</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <span style={{ color: '#fbbf24', fontWeight: 600 }}>Est. Arrival: +{selectedFire.estimated_arrival_hours}h</span>
              <button
                onClick={() => setSelectedFire(null)}
                style={{ background: 'transparent', border: 'none', color: '#94a3b8', cursor: 'pointer', display: 'flex', alignItems: 'center' }}
                title="Close"
              >
                <X size={14} />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
