import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Play,
  Pause,
  RotateCcw,
  Layers,
  Wind,
  Flame,
  Download,
  Info,
  Sliders,
  Compass,
  MapPin,
  Sparkles
} from 'lucide-react';
import { SpatialGridData, PlumeData, PlumeEstimate } from '../../types';
import { fetchSpatialGrid } from '../../api';

interface DynamicCoupledHeatmapProps {
  timeStep: number;
  onTimeStepChange: (t: number) => void;
  isPlaying: boolean;
  onTogglePlay: () => void;
  plumes: PlumeData | null;
  onDownloadForecast?: () => void;
}

// Bounding Box for Delhi NCR 3-km D03 Airshed
const NCR_BOUNDS = {
  north: 28.90,
  south: 28.20,
  west: 76.80,
  east: 77.60
};

// Strategic Monitoring Receptors
const LANDMARKS = [
  { name: 'Connaught Place', lat: 28.6315, lon: 77.2167, type: 'Central Urban Core' },
  { name: 'Anand Vihar ISBT', lat: 28.6508, lon: 77.3152, type: 'East Inflow Hotspot' },
  { name: 'IGI Airport', lat: 28.5562, lon: 77.1000, type: 'South-West Corridor' },
  { name: 'Jahangirpuri', lat: 28.7300, lon: 77.1700, type: 'North Biomass Inflow' },
  { name: 'Okhla Phase-II', lat: 28.5300, lon: 77.2700, type: 'Industrial Cluster' },
  { name: 'Noida Sec-62', lat: 28.6280, lon: 77.3649, type: 'Trans-Yamuna Basin' },
  { name: 'Gurugram CyberCity', lat: 28.4950, lon: 77.0890, type: 'South NCR Hub' }
];

