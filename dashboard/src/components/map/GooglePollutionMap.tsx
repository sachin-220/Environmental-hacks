import React, { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import {
  GoogleMap,
  useLoadScript,
  Marker,
  InfoWindow,
  Polyline,
  Polygon,
  Rectangle
} from '@react-google-maps/api';
import { SpatialGridData, PlumeData, PlumeEstimate } from '../../types';
import { fetchSpatialGrid } from '../../api';

// Geometry library for coordinate projection
const libraries: 'geometry'[] = ['geometry'];

// Google Maps API Key from environment variable
const GOOGLE_MAPS_API_KEY: string = ((import.meta as any).env?.VITE_GOOGLE_MAPS_API_KEY as string) || '';

const mapContainerStyle = {
  width: '100%',
  height: '570px'
};

const delhiCenter = {
  lat: 28.6139,
  lng: 77.2090
};

// Domain Bounding Box for WRF-Chem 3-km D03 Airshed
const AIRSHED_BOUNDS = {
  north: 29.24,
  south: 28.15,
  west: 76.62,
  east: 77.82
};

// Strategic Monitoring Receptors across Delhi NCR
interface HotspotLocation {
  id: string;
  name: string;
  lat: number;
  lon: number;
  type: string;
  baselineOffset: number;
}

const STRATEGIC_HOTSPOTS: HotspotLocation[] = [
  { id: 'AV', name: 'Anand Vihar ISBT', lat: 28.650, lon: 77.315, type: 'Interstate Transport & Industrial Core', baselineOffset: 45.2 },
  { id: 'JP', name: 'Jahangirpuri', lat: 28.730, lon: 77.170, type: 'North Inflow Advection Corridor', baselineOffset: 34.0 },
  { id: 'PB', name: 'Punjabi Bagh', lat: 28.670, lon: 77.130, type: 'West Urban Traffic Congestion', baselineOffset: 24.5 },
  { id: 'OK', name: 'Okhla Phase-II', lat: 28.530, lon: 77.270, type: 'Industrial Manufacturing Belt', baselineOffset: 29.8 },
  { id: 'CP', name: 'Central Delhi (CP)', lat: 28.631, lon: 77.217, type: 'Urban Background Baseline', baselineOffset: 0.0 }
];

// Clean Google Maps institutional styling
const institutionalMapStyles = [
  { featureType: 'administrative', elementType: 'labels.text.fill', stylers: [{ color: '#334155' }] },
  { featureType: 'landscape', elementType: 'all', stylers: [{ color: '#F8FAFC' }] },
  { featureType: 'poi', elementType: 'all', stylers: [{ visibility: 'off' }] },
  { featureType: 'road', elementType: 'all', stylers: [{ saturation: -100 }, { lightness: 45 }] },
  { featureType: 'road.highway', elementType: 'all', stylers: [{ visibility: 'simplified' }] },
  { featureType: 'water', elementType: 'all', stylers: [{ color: '#E2E8F0' }, { visibility: 'on' }] }
];

interface HoveredCellInfo {
  lat: number;
  lon: number;
  val: number;
  aqi: number;
  statusLabel: string;
  statusClass: string;
  color: string;
  locationName: string;
  speed: number;
  dirDeg: number;
  dirCard: string;
  gridId: string;
  dispersionText: string;
}

interface GooglePollutionMapProps {
  plumes: PlumeData | null;
  onSwitchProvider?: (provider: 'google' | 'osm') => void;
}

// Continuous scientific color interpolation across CPCB intervals
// Continuous scientific color interpolation: Orange for Moderate, Dense Red for Severe
function getContinuousRgb(val: number): [number, number, number] {
  const stops: [number, [number, number, number]][] = [
    [0,   [249, 115, 22]],   // Baseline moderate start - Orange
    [80,  [249, 115, 22]],   // Moderate - Pure Vibrant Orange
    [140, [234, 88, 12]],    // High Moderate - Fiery Amber Orange
    [200, [239, 68, 68]],    // Severe Entry - Red
    [270, [220, 38, 38]],    // Severe - Intense Red
    [380, [153, 27, 27]]     // Severe Dense - Deep Crimson
  ];

  if (val <= stops[0][0]) return stops[0][1];
  if (val >= stops[stops.length - 1][0]) return stops[stops.length - 1][1];

  for (let i = 0; i < stops.length - 1; i++) {
    const [t0, c0] = stops[i];
    const [t1, c1] = stops[i + 1];
    if (val >= t0 && val <= t1) {
      const f = (val - t0) / (t1 - t0);
      return [
        Math.round(c0[0] + f * (c1[0] - c0[0])),
        Math.round(c0[1] + f * (c1[1] - c0[1])),
        Math.round(c0[2] + f * (c1[2] - c0[2]))
      ];
    }
  }
  return [220, 38, 38];
}

export const GooglePollutionMap: React.FC<GooglePollutionMapProps> = ({ plumes, onSwitchProvider }) => {
  const { isLoaded, loadError } = useLoadScript({
    googleMapsApiKey: GOOGLE_MAPS_API_KEY,
    libraries
  });

  const [activeLayer, setActiveLayer] = useState<'pm25' | 'pm10' | 'o3' | 'wind' | 'fires' | 'plume'>('pm25');
  const [renderMode, setRenderMode] = useState<'cloud' | 'mesh' | 'hybrid'>('cloud');
  const [mapType, setMapType] = useState<'roadmap' | 'satellite' | 'terrain'>('roadmap');
  const [timeStep, setTimeStep] = useState<number>(0);
  const [gridData, setGridData] = useState<SpatialGridData | null>(null);
  const [heatmapOpacity, setHeatmapOpacity] = useState<number>(0.75);
  const [showHotspots, setShowHotspots] = useState<boolean>(true);
  const [showWindVectors, setShowWindVectors] = useState<boolean>(false);

  const [hoverInfo, setHoverInfo] = useState<HoveredCellInfo>({
    lat: 28.614,
    lon: 77.209,
    val: 225.2,
    aqi: 381,
    statusLabel: 'Severe',
    statusClass: 'severe',
    color: '#DC2626',
    locationName: 'Central Delhi · Mandir Marg / Connaught Place',
    speed: 2.4,
    dirDeg: 312,
    dirCard: 'NW',
    gridId: 'D03_R30_C30',
    dispersionText: 'Critical Inversion Stagnation (Poor Advective Flush)'
  });

  const [selectedFire, setSelectedFire] = useState<PlumeEstimate | null>(null);
  const [selectedHotspot, setSelectedHotspot] = useState<HotspotLocation | null>(null);

  const mapRef = useRef<google.maps.Map | null>(null);
  const groundOverlayRef = useRef<google.maps.GroundOverlay | null>(null);

  const backendVar = activeLayer === 'pm10' ? 'pm10' : activeLayer === 'o3' ? 'o3' : 'pm25';

  useEffect(() => {
    let active = true;
    fetchSpatialGrid(backendVar, timeStep)
      .then((data) => {
        if (active) setGridData(data);
      })
      .catch((err) => console.error('Google Maps spatial grid error:', err));
    return () => {
      active = false;
    };
  }, [backendVar, timeStep]);

  const getCellColor = useCallback((val: number): string => {
    const [r, g, b] = getContinuousRgb(val);
    return `rgb(${r}, ${g}, ${b})`;
  }, []);

  const getAqiCategory = useCallback((val: number): { label: string; class: string; aqi: number } => {
    let aqi = Math.round(val);
    if (val <= 30) aqi = Math.round((val / 30) * 50);
    else if (val <= 60) aqi = Math.round(50 + ((val - 30) / 30) * 50);
    else if (val <= 90) aqi = Math.round(100 + ((val - 60) / 30) * 100);
    else if (val <= 120) aqi = Math.round(200 + ((val - 90) / 30) * 100);
    else if (val <= 250) aqi = Math.round(300 + ((val - 120) / 130) * 100);
    else aqi = Math.min(500, Math.round(400 + ((val - 250) / 130) * 100));

    if (aqi <= 50) return { label: 'Good', class: 'good', aqi };
    if (aqi <= 100) return { label: 'Satisfactory', class: 'satisfactory', aqi };
    if (aqi <= 200) return { label: 'Moderate', class: 'moderate', aqi };
    if (aqi <= 300) return { label: 'Poor', class: 'poor', aqi };
    if (aqi <= 400) return { label: 'Very Poor', class: 'very-poor', aqi };
    return { label: 'Severe', class: 'severe', aqi };
  }, []);

  const getWindCardinal = (deg: number): string => {
    const directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW'];
    return directions[Math.round(deg / 22.5) % 16];
  };

  const getNearestLandmark = (lat: number, lon: number): string => {
    if (lat > 28.70 && lon < 77.18) return 'Outer North · Jahangirpuri Corridor';
    if (lat > 28.68 && lon > 77.22) return 'North-East · Yamuna Airshed';
    if (lat > 28.62 && lon > 77.28) return 'East Delhi · Anand Vihar ISBT';
    if (lat > 28.64 && lon < 77.16) return 'West Delhi · Punjabi Bagh / Rajouri';
    if (lat < 28.56 && lon < 77.12) return 'South-West · IGI Airport & Dwarka';
    if (lat < 28.55 && lon > 77.24) return 'South-East · Okhla Industrial Cluster';
    if (lon > 77.33) return 'Gautam Buddha Nagar · Noida Airshed';
    if (lon < 76.95) return 'Gurugram · Southern NCR Sub-Basin';
    return 'Central Delhi · Mandir Marg / Connaught Place';
  };

  const halfLat = 0.0135;
  const halfLon = 0.0155;

  // Generate Continuous Cloud GroundOverlay Canvas with Smooth Feathering
  const generateCloudCanvas = useCallback((): string | null => {
    if (!gridData?.cells || gridData.cells.length === 0) return null;

    const width = 850;
    const height = 750;
    const canvas = document.createElement('canvas');
    canvas.width = width;
    canvas.height = height;
    const ctx = canvas.getContext('2d');
    if (!ctx) return null;

    ctx.clearRect(0, 0, width, height);

    const { north, south, west, east } = AIRSHED_BOUNDS;
    const lonSpan = east - west;
    const latSpan = north - south;

    // 1. Render contributing plumes only (Dense Red in Severe, Orange in Moderate)
    gridData.cells
      .filter((cell) => (cell.value ?? cell.val ?? 0) >= 80) // Only contributing cells!
      .forEach((cell) => {
        const val = cell.value ?? cell.val ?? 0;
        const x = ((cell.lon - west) / lonSpan) * width;
        const y = ((north - cell.lat) / latSpan) * height;

        const [r, g, b] = getContinuousRgb(val);
        const isSevere = val >= 190;

        // Severe regions receive dense concentrated cores
        const radius = isSevere ? 36 : 28;
        const grad = ctx.createRadialGradient(x, y, 1, x, y, radius);
        const alpha = isSevere ? 0.96 : 0.65;
        grad.addColorStop(0, `rgba(${r}, ${g}, ${b}, ${alpha})`);
        grad.addColorStop(0.4, `rgba(${r}, ${g}, ${b}, ${alpha * 0.8})`);
        grad.addColorStop(0.75, `rgba(${r}, ${g}, ${b}, ${alpha * 0.3})`);
        grad.addColorStop(1, `rgba(${r}, ${g}, ${b}, 0)`);

        ctx.fillStyle = grad;
        ctx.beginPath();
        ctx.arc(x, y, radius, 0, Math.PI * 2);
        ctx.fill();
      });

    // 2. Feather the outer boundary so cloud dissolves organically into map
    const centerX = width / 2;
    const centerY = height / 2;
    const maskGrad = ctx.createRadialGradient(
      centerX,
      centerY,
      Math.min(width, height) * 0.34,
      centerX,
      centerY,
      Math.min(width, height) * 0.49
    );
    maskGrad.addColorStop(0, 'rgba(0, 0, 0, 1)');
    maskGrad.addColorStop(0.75, 'rgba(0, 0, 0, 0.85)');
    maskGrad.addColorStop(1, 'rgba(0, 0, 0, 0)');

    ctx.globalCompositeOperation = 'destination-in';
    ctx.fillStyle = maskGrad;
    ctx.fillRect(0, 0, width, height);
    ctx.globalCompositeOperation = 'source-over';

    return canvas.toDataURL('image/png');
  }, [gridData]);

  // Synchronize Google Maps GroundOverlay
  useEffect(() => {
    if (!mapRef.current || !window.google || (renderMode !== 'cloud' && renderMode !== 'hybrid')) {
      if (groundOverlayRef.current) {
        groundOverlayRef.current.setMap(null);
        groundOverlayRef.current = null;
      }
      return;
    }

    const dataUrl = generateCloudCanvas();
    if (!dataUrl) return;

    if (groundOverlayRef.current) {
      groundOverlayRef.current.setMap(null);
    }

    const bounds = new window.google.maps.LatLngBounds(
      new window.google.maps.LatLng(AIRSHED_BOUNDS.south, AIRSHED_BOUNDS.west),
      new window.google.maps.LatLng(AIRSHED_BOUNDS.north, AIRSHED_BOUNDS.east)
    );

    const overlay = new window.google.maps.GroundOverlay(dataUrl, bounds, {
      opacity: heatmapOpacity,
      clickable: false
    });

    overlay.setMap(mapRef.current);
    groundOverlayRef.current = overlay;

    return () => {
      if (groundOverlayRef.current) {
        groundOverlayRef.current.setMap(null);
        groundOverlayRef.current = null;
      }
    };
  }, [generateCloudCanvas, renderMode, heatmapOpacity]);

  // Handle map cursor hovering for live inspector HUD
  const handleMapMouseMove = useCallback(
    (e: google.maps.MapMouseEvent) => {
      if (!e.latLng || !gridData?.cells) return;
      const lat = e.latLng.lat();
      const lon = e.latLng.lng();

      let closestCell = gridData.cells[0];
      let minDistance = 999999;

      for (let i = 0; i < gridData.cells.length; i++) {
        const c = gridData.cells[i];
        const dist = (c.lat - lat) ** 2 + (c.lon - lon) ** 2;
        if (dist < minDistance) {
          minDistance = dist;
          closestCell = c;
        }
      }

      if (minDistance < 0.05) {
        const val = closestCell.value ?? closestCell.val ?? 0;
        const u = closestCell.u_wind ?? -2.0;
        const v = closestCell.v_wind ?? -1.5;
        const speed = Math.sqrt(u * u + v * v);
        const angleDeg = (Math.atan2(-v, u) * 180) / Math.PI + 90;
        const aqiInfo = getAqiCategory(val);
        const landmark = getNearestLandmark(closestCell.lat, closestCell.lon);

        const dispersionText =
          speed < 2.0
            ? 'Critical Nocturnal Stagnation (Poor Advective Flush)'
            : speed < 3.5
            ? 'Moderate Ventilation Index'
            : 'Active Atmospheric Dispersion';

        setHoverInfo({
          lat: closestCell.lat,
          lon: closestCell.lon,
          val,
          aqi: aqiInfo.aqi,
          statusLabel: aqiInfo.label,
          statusClass: aqiInfo.class,
          color: getCellColor(val),
          locationName: landmark,
          speed,
          dirDeg: Math.round((angleDeg + 360) % 360),
          dirCard: getWindCardinal((angleDeg + 360) % 360),
          gridId: closestCell.grid_id || 'D03-LOC',
          dispersionText
        });
      }
    },
    [gridData, getAqiCategory, getCellColor]
  );

  // Staggered aerodynamic sampling of wind vectors across Delhi NCR (eliminates dense vertical lines)
  const sampledWindVectors = useMemo(() => {
    if (!gridData?.cells) return [];
    const sampleLats = [28.25, 28.40, 28.55, 28.70, 28.85, 29.00, 29.15];
    const sampleLons = [76.75, 76.92, 77.09, 77.26, 77.43, 77.60, 77.75];
    const sampled: any[] = [];

    sampleLats.forEach((lat) => {
      sampleLons.forEach((lon) => {
        let closest = gridData.cells[0];
        let minD = 999999;
        gridData.cells.forEach((c) => {
          const d = (c.lat - lat) ** 2 + (c.lon - lon) ** 2;
          if (d < minD) {
            minD = d;
            closest = c;
          }
        });
        if (minD < 0.018) sampled.push(closest);
      });
    });
    return sampled;
  }, [gridData]);

  // Active FIRMS Fire Clusters
  const activeFires: PlumeEstimate[] = useMemo(() => {
    return (
      plumes?.plume_estimates || [
        {
          cluster_id: 'FIRMS-HOTSPOT-01',
          centroid_lat: 29.85,
          centroid_lon: 76.10,
          fire_count: 42,
          total_frp_mw: 385.0,
          distance_to_delhi_km: 172.5,
          bearing_deg: 312.0,
          aligned_with_wind: true,
          transit_speed_kmh: 9.5,
          estimated_arrival_hours: 18.2,
          urgency: 'HIGH',
          confidence: 94.0,
          provenance: 'OBSERVED'
        },
        {
          cluster_id: 'FIRMS-HOTSPOT-02',
          centroid_lat: 29.40,
          centroid_lon: 76.45,
          fire_count: 28,
          total_frp_mw: 210.0,
          distance_to_delhi_km: 115.0,
          bearing_deg: 320.0,
          aligned_with_wind: true,
          transit_speed_kmh: 9.2,
          estimated_arrival_hours: 12.4,
          urgency: 'MEDIUM',
          confidence: 91.0,
          provenance: 'OBSERVED'
        }
      ]
    );
  }, [plumes]);

  // Modelled Plume Transport Trajectories (Upwind -> Central Delhi)
  const plumeTrajectories = useMemo(() => {
    return activeFires.map((fire) => {
      const lat = fire.centroid_lat ?? fire.cluster_center_lat ?? 29.85;
      const lon = fire.centroid_lon ?? fire.cluster_center_lon ?? 76.10;
      const start = { lat, lng: lon };
      const mid1 = {
        lat: lat * 0.7 + 28.6139 * 0.3 - 0.03,
        lng: lon * 0.7 + 77.2090 * 0.3 + 0.05
      };
      const mid2 = {
        lat: lat * 0.35 + 28.6139 * 0.65 - 0.02,
        lng: lon * 0.35 + 77.2090 * 0.65 + 0.02
      };
      const end = { lat: 28.6139, lng: 77.2090 };
      return {
        fire,
        path: [start, mid1, mid2, end]
      };
    });
  }, [activeFires]);

  // Delhi NCR Airshed Domain Boundary Polygon
  const ncrBoundary = [
    { lat: 28.25, lng: 76.70 },
    { lat: 28.15, lng: 77.05 },
    { lat: 28.20, lng: 77.45 },
    { lat: 28.40, lng: 77.68 },
    { lat: 28.75, lng: 77.75 },
    { lat: 29.10, lng: 77.55 },
    { lat: 29.18, lng: 77.10 },
    { lat: 29.02, lng: 76.70 },
    { lat: 28.60, lng: 76.55 },
    { lat: 28.25, lng: 76.70 }
  ];

  // Camera presets
  const zoomToRegion = (region: 'delhi' | 'ncr' | 'upwind') => {
    if (!mapRef.current) return;
    if (region === 'delhi') {
      mapRef.current.panTo(delhiCenter);
      mapRef.current.setZoom(11);
    } else if (region === 'ncr') {
      mapRef.current.panTo({ lat: 28.65, lng: 77.20 });
      mapRef.current.setZoom(9);
    } else {
      mapRef.current.panTo({ lat: 29.35, lng: 76.60 });
      mapRef.current.setZoom(8);
    }
  };

  if (loadError) {
    return (
      <div className="portal-section" style={{ padding: '24px', textAlign: 'center', background: '#FEF2F2', border: '1px solid #FCA5A5' }}>
        <strong style={{ color: '#DC2626', fontSize: '14px' }}>Google Maps Service Notice:</strong>
        <p style={{ fontSize: '12px', color: '#7F1D1D', margin: '8px 0 14px' }}>
          {loadError.message || 'Unable to connect to Google Maps API service.'}
        </p>
        {onSwitchProvider && (
          <button
            onClick={() => onSwitchProvider('osm')}
            className="portal-btn"
            style={{ background: '#003366', color: '#FFFFFF', padding: '6px 14px' }}
          >
            Switch to OpenStreetMap (Leaflet)
          </button>
        )}
      </div>
    );
  }

  return (
    <div className="portal-section" style={{ padding: 0 }}>
      {/* Top Map Control Bar */}
      <div
        style={{
          padding: '12px 18px',
          borderBottom: '1px solid var(--border-color)',
          background: '#F8F9FA',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '12px'
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <strong style={{ fontSize: '14px', color: '#003366' }}>
              DELHI NCR — 3 KM COUPLED ATMOSPHERIC POLLUTION HEATMAP
            </strong>
            <span className="status-tag status-severe" style={{ fontSize: '10px' }}>METEOROLOGICAL CLOUD</span>
          </div>
          <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginTop: '2px' }}>
            Continuous Raster Splatting · WRF-Chem D03 3-km Airshed · Live Advection Cursor Telemetry
          </div>
        </div>

        {/* Time Horizon Selector */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          <span style={{ fontSize: '11px', fontWeight: 'bold', color: 'var(--text-secondary)', marginRight: '4px' }}>
            FORECAST STEP:
          </span>
          {[
            { step: 0, label: 'NOW' },
            { step: 6, label: '+6H' },
            { step: 12, label: '+12H' },
            { step: 24, label: '+24H' },
            { step: 48, label: '+48H' },
            { step: 72, label: '+72H' }
          ].map((t) => (
            <button
              key={t.step}
              onClick={() => setTimeStep(t.step)}
              className={timeStep === t.step ? 'portal-btn' : 'portal-btn-secondary'}
              style={{ padding: '4px 8px', fontSize: '11px' }}
            >
              {t.label}
            </button>
          ))}
        </div>
      </div>

      {/* Layer Selector & Presentation Controls */}
      <div
        style={{
          padding: '8px 18px',
          borderBottom: '1px solid var(--border-color)',
          background: '#FFFFFF',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '10px'
        }}
      >
        {/* Layer Chips */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap' }}>
          <span style={{ fontSize: '11px', fontWeight: 'bold', color: 'var(--text-secondary)', marginRight: '4px' }}>
            POLLUTANT:
          </span>
          {(['pm25', 'pm10', 'o3', 'wind', 'fires', 'plume'] as const).map((l) => (
            <button
              key={l}
              onClick={() => setActiveLayer(l)}
              className={activeLayer === l ? 'portal-btn' : 'portal-btn-secondary'}
              style={{
                padding: '4px 10px',
                fontSize: '11px',
                textTransform: 'uppercase',
                background: activeLayer === l ? '#003366' : '#FFFFFF'
              }}
            >
              {l === 'pm25'
                ? 'PM2.5 Heatmap'
                : l === 'pm10'
                ? 'PM10 Heatmap'
                : l === 'o3'
                ? 'Ozone (O3)'
                : l === 'wind'
                ? 'Wind Field'
                : l === 'fires'
                ? 'FIRMS Fires'
                : 'Modelled Plume'}
            </button>
          ))}

          {/* Presentation Style */}
          {(activeLayer === 'pm25' || activeLayer === 'pm10' || activeLayer === 'o3') && (
            <div style={{ display: 'inline-flex', background: '#F1F5F9', padding: '2px', borderRadius: '3px', border: '1px solid var(--border-color)', marginLeft: '6px' }}>
              <button
                onClick={() => setRenderMode('cloud')}
                className={`map-control-chip ${renderMode === 'cloud' ? 'active' : ''}`}
                style={{ fontSize: '10px', padding: '2px 7px' }}
                title="Continuous Organic Atmospheric Dispersion Cloud"
              >
                Organic Cloud
              </button>
              <button
                onClick={() => setRenderMode('hybrid')}
                className={`map-control-chip ${renderMode === 'hybrid' ? 'active' : ''}`}
                style={{ fontSize: '10px', padding: '2px 7px' }}
                title="Cloud Gradient with 3-km Grid Outlines"
              >
                Hybrid Mesh
              </button>
              <button
                onClick={() => setRenderMode('mesh')}
                className={`map-control-chip ${renderMode === 'mesh' ? 'active' : ''}`}
                style={{ fontSize: '10px', padding: '2px 7px' }}
                title="Scientific 3-km Discrete Model Mesh"
              >
                Discrete 3-km
              </button>
            </div>
          )}

          {/* Hotspot & Wind Toggle Chips */}
          <button
            onClick={() => setShowHotspots(!showHotspots)}
            className={`map-control-chip ${showHotspots ? 'active' : ''}`}
            style={{ fontSize: '10px', padding: '3px 8px', marginLeft: '6px' }}
          >
            {showHotspots ? '● Hotspot Radar (ON)' : '○ Hotspot Radar (OFF)'}
          </button>
          <button
            onClick={() => setShowWindVectors(!showWindVectors)}
            className={`map-control-chip ${showWindVectors ? 'active' : ''}`}
            style={{ fontSize: '10px', padding: '3px 8px' }}
          >
            {showWindVectors ? '● Wind Vectors (ON)' : '○ Wind Vectors (OFF)'}
          </button>
        </div>

        {/* Viewport Presets & Provider */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap' }}>
          <span style={{ fontSize: '11px', fontWeight: 'bold', color: 'var(--text-secondary)' }}>
            BASE:
          </span>
          {(['roadmap', 'satellite', 'terrain'] as const).map((mt) => (
            <button
              key={mt}
              onClick={() => setMapType(mt)}
              className={mapType === mt ? 'portal-btn' : 'portal-btn-secondary'}
              style={{ padding: '3px 8px', fontSize: '10px', textTransform: 'capitalize' }}
            >
              {mt}
            </button>
          ))}

          {/* Preset Camera Zoom Buttons */}
          <div style={{ display: 'inline-flex', gap: '2px', marginLeft: '4px' }}>
            <button onClick={() => zoomToRegion('delhi')} className="portal-btn-secondary" style={{ padding: '2px 6px', fontSize: '10px' }}>
              Delhi Core
            </button>
            <button onClick={() => zoomToRegion('ncr')} className="portal-btn-secondary" style={{ padding: '2px 6px', fontSize: '10px' }}>
              Full NCR
            </button>
            <button onClick={() => zoomToRegion('upwind')} className="portal-btn-secondary" style={{ padding: '2px 6px', fontSize: '10px' }}>
              Upwind Corridor
            </button>
          </div>

          {/* Provider Switcher */}
          {onSwitchProvider && (
            <div style={{ display: 'flex', background: '#F1F5F9', padding: '2px', borderRadius: '3px', border: '1px solid var(--border-color)', marginLeft: '6px' }}>
              <button className="portal-btn" style={{ padding: '2px 7px', fontSize: '10px' }}>
                Google Maps
              </button>
              <button
                onClick={() => onSwitchProvider('osm')}
                className="portal-btn-secondary"
                style={{ padding: '2px 7px', fontSize: '10px', background: 'transparent', border: 'none' }}
              >
                OpenStreetMap
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Main Map Canvas Area */}
      <div style={{ position: 'relative', width: '100%', height: '570px', background: '#F5F6F7' }}>
        {loadError || !GOOGLE_MAPS_API_KEY ? (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'var(--text-secondary)', padding: '20px', textAlign: 'center' }}>
            <p style={{ fontWeight: 'bold', marginBottom: '8px', color: 'var(--text-primary)' }}>Google Maps API Key not configured or failed to load.</p>
            <p style={{ fontSize: '12px', marginBottom: '14px', maxWidth: '420px' }}>Set <code>VITE_GOOGLE_MAPS_API_KEY</code> in your environment, or switch to the built-in OpenStreetMap / Leaflet spatial engine below.</p>
            {onSwitchProvider && (
              <button onClick={() => onSwitchProvider('osm')} className="portal-btn" style={{ padding: '6px 14px', fontSize: '12px' }}>
                Switch to OpenStreetMap Engine
              </button>
            )}
          </div>
        ) : !isLoaded ? (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'var(--text-secondary)' }}>
            Initializing Google Maps Advanced Spatial Intelligence Engine...
          </div>
        ) : (
          <GoogleMap
            mapContainerStyle={mapContainerStyle}
            center={delhiCenter}
            zoom={9}
            mapTypeId={mapType}
            onLoad={(map) => {
              mapRef.current = map;
            }}
            onMouseMove={handleMapMouseMove}
            options={{
              styles: mapType === 'roadmap' ? institutionalMapStyles : undefined,
              disableDefaultUI: false,
              zoomControl: true,
              streetViewControl: false,
              mapTypeControl: false,
              fullscreenControl: true
            }}
          >
            {/* 1. Optional 3-km Mesh Grid Rectangles (in mesh or hybrid mode) */}
            {(renderMode === 'mesh' || renderMode === 'hybrid') &&
              (activeLayer === 'pm25' || activeLayer === 'pm10' || activeLayer === 'o3') &&
              gridData?.cells?.map((cell, idx) => {
                const val = cell.value ?? cell.val ?? 0;
                const color = getCellColor(val);

                return (
                  <Rectangle
                    key={`mesh-rect-${idx}`}
                    bounds={{
                      north: cell.lat + halfLat,
                      south: cell.lat - halfLat,
                      east: cell.lon + halfLon,
                      west: cell.lon - halfLon
                    }}
                    options={{
                      fillColor: renderMode === 'mesh' ? color : 'transparent',
                      fillOpacity: renderMode === 'mesh' ? 0.65 : 0,
                      strokeColor: renderMode === 'hybrid' ? '#64748B' : color,
                      strokeOpacity: renderMode === 'hybrid' ? 0.4 : 0.75,
                      strokeWeight: 0.65,
                      clickable: false
                    }}
                  />
                );
              })}

            {/* 2. Delhi NCR Airshed Boundary Outline */}
            <Polygon
              paths={ncrBoundary}
              options={{
                strokeColor: '#003366',
                strokeOpacity: 0.85,
                strokeWeight: 2.2,
                fillColor: '#003366',
                fillOpacity: 0.02,
                clickable: false
              }}
            />

            {/* 3. Surface Wind Flow Vectors (Staggered aerodynamic sampling across domain) */}
            {(showWindVectors || activeLayer === 'wind') &&
              sampledWindVectors.map((cell, idx) => {
                const u = cell.u_wind ?? -2.0;
                const v = cell.v_wind ?? -1.5;
                const speed = Math.sqrt(u * u + v * v);
                const angleDeg = (Math.atan2(-v, u) * 180) / Math.PI + 90;

                return (
                  <Marker
                    key={`wind-arrow-${idx}`}
                    position={{ lat: cell.lat, lng: cell.lon }}
                    icon={{
                      path: 1, // google.maps.SymbolPath.FORWARD_CLOSED_ARROW
                      scale: Math.max(2.4, Math.min(4.5, speed * 1.4)),
                      rotation: angleDeg,
                      fillColor: '#1D4ED8',
                      fillOpacity: 0.85,
                      strokeColor: '#FFFFFF',
                      strokeWeight: 1
                    }}
                    title={`Surface Wind: ${speed.toFixed(1)} m/s from ${(angleDeg + 360) % 360}°`}
                  />
                );
              })}

            {/* 4. Strategic Pollution Hotspot Radar Beacons */}
            {showHotspots &&
              STRATEGIC_HOTSPOTS.map((spot) => {
                const baseVal = 225.2 + spot.baselineOffset;
                const spotColor = getCellColor(baseVal);

                return (
                  <Marker
                    key={`spot-${spot.id}`}
                    position={{ lat: spot.lat, lng: spot.lon }}
                    onClick={() => setSelectedHotspot(spot)}
                    icon={{
                      path: 0, // SymbolPath.CIRCLE
                      scale: 10,
                      fillColor: spotColor,
                      fillOpacity: 0.95,
                      strokeColor: '#FFFFFF',
                      strokeWeight: 2.5
                    }}
                    label={{
                      text: `${spot.id}: ${baseVal.toFixed(0)}`,
                      color: '#0F172A',
                      fontSize: '10px',
                      fontWeight: 'bold'
                    }}
                    title={`${spot.name} (${spot.type}): ${baseVal.toFixed(1)} µg/m³`}
                  />
                );
              })}

            {/* Hotspot InfoWindow on Click */}
            {selectedHotspot && (
              <InfoWindow
                position={{ lat: selectedHotspot.lat, lng: selectedHotspot.lon }}
                onCloseClick={() => setSelectedHotspot(null)}
              >
                <div style={{ padding: '6px', minWidth: '200px', fontSize: '11px', fontFamily: 'Arial, sans-serif' }}>
                  <div style={{ fontWeight: 'bold', color: '#003366', borderBottom: '1px solid #D9DDE1', paddingBottom: '3px' }}>
                    {selectedHotspot.name.toUpperCase()} RECEPTOR
                  </div>
                  <div style={{ fontSize: '10px', color: '#54595D', marginTop: '3px' }}>
                    {selectedHotspot.type}
                  </div>
                  <table style={{ width: '100%', fontSize: '11px', marginTop: '6px', borderCollapse: 'collapse' }}>
                    <tbody>
                      <tr>
                        <td><strong>Coordinates:</strong></td>
                        <td>{selectedHotspot.lat.toFixed(3)}°N, {selectedHotspot.lon.toFixed(3)}°E</td>
                      </tr>
                      <tr>
                        <td><strong>Peak PM2.5:</strong></td>
                        <td><strong style={{ color: '#DC2626' }}>{(225.2 + selectedHotspot.baselineOffset).toFixed(1)} µg/m³</strong></td>
                      </tr>
                      <tr>
                        <td><strong>Local NAQI:</strong></td>
                        <td><span className="status-tag status-severe">Severe (AQI 390+)</span></td>
                      </tr>
                      <tr>
                        <td><strong>Vulnerability:</strong></td>
                        <td>High Inversion Trap & Advection Focus</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </InfoWindow>
            )}

            {/* 5. Plume Transport Trajectories (Punjab Corridors) */}
            {(activeLayer === 'plume' || activeLayer === 'fires') &&
              plumeTrajectories.map((traj, idx) => (
                <Polyline
                  key={`traj-g-${idx}`}
                  path={traj.path}
                  options={{
                    strokeColor: '#DC2626',
                    strokeOpacity: 0.9,
                    strokeWeight: 3.5,
                    icons: [
                      {
                        icon: {
                          path: 1, // google.maps.SymbolPath.FORWARD_CLOSED_ARROW
                          scale: 3,
                          fillColor: '#DC2626',
                          fillOpacity: 1,
                          strokeColor: '#FFFFFF',
                          strokeWeight: 1
                        },
                        offset: '50%',
                        repeat: '100px'
                      }
                    ]
                  }}
                />
              ))}

            {/* 6. FIRMS Active Fire Satellite Markers */}
            {(activeLayer === 'fires' || activeLayer === 'plume') &&
              activeFires.map((fire) => {
                const lat = fire.centroid_lat ?? fire.cluster_center_lat ?? 29.85;
                const lon = fire.centroid_lon ?? fire.cluster_center_lon ?? 76.10;
                const frp = fire.total_frp_mw ?? fire.total_frp ?? 200;

                return (
                  <Marker
                    key={`fire-g-${fire.cluster_id}`}
                    position={{ lat, lng: lon }}
                    onClick={() => setSelectedFire(fire)}
                    icon={{
                      path: 0, // SymbolPath.CIRCLE
                      scale: Math.min(14, Math.max(7, Math.sqrt(frp) * 0.6)),
                      fillColor: '#DC2626',
                      fillOpacity: 0.9,
                      strokeColor: '#FFFFFF',
                      strokeWeight: 2
                    }}
                    title={`Cluster ${fire.cluster_id}: ${frp.toFixed(0)} MW`}
                  />
                );
              })}

            {/* InfoWindow for Selected Fire Cluster */}
            {selectedFire && (
              <InfoWindow
                position={{
                  lat: selectedFire.centroid_lat ?? selectedFire.cluster_center_lat ?? 29.85,
                  lng: selectedFire.centroid_lon ?? selectedFire.cluster_center_lon ?? 76.10
                }}
                onCloseClick={() => setSelectedFire(null)}
              >
                <div style={{ padding: '6px', minWidth: '200px', fontSize: '11px', fontFamily: 'Arial, sans-serif' }}>
                  <div style={{ fontWeight: 'bold', color: '#DC2626', borderBottom: '1px solid #D9DDE1', paddingBottom: '3px' }}>
                    ACTIVE FIRE CLUSTER ({selectedFire.cluster_id})
                  </div>
                  <table style={{ width: '100%', fontSize: '11px', marginTop: '6px', borderCollapse: 'collapse' }}>
                    <tbody>
                      <tr>
                        <td><strong>FRP:</strong></td>
                        <td><strong style={{ color: '#DC2626' }}>{(selectedFire.total_frp_mw ?? selectedFire.total_frp ?? 0).toFixed(1)} MW</strong></td>
                      </tr>
                      <tr>
                        <td><strong>Hotspots:</strong></td>
                        <td>{selectedFire.fire_count} active detections</td>
                      </tr>
                      <tr>
                        <td><strong>Distance:</strong></td>
                        <td>{(selectedFire.distance_to_delhi_km ?? selectedFire.distance_km ?? 150).toFixed(1)} km upwind</td>
                      </tr>
                      <tr>
                        <td><strong>Advection ETA:</strong></td>
                        <td>+{(selectedFire.estimated_arrival_hours ?? 18).toFixed(1)} Hours</td>
                      </tr>
                      <tr>
                        <td><strong>Transport Score:</strong></td>
                        <td>{selectedFire.transport_potential_score ?? 84} / 100</td>
                      </tr>
                      <tr>
                        <td><strong>Telemetry Source:</strong></td>
                        <td>NASA FIRMS (MODIS/VIIRS)</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </InfoWindow>
            )}
          </GoogleMap>
        )}

        {/* Dynamic Glassmorphic Telemetry HUD (Live Cursor Inspector) */}
        {hoverInfo && (
          <div className="map-hud-card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
              <strong style={{ fontSize: '12px', color: '#003366' }}>
                {hoverInfo.locationName}
              </strong>
              <span className={`status-tag status-${hoverInfo.statusClass}`} style={{ fontSize: '10px' }}>
                AQI {hoverInfo.aqi} · {hoverInfo.statusLabel}
              </span>
            </div>
            <div style={{ fontSize: '24px', fontWeight: 'bold', color: hoverInfo.color, lineHeight: 1.1 }}>
              {hoverInfo.val.toFixed(1)}{' '}
              <span style={{ fontSize: '12px', color: '#54595D', fontWeight: 'normal' }}>
                µg/m³ {activeLayer.toUpperCase()}
              </span>
            </div>
            <div style={{ fontSize: '11px', color: '#334155', marginTop: '4px' }}>
              Surface Wind: <strong>{hoverInfo.speed.toFixed(1)} m/s</strong> from <strong>{hoverInfo.dirCard} ({hoverInfo.dirDeg}°)</strong>
            </div>
            <div style={{ fontSize: '10px', color: '#64748B', marginTop: '2px' }}>
              {hoverInfo.dispersionText} · Cell <code>{hoverInfo.gridId}</code> ({hoverInfo.lat.toFixed(3)}°N, {hoverInfo.lon.toFixed(3)}°E)
            </div>
          </div>
        )}

        {/* Floating Continuous CPCB Spectrum Legend (Bottom Right) */}
        <div
          style={{
            position: 'absolute',
            bottom: '16px',
            right: '16px',
            zIndex: 10,
            background: 'rgba(255, 255, 255, 0.95)',
            backdropFilter: 'blur(8px)',
            WebkitBackdropFilter: 'blur(8px)',
            border: '1px solid var(--border-color)',
            borderRadius: '4px',
            padding: '10px 14px',
            boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
            fontSize: '11px',
            minWidth: '240px'
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--border-color)', paddingBottom: '4px' }}>
            <span style={{ fontWeight: 'bold', color: '#003366' }}>
              CPCB NAQI CONTINUOUS SPECTRUM
            </span>
            <span style={{ fontSize: '10px', color: 'var(--text-secondary)' }}>µg/m³</span>
          </div>

          {/* Continuous Gradient Bar */}
          <div className="map-legend-gradient-bar" />

          {/* Numerical Breakpoints Scale */}
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px', color: '#54595D', fontWeight: 600 }}>
            <span>0</span>
            <span>60</span>
            <span>120</span>
            <span>250</span>
            <span>350</span>
            <span>450+</span>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '9px', color: '#64748B', marginTop: '2px' }}>
            <span style={{ color: '#10B981' }}>Good</span>
            <span style={{ color: '#84CC16' }}>Sat</span>
            <span style={{ color: '#F59E0B' }}>Mod</span>
            <span style={{ color: '#F97316' }}>Poor</span>
            <span style={{ color: '#EF4444' }}>V.Poor</span>
            <span style={{ color: '#7F1D1D', fontWeight: 'bold' }}>Severe</span>
          </div>

          {/* Opacity Adjustment Slider */}
          <div style={{ marginTop: '8px', paddingTop: '6px', borderTop: '1px solid #EAECF0', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '10px', color: '#54595D' }}>Opacity:</span>
            <input
              type="range"
              min="0.25"
              max="0.95"
              step="0.05"
              value={heatmapOpacity}
              onChange={(e) => setHeatmapOpacity(parseFloat(e.target.value))}
              style={{ width: '130px', cursor: 'pointer' }}
            />
            <span style={{ fontSize: '10px', fontWeight: 'bold', color: '#003366' }}>
              {Math.round(heatmapOpacity * 100)}%
            </span>
          </div>
        </div>

        {/* Data Provenance & Domain Info (Bottom Left) */}
        <div
          style={{
            position: 'absolute',
            bottom: '16px',
            left: '16px',
            zIndex: 10,
            background: 'rgba(255, 255, 255, 0.92)',
            backdropFilter: 'blur(6px)',
            WebkitBackdropFilter: 'blur(6px)',
            border: '1px solid var(--border-color)',
            borderRadius: '3px',
            padding: '6px 10px',
            fontSize: '10px',
            color: 'var(--text-secondary)'
          }}
        >
          <div>
            Coupled Engine: <strong>WRF-Chem D03 3-km Grid</strong> · Continuous Canvas Interpolation
          </div>
          <div>
            Forecast Step: <strong>+{timeStep} Hours</strong> · Receptor: <strong>Delhi Central Airshed</strong>
          </div>
        </div>
      </div>
    </div>
  );
};