export const DynamicCoupledHeatmap: React.FC<DynamicCoupledHeatmapProps> = ({
  timeStep,
  onTimeStepChange,
  isPlaying,
  onTogglePlay,
  plumes,
  onDownloadForecast
}) => {
  const [variable, setVariable] = useState<'pm25' | 'pm10' | 'o3' | 'no2' | 'boundary_layer_height'>('pm25');
  const [gridData, setGridData] = useState<SpatialGridData | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [showWind, setShowWind] = useState<boolean>(true);
  const [showFires, setShowFires] = useState<boolean>(true);
  const [showLandmarks, setShowLandmarks] = useState<boolean>(true);
  const [opacity, setOpacity] = useState<number>(0.85);

  const [hoveredCell, setHoveredCell] = useState<{
    lat: number;
    lon: number;
    val: number;
    aqi: number;
    category: string;
    windSpeed: number;
    windDir: string;
    landmark?: string;
  } | null>(null);

  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  // Fetch 3-km spatial grid slice whenever variable or timeStep changes
  useEffect(() => {
    let active = true;
    setLoading(true);
    fetchSpatialGrid(variable, timeStep)
      .then((data) => {
        if (active) setGridData(data);
      })
      .catch((err) => console.error('Spatial grid fetch error:', err))
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [variable, timeStep]);

  // Color calculation across CPCB National Air Quality Index breakpoints
  const getInterpolatedRgb = useCallback((val: number, varType: string): [number, number, number] => {
    if (varType === 'boundary_layer_height') {
      // Lower PBL height is more critical (purple/dark blue inversion trapping)
      if (val < 250) return [126, 34, 206]; // Extreme Inversion Lid
      if (val < 450) return [168, 85, 247]; // Moderate Inversion
      if (val < 700) return [59, 130, 246];  // Intermediate
      return [6, 182, 212];                  // Well mixed
    }

    if (varType === 'o3') {
      if (val <= 50) return [16, 185, 129];
      if (val <= 100) return [234, 179, 8];
      if (val <= 168) return [249, 115, 22];
      return [220, 38, 38];
    }

    // Default for PM2.5 & PM10
    if (val <= 30) return [16, 185, 129];   // Good (Emerald)
    if (val <= 60) return [132, 204, 22];   // Satisfactory (Lime)
    if (val <= 120) return [234, 179, 8];   // Moderate (Amber)
    if (val <= 250) return [249, 115, 22];  // Poor (Orange)
    if (val <= 380) return [220, 38, 38];   // Very Poor (Red)
    return [127, 29, 29];                   // Severe (Maroon)
  }, []);

  // Render fluid canvas heatmap with radial Gaussian splats
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !gridData?.cells || gridData.cells.length === 0) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const width = canvas.width;
    const height = canvas.height;
    ctx.clearRect(0, 0, width, height);

    const { north, south, west, east } = NCR_BOUNDS;
    const lonSpan = east - west;
    const latSpan = north - south;

    // Background base
    ctx.fillStyle = '#0a0f1d';
    ctx.fillRect(0, 0, width, height);

    // Render continuous overlapping radial gradient splats
    gridData.cells.forEach((cell) => {
      const val = cell.value ?? (cell as any).val ?? 0;
      const x = ((cell.lon - west) / lonSpan) * width;
      const y = ((north - cell.lat) / latSpan) * height;

      const [r, g, b] = getInterpolatedRgb(val, variable);

      const radius = 32;
      const grad = ctx.createRadialGradient(x, y, 2, x, y, radius);
      grad.addColorStop(0, `rgba(${r}, ${g}, ${b}, ${0.95 * opacity})`);
      grad.addColorStop(0.35, `rgba(${r}, ${g}, ${b}, ${0.75 * opacity})`);
      grad.addColorStop(0.7, `rgba(${r}, ${g}, ${b}, ${0.35 * opacity})`);
      grad.addColorStop(1, `rgba(${r}, ${g}, ${b}, 0)`);

      ctx.fillStyle = grad;
      ctx.beginPath();
      ctx.arc(x, y, radius, 0, Math.PI * 2);
      ctx.fill();
    });

    // Subtly feather boundaries
    ctx.globalCompositeOperation = 'source-over';
  }, [gridData, variable, opacity, getInterpolatedRgb]);

  // Coordinate projection to SVG overlay
  const mapW = 900;
  const mapH = 540;
  const projX = (lon: number) => ((lon - NCR_BOUNDS.west) / (NCR_BOUNDS.east - NCR_BOUNDS.west)) * mapW;
  const projY = (lat: number) => ((NCR_BOUNDS.north - lat) / (NCR_BOUNDS.north - NCR_BOUNDS.south)) * mapH;

  const handleMouseMove = (e: React.MouseEvent<SVGSVGElement>) => {
    if (!gridData?.cells) return;
    const rect = e.currentTarget.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width) * mapW;
    const y = ((e.clientY - rect.top) / rect.height) * mapH;

    const lon = NCR_BOUNDS.west + (x / mapW) * (NCR_BOUNDS.east - NCR_BOUNDS.west);
    const lat = NCR_BOUNDS.north - (y / mapH) * (NCR_BOUNDS.north - NCR_BOUNDS.south);

    // Find closest cell
    let closest = gridData.cells[0];
    let minDist = Infinity;
    for (const c of gridData.cells) {
      const d = Math.hypot(c.lat - lat, c.lon - lon);
      if (d < minDist) {
        minDist = d;
        closest = c;
      }
    }

    if (closest && minDist < 0.12) {
      const val = closest.value ?? (closest as any).val ?? 0;
      let aqi = Math.round(val);
      if (val <= 30) aqi = Math.round((val / 30) * 50);
      else if (val <= 60) aqi = Math.round(50 + ((val - 30) / 30) * 50);
      else if (val <= 90) aqi = Math.round(100 + ((val - 60) / 30) * 100);
      else if (val <= 120) aqi = Math.round(200 + ((val - 90) / 30) * 100);
      else if (val <= 250) aqi = Math.round(300 + ((val - 120) / 130) * 100);
      else aqi = Math.min(500, Math.round(400 + ((val - 250) / 130) * 100));

      let cat = 'Severe';
      if (aqi <= 50) cat = 'Good';
      else if (aqi <= 100) cat = 'Satisfactory';
      else if (aqi <= 200) cat = 'Moderate';
      else if (aqi <= 300) cat = 'Poor';
      else if (aqi <= 400) cat = 'Very Poor';

      const u = closest.u_wind || -2.2;
      const v = closest.v_wind || -1.8;
      const ws = Math.sqrt(u * u + v * v);
      const angle = (Math.atan2(u, v) * 180) / Math.PI;
      const dirCard = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'][Math.round(((angle + 360) % 360) / 45) % 8];

      // Find nearest landmark
      let nearLm = '';
      for (const lm of LANDMARKS) {
        if (Math.hypot(lm.lat - closest.lat, lm.lon - closest.lon) < 0.05) {
          nearLm = lm.name;
          break;
        }
      }

      setHoveredCell({
        lat: closest.lat,
        lon: closest.lon,
        val,
        aqi,
        category: cat,
        windSpeed: round(ws, 1),
        windDir: dirCard,
        landmark: nearLm
      });
    }
  };

  const round = (num: number, dec = 1) => Math.round(num * Math.pow(10, dec)) / Math.pow(10, dec);

  return (
    <div
      style={{
        background: '#0B1120',
        borderRadius: '12px',
        border: '1px solid #1E293B',
        overflow: 'hidden',
        color: '#F8FAFC',
        marginBottom: '20px',
        boxShadow: '0 8px 24px rgba(0, 0, 0, 0.25)'
      }}
    >
      {/* 1. Header Toolbar with Dynamic 72-Hour Player */}
      <div
        style={{
          background: 'linear-gradient(180deg, #111827 0%, #0B1120 100%)',
          borderBottom: '1px solid #1E293B',
          padding: '12px 20px',
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '12px'
        }}
      >
        {/* Title and Airshed Badge */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div
            style={{
              background: '#0284C7',
              color: '#FFFFFF',
              padding: '4px 8px',
              borderRadius: '6px',
              fontWeight: 800,
              fontSize: '11px',
              letterSpacing: '0.05em'
            }}
          >
            DELHI NCR 3-KM AIRSHED
          </div>
          <span style={{ fontSize: '14px', fontWeight: 700, color: '#E2E8F0' }}>
            Atmospheric Coupling & Dispersion Heatmap
          </span>
          {loading && (
            <span style={{ fontSize: '11px', color: '#38BDF8', display: 'flex', alignItems: 'center', gap: '4px' }}>
              <Sparkles size={12} /> Syncing Model Step...
            </span>
          )}
        </div>

        {/* Layer Toggles */}
        <div style={{ display: 'flex', gap: '4px', background: '#1E293B', padding: '3px', borderRadius: '8px' }}>
          {(
            [
              { id: 'pm25', label: 'PM2.5 Heatmap' },
              { id: 'pm10', label: 'PM10' },
              { id: 'o3', label: 'O3 (Ozone)' },
              { id: 'boundary_layer_height', label: 'Inversion Lid (PBLH)' }
            ] as const
          ).map((layer) => (
            <button
              key={layer.id}
              onClick={() => setVariable(layer.id)}
              style={{
                background: variable === layer.id ? '#0284C7' : 'transparent',
                color: variable === layer.id ? '#FFFFFF' : '#94A3B8',
                border: 'none',
                borderRadius: '6px',
                padding: '4px 10px',
                fontSize: '11px',
                fontWeight: 600,
                cursor: 'pointer',
                transition: 'all 0.15s ease'
              }}
            >
              {layer.label}
            </button>
          ))}
        </div>

        {/* Feature Switches & On-Demand Download */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <button
            onClick={() => setShowWind(!showWind)}
            style={{
              background: showWind ? '#1E293B' : 'transparent',
              color: showWind ? '#38BDF8' : '#64748B',
              border: '1px solid #334155',
              borderRadius: '6px',
              padding: '4px 8px',
              fontSize: '11px',
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              cursor: 'pointer'
            }}
            title="Toggle Wind Streamline Vectors"
          >
            <Wind size={13} /> Wind Vectors
          </button>

          <button
            onClick={() => setShowFires(!showFires)}
            style={{
              background: showFires ? '#1E293B' : 'transparent',
              color: showFires ? '#F97316' : '#64748B',
              border: '1px solid #334155',
              borderRadius: '6px',
              padding: '4px 8px',
              fontSize: '11px',
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              cursor: 'pointer'
            }}
            title="Toggle FIRMS Active Fire Hotspots"
          >
            <Flame size={13} /> Active Fires
          </button>

          {onDownloadForecast && (
            <button
              onClick={onDownloadForecast}
              style={{
                background: '#16A34A',
                color: '#FFFFFF',
                border: 'none',
                borderRadius: '6px',
                padding: '4px 10px',
                fontSize: '11px',
                fontWeight: 700,
                display: 'flex',
                alignItems: 'center',
                gap: '5px',
                cursor: 'pointer'
              }}
              title="Download full 72-hour forecast dataset (CSV)"
            >
              <Download size={13} /> Recover/Download Data
            </button>
          )}
        </div>
      </div>

      {/* 2. Synchronized 72-Hour Timeline Player Bar */}
      <div
        style={{
          background: '#0F172A',
          borderBottom: '1px solid #1E293B',
          padding: '10px 20px',
          display: 'flex',
          alignItems: 'center',
          gap: '16px'
        }}
      >
        {/* Play / Pause / Reset */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <button
            onClick={onTogglePlay}
            style={{
              background: isPlaying ? '#DC2626' : '#0284C7',
              color: '#FFFFFF',
              border: 'none',
              borderRadius: '6px',
              width: '32px',
              height: '32px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer'
            }}
            title={isPlaying ? 'Pause 72h Forecast Playback' : 'Play 72h Dynamic Simulation'}
          >
            {isPlaying ? <Pause size={15} /> : <Play size={15} style={{ marginLeft: '2px' }} />}
          </button>

          <button
            onClick={() => onTimeStepChange(0)}
            style={{
              background: '#1E293B',
              color: '#94A3B8',
              border: 'none',
              borderRadius: '6px',
              width: '32px',
              height: '32px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer'
            }}
            title="Reset to Hour 0 (Current Time)"
          >
            <RotateCcw size={14} />
          </button>
        </div>

        {/* Current Forecast Step Indicator */}
        <div style={{ minWidth: '130px' }}>
          <div style={{ fontSize: '11px', color: '#94A3B8' }}>FORECAST TIMELINE</div>
          <div style={{ fontSize: '15px', fontWeight: 800, color: '#38BDF8', fontFamily: 'monospace' }}>
            +{timeStep}h · {timeStep === 0 ? 'Current Baseline' : `Day ${Math.floor(timeStep / 24) + 1} (${timeStep % 24}:00)`}
          </div>
        </div>

        {/* Scrubbable Range Slider */}
        <div style={{ flex: 1, display: 'flex', alignItems: 'center', gap: '10px' }}>
          <input
            type="range"
            min="0"
            max="71"
            value={timeStep}
            onChange={(e) => onTimeStepChange(parseInt(e.target.value, 10))}
            style={{
              flex: 1,
              height: '6px',
              accentColor: '#38BDF8',
              cursor: 'pointer'
            }}
          />
        </div>

        {/* Fast Jump Markers */}
        <div style={{ display: 'flex', gap: '6px' }}>
          {[
            { label: 'Now', step: 0 },
            { label: '+6h', step: 6 },
            { label: '+12h', step: 12 },
            { label: '+24h (D1)', step: 24 },
            { label: '+48h (D2)', step: 48 },
            { label: '+72h (D3)', step: 71 }
          ].map((m) => (
            <button
              key={m.label}
              onClick={() => onTimeStepChange(m.step)}
              style={{
                background: timeStep === m.step ? '#38BDF8' : '#1E293B',
                color: timeStep === m.step ? '#0F172A' : '#94A3B8',
                border: 'none',
                borderRadius: '4px',
                padding: '3px 7px',
                fontSize: '10px',
                fontWeight: 700,
                cursor: 'pointer'
              }}
            >
              {m.label}
            </button>
          ))}
        </div>
      </div>

      {/* 3. Main Map Surface: Fluid Canvas + SVG Overlays */}
      <div style={{ position: 'relative', width: '100%', height: '540px', background: '#060a12' }}>
        {/* Underlying Fluid Heatmap Canvas */}
        <canvas
          ref={canvasRef}
          width={mapW}
          height={mapH}
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            width: '100%',
            height: '100%',
            display: 'block'
          }}
        />

        {/* Interactive SVG Vector Layer (Wind, Landmarks, Fires, Cursor) */}
        <svg
          viewBox={`0 0 ${mapW} ${mapH}`}
          onMouseMove={handleMouseMove}
          onMouseLeave={() => setHoveredCell(null)}
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            width: '100%',
            height: '100%',
            cursor: 'crosshair',
            userSelect: 'none'
          }}
        >
          {/* Spatial Grid Border & Ticks */}
          <rect
            x="0"
            y="0"
            width={mapW}
            height={mapH}
            fill="none"
            stroke="rgba(255, 255, 255, 0.08)"
            strokeWidth="2"
          />

          {/* Wind Streamline Vector Overlay */}
          {showWind &&
            gridData?.cells
              ?.filter((_, i) => i % 14 === 0)
              .map((c, idx) => {
                const cx = projX(c.lon);
                const cy = projY(c.lat);
                const u = c.u_wind || -2.2;
                const v = c.v_wind || -1.8;
                const len = 16;
                const angle = Math.atan2(-v, u);
                const x2 = cx + len * Math.cos(angle);
                const y2 = cy + len * Math.sin(angle);

                return (
                  <g key={`w-${idx}`} opacity="0.55">
                    <line x1={cx} y1={cy} x2={x2} y2={y2} stroke="#38BDF8" strokeWidth="1.3" />
                    <circle cx={x2} cy={y2} r="1.6" fill="#38BDF8" />
                  </g>
                );
              })}

          {/* Active FIRMS Fire Hotspots */}
          {showFires &&
            (plumes?.plume_estimates || []).map((fire, idx) => {
              const fx = projX(fire.centroid_lon);
              const fy = projY(fire.centroid_lat);
              if (fx < 0 || fx > mapW || fy < 0 || fy > mapH) return null;

              return (
                <g key={`fire-${idx}`} transform={`translate(${fx}, ${fy})`}>
                  <circle r="12" fill="rgba(239, 68, 68, 0.25)" stroke="#EF4444" strokeWidth="1.5">
                    <animate attributeName="r" values="8;16;8" dur="2s" repeatCount="indefinite" />
                    <animate attributeName="opacity" values="0.8;0.2;0.8" dur="2s" repeatCount="indefinite" />
                  </circle>
                  <circle r="4" fill="#F97316" />
                  <text y="-8" textAnchor="middle" fill="#FDE047" fontSize="10" fontWeight="bold">
                    {fire.total_frp_mw} MW
                  </text>
                </g>
              );
            })}

          {/* Key Strategic Monitoring Stations */}
          {showLandmarks &&
            LANDMARKS.map((lm) => {
              const lx = projX(lm.lon);
              const ly = projY(lm.lat);

              return (
                <g key={lm.name} transform={`translate(${lx}, ${ly})`}>
                  <circle r="4" fill="#FFFFFF" stroke="#0284C7" strokeWidth="2" />
                  <rect
                    x="-40"
                    y="-22"
                    width="80"
                    height="16"
                    rx="3"
                    fill="rgba(15, 23, 42, 0.85)"
                    stroke="rgba(255, 255, 255, 0.15)"
                  />
                  <text
                    x="0"
                    y="-11"
                    textAnchor="middle"
                    fill="#E2E8F0"
                    fontSize="9"
                    fontWeight="600"
                    fontFamily="sans-serif"
                  >
                    {lm.name}
                  </text>
                </g>
              );
            })}
        </svg>

        {/* 4. Live Inspector Tooltip Overlay */}
        {hoveredCell && (
          <div
            style={{
              position: 'absolute',
              bottom: '16px',
              right: '16px',
              background: 'rgba(15, 23, 42, 0.92)',
              backdropFilter: 'blur(8px)',
              border: '1px solid rgba(255, 255, 255, 0.12)',
              borderRadius: '8px',
              padding: '12px 16px',
              color: '#FFFFFF',
              boxShadow: '0 4px 16px rgba(0,0,0,0.5)',
              minWidth: '220px',
              pointerEvents: 'none'
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
              <span style={{ fontSize: '11px', color: '#94A3B8' }}>AIRSHED CELL RECEPTOR</span>
              <span
                style={{
                  fontSize: '10px',
                  fontWeight: 700,
                  padding: '2px 6px',
                  borderRadius: '4px',
                  background:
                    hoveredCell.category === 'Severe'
                      ? '#7F1D1D'
                      : hoveredCell.category === 'Very Poor'
                      ? '#991B1B'
                      : hoveredCell.category === 'Poor'
                      ? '#C2410C'
                      : '#16A34A',
                  color: '#FFFFFF'
                }}
              >
                {hoveredCell.category.toUpperCase()}
              </span>
            </div>

            <div style={{ fontSize: '14px', fontWeight: 800, color: '#38BDF8', marginBottom: '6px' }}>
              {hoveredCell.landmark || `${hoveredCell.lat.toFixed(3)}°N, ${hoveredCell.lon.toFixed(3)}°E`}
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', fontSize: '11px' }}>
              <div>
                <span style={{ color: '#94A3B8' }}>{variable.toUpperCase()}: </span>
                <strong>
                  {hoveredCell.val} {variable === 'boundary_layer_height' ? 'm' : 'µg/m³'}
                </strong>
              </div>
              <div>
                <span style={{ color: '#94A3B8' }}>NAQI: </span>
                <strong style={{ color: '#F87171' }}>{hoveredCell.aqi}</strong>
              </div>
              <div>
                <span style={{ color: '#94A3B8' }}>Wind Speed: </span>
                <strong>{hoveredCell.windSpeed} m/s</strong>
              </div>
              <div>
                <span style={{ color: '#94A3B8' }}>Wind Heading: </span>
                <strong>{hoveredCell.windDir}</strong>
              </div>
            </div>
          </div>
        )}

        {/* 5. Fluid Heatmap Legend */}
        <div
          style={{
            position: 'absolute',
            bottom: '16px',
            left: '16px',
            background: 'rgba(15, 23, 42, 0.88)',
            backdropFilter: 'blur(6px)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            borderRadius: '6px',
            padding: '8px 12px',
            color: '#FFFFFF',
            fontSize: '11px'
          }}
        >
          <div style={{ fontWeight: 700, marginBottom: '6px', color: '#94A3B8' }}>
            {variable === 'boundary_layer_height'
              ? 'BOUNDARY LAYER HEIGHT (PBLH)'
              : `${variable.toUpperCase()} DISPERSION CONCENTRATION`}
          </div>

          <div
            style={{
              width: '180px',
              height: '8px',
              borderRadius: '4px',
              background:
                variable === 'boundary_layer_height'
                  ? 'linear-gradient(to right, #7E22CE, #A855F7, #3B82F6, #06B6D4)'
                  : 'linear-gradient(to right, #10B981, #84CC16, #EAB308, #F97316, #DC2626, #7F1D1D)'
            }}
          />

          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              fontSize: '9px',
              color: '#94A3B8',
              marginTop: '4px'
            }}
          >
            {variable === 'boundary_layer_height' ? (
              <>
                <span>150 m (Trapping)</span>
                <span>500 m</span>
                <span>1000 m (Mixed)</span>
              </>
            ) : (
              <>
                <span>0</span>
                <span>60</span>
                <span>120</span>
                <span>250</span>
                <span>380+ µg/m³</span>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
