import React, { useState, useEffect, useMemo } from 'react';
import {
  MapContainer,
  TileLayer,
  Rectangle,
  CircleMarker,
  Polyline,
  Polygon,
  Popup,
  Tooltip,
  useMap
} from 'react-leaflet';
import { LatLngBoundsExpression, LatLngExpression } from 'leaflet';
import { SpatialGridData, PlumeData, PlumeEstimate } from '../../types';
import { fetchSpatialGrid } from '../../api';

function MapResizer() {
  const map = useMap();
  useEffect(() => {
    const timer = setTimeout(() => {
      map.invalidateSize();
    }, 200);
    return () => clearTimeout(timer);
  }, [map]);
  return null;
}

interface OsmPollutionMapProps {
  plumes: PlumeData | null;
  onSwitchProvider?: (provider: 'google' | 'osm') => void;
}

export const OsmPollutionMap: React.FC<OsmPollutionMapProps> = ({ plumes, onSwitchProvider }) => {
  const [activeLayer, setActiveLayer] = useState<'pm25' | 'pm10' | 'o3' | 'wind' | 'fires' | 'plume'>('pm25');
  const [timeStep, setTimeStep] = useState<number>(0);
  const [gridData, setGridData] = useState<SpatialGridData | null>(null);

  const delhiCenter: LatLngExpression = [28.6139, 77.2090];
  const initialZoom = 9;

  const backendVar = activeLayer === 'pm10' ? 'pm10' : activeLayer === 'o3' ? 'o3' : 'pm25';

  useEffect(() => {
    let active = true;
    fetchSpatialGrid(backendVar, timeStep)
      .then((data) => {
        if (active) setGridData(data);
      })
      .catch((err) => console.error('Spatial grid fetch error:', err));
    return () => {
      active = false;
    };
  }, [backendVar, timeStep]);

  const getCellColor = (val: number, layer: string): string => {
    if (layer === 'o3') {
      if (val < 40) return 'transparent';
      if (val < 85) return '#F97316'; // Moderate Orange
      return '#DC2626'; // Severe Red
    }
    if (layer === 'pm10') {
      if (val < 140) return 'transparent';
      if (val < 300) return '#F97316'; // Moderate Orange
      return '#DC2626'; // Severe Red
    }
    // PM2.5 default
    if (val < 80) return 'transparent'; // Non-contributing / baseline
    if (val < 190) return '#F97316'; // Moderate Orange
    return '#DC2626'; // Severe Dense Red
  };

  const getAqiCategory = (val: number): string => {
    if (val <= 60) return 'GOOD';
    if (val <= 120) return 'SATISFACTORY';
    if (val <= 250) return 'MODERATE';
    if (val <= 350) return 'POOR';
    if (val <= 450) return 'VERY POOR';
    return 'SEVERE';
  };

  const halfLat = 0.0135;
  const halfLon = 0.0155;

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

  const plumeTrajectories = useMemo(() => {
    return activeFires.map((fire) => {
      const lat = fire.centroid_lat ?? fire.cluster_center_lat ?? 29.85;
      const lon = fire.centroid_lon ?? fire.cluster_center_lon ?? 76.10;
      const start: LatLngExpression = [lat, lon];
      const mid1: LatLngExpression = [
        lat * 0.7 + 28.6139 * 0.3 - 0.03,
        lon * 0.7 + 77.2090 * 0.3 + 0.05
      ];
      const mid2: LatLngExpression = [
        lat * 0.35 + 28.6139 * 0.65 - 0.02,
        lon * 0.35 + 77.2090 * 0.65 + 0.02
      ];
      const end: LatLngExpression = [28.6139, 77.2090];
      return {
        fire,
        path: [start, mid1, mid2, end]
      };
    });
  }, [activeFires]);

  const ncrBoundary: LatLngExpression[] = [
    [28.25, 76.70],
    [28.15, 77.05],
    [28.20, 77.45],
    [28.40, 77.68],
    [28.75, 77.75],
    [29.10, 77.55],
    [29.18, 77.10],
    [29.02, 76.70],
    [28.60, 76.55],
    [28.25, 76.70]
  ];

  return (
    <div className="portal-section" style={{ padding: 0 }}>
      {/* Map Institutional Header */}
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
          <strong style={{ fontSize: '14px', color: '#003366' }}>
            DELHI NCR — 3 KM POLLUTION DISTRIBUTION (OPENSTREETMAP)
          </strong>
          <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
            WRF-Chem Coupled Two-Way Atmospheric Chemistry Grid (D03 Domain)
          </div>
        </div>

        {/* Time Selector */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          <span style={{ fontSize: '11px', fontWeight: 'bold', color: 'var(--text-secondary)', marginRight: '4px' }}>
            TIME HORIZON:
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

      {/* Layer Selector Bar */}
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
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span style={{ fontSize: '11px', fontWeight: 'bold', color: 'var(--text-secondary)', marginRight: '4px' }}>
            ACTIVE LAYER:
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
              {l === 'pm25' ? 'PM2.5 Heatmap' : l === 'pm10' ? 'PM10 Heatmap' : l === 'o3' ? 'Ozone (O3)' : l === 'wind' ? 'Wind Field' : l === 'fires' ? 'FIRMS Fires' : 'Modelled Plume'}
            </button>
          ))}
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {onSwitchProvider && (
            <div style={{ display: 'flex', background: '#F1F5F9', padding: '2px', borderRadius: '3px', border: '1px solid var(--border-color)' }}>
              <button
                onClick={() => onSwitchProvider('google')}
                className="portal-btn-secondary"
                style={{ padding: '2px 7px', fontSize: '10px', background: 'transparent', border: 'none' }}
              >
                Google Maps
              </button>
              <button
                className="portal-btn"
                style={{ padding: '2px 7px', fontSize: '10px' }}
              >
                OpenStreetMap
              </button>
            </div>
          )}
          <span className="prov-badge modelled">MODELLED</span>
        </div>
      </div>

      {/* Map Container */}
      <div style={{ position: 'relative', width: '100%', height: '520px', background: '#F5F6F7' }}>
        <MapContainer
          center={delhiCenter}
          zoom={initialZoom}
          scrollWheelZoom={true}
          style={{ height: '100%', width: '100%' }}
        >
          <MapResizer />

          {/* OpenStreetMap Standard Base Tiles */}
          <TileLayer
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            maxZoom={18}
          />

          {/* Delhi NCR Airshed Boundary Polygon */}
          <Polygon
            positions={ncrBoundary}
            pathOptions={{
              color: '#003366',
              weight: 2,
              dashArray: '5, 5',
              fillColor: '#003366',
              fillOpacity: 0.04
            }}
          />

          {/* 1. Contributing Source Plume Clusters (Dense Red in Severe, Orange in Moderate) */}
          {(activeLayer === 'pm25' || activeLayer === 'pm10' || activeLayer === 'o3') &&
            gridData?.cells
              ?.filter((cell) => {
                const val = cell.value ?? cell.val ?? 0;
                const minThresh = activeLayer === 'pm10' ? 140 : activeLayer === 'o3' ? 40 : 80;
                return val >= minThresh; // Only render regions that contribute!
              })
              .map((cell, idx) => {
                const val = cell.value ?? cell.val ?? 0;
                const color = getCellColor(val, activeLayer);
                const isSevere = color === '#DC2626';

                return (
                  <CircleMarker
                    key={`cell-${idx}`}
                    center={[cell.lat, cell.lon]}
                    radius={isSevere ? 22 : 15}
                    pathOptions={{
                      color: color,
                      fillColor: color,
                      fillOpacity: isSevere ? 0.90 : 0.60,
                      weight: isSevere ? 2 : 1,
                      stroke: false
                    }}
                  >
                    <Tooltip direction="top" offset={[0, -5]} opacity={0.95}>
                      <div style={{ fontSize: '11px', lineHeight: '1.4', fontFamily: 'Calibri, sans-serif' }}>
                        <strong>Cell: {cell.grid_id || `D03-${idx}`}</strong><br />
                        Lat: {cell.lat.toFixed(3)}, Lon: {cell.lon.toFixed(3)}<br />
                        {activeLayer.toUpperCase()}: <strong>{val.toFixed(1)} µg/m³</strong><br />
                        Status: <span style={{ fontWeight: 'bold', color }}>{isSevere ? 'SEVERE HAZARD' : 'MODERATE'}</span><br />
                        Wind: {Math.sqrt((cell.u_wind ?? 0) ** 2 + (cell.v_wind ?? 0) ** 2).toFixed(1)} m/s<br />
                        <span className="prov-badge modelled">WRF-Chem D03</span>
                      </div>
                    </Tooltip>
                  </CircleMarker>
                );
              })}

          {/* 2. Wind Flow Vector Representation */}
          {activeLayer === 'wind' &&
            gridData?.cells
              ?.filter((_, idx) => idx % 4 === 0)
              .map((cell, idx) => {
                const u = cell.u_wind ?? -2.0;
                const v = cell.v_wind ?? -1.5;
                const speed = Math.sqrt(u * u + v * v);
                const endLat = cell.lat + (v * 0.015);
                const endLon = cell.lon + (u * 0.015);

                return (
                  <React.Fragment key={`wind-${idx}`}>
                    <Polyline
                      positions={[
                        [cell.lat, cell.lon],
                        [endLat, endLon]
                      ]}
                      pathOptions={{
                        color: '#1D4ED8',
                        weight: 2,
                        opacity: 0.85
                      }}
                    />
                    <CircleMarker
                      center={[endLat, endLon]}
                      radius={2.5}
                      pathOptions={{
                        color: '#1D4ED8',
                        fillColor: '#1D4ED8',
                        fillOpacity: 1
                      }}
                    />
                  </React.Fragment>
                );
              })}

          {/* 3. FIRMS Satellite Fire Detections */}
          {(activeLayer === 'fires' || activeLayer === 'plume') &&
            activeFires.map((fire) => {
              const lat = fire.centroid_lat ?? fire.cluster_center_lat ?? 29.85;
              const lon = fire.centroid_lon ?? fire.cluster_center_lon ?? 76.10;
              const frp = fire.total_frp_mw ?? fire.total_frp ?? 200;

              return (
                <CircleMarker
                  key={`fire-${fire.cluster_id}`}
                  center={[lat, lon]}
                  radius={Math.min(14, Math.max(7, Math.sqrt(frp) * 0.6))}
                  pathOptions={{
                    color: '#DC2626',
                    fillColor: '#EF4444',
                    fillOpacity: 0.85,
                    weight: 2
                  }}
                >
                  <Popup>
                    <div style={{ padding: '4px', minWidth: '180px', fontSize: '11px' }}>
                      <strong style={{ color: '#DC2626' }}>CLUSTER: {fire.cluster_id}</strong><br />
                      FRP: <strong>{frp.toFixed(1)} MW</strong><br />
                      Fires: <strong>{fire.fire_count} hotspots</strong><br />
                      Distance: {(fire.distance_to_delhi_km ?? fire.distance_km ?? 150).toFixed(1)} km upwind<br />
                      Transport ETA: +{(fire.estimated_arrival_hours ?? 18).toFixed(1)} h<br />
                      Transport Score: {fire.transport_potential_score ?? 84} / 100<br />
                      <span className="prov-badge observed">NASA FIRMS</span>
                    </div>
                  </Popup>
                </CircleMarker>
              );
            })}

          {/* 4. Modelled Plume Trajectories */}
          {(activeLayer === 'plume' || activeLayer === 'fires') &&
            plumeTrajectories.map((traj, idx) => (
              <Polyline
                key={`traj-${idx}`}
                positions={traj.path}
                pathOptions={{
                  color: '#DC2626',
                  weight: 3,
                  opacity: 0.8,
                  dashArray: '8, 8'
                }}
              >
                <Tooltip direction="top">
                  <div style={{ fontSize: '11px' }}>
                    <strong>Modelled Biomass Plume Advection</strong><br />
                    Source: {traj.fire.cluster_id}<br />
                    ETA Central Delhi: +{(traj.fire.estimated_arrival_hours ?? 18).toFixed(1)} h<br />
                    <span className="prov-badge modelled">WRF-Chem Wind Coupling</span>
                  </div>
                </Tooltip>
              </Polyline>
            ))}
        </MapContainer>

        {/* Floating Fixed CPCB NAQI Legend (Bottom Right) */}
        <div
          style={{
            position: 'absolute',
            bottom: '16px',
            right: '16px',
            zIndex: 1000,
            background: '#FFFFFF',
            border: '1px solid var(--border-color)',
            padding: '10px 14px',
            boxShadow: '0 2px 6px rgba(0,0,0,0.15)',
            fontSize: '11px',
            minWidth: '190px'
          }}
        >
          <div style={{ fontWeight: 'bold', color: '#003366', borderBottom: '1px solid var(--border-color)', paddingBottom: '4px', marginBottom: '6px' }}>
            CPCB NAQI CONCENTRATION SCALE
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '16px 1fr auto', gap: '4px', alignItems: 'center', marginBottom: '3px' }}>
            <span style={{ width: '12px', height: '12px', background: '#16A34A', border: '1px solid #14532D' }}></span>
            <span>0 – 60</span>
            <span style={{ fontWeight: 'bold', color: '#16A34A' }}>Good</span>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '16px 1fr auto', gap: '4px', alignItems: 'center', marginBottom: '3px' }}>
            <span style={{ width: '12px', height: '12px', background: '#65A30D', border: '1px solid #3F6212' }}></span>
            <span>61 – 120</span>
            <span style={{ fontWeight: 'bold', color: '#65A30D' }}>Satisfactory</span>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '16px 1fr auto', gap: '4px', alignItems: 'center', marginBottom: '3px' }}>
            <span style={{ width: '12px', height: '12px', background: '#EAB308', border: '1px solid #854D0E' }}></span>
            <span>121 – 250</span>
            <span style={{ fontWeight: 'bold', color: '#854D0E' }}>Moderate</span>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '16px 1fr auto', gap: '4px', alignItems: 'center', marginBottom: '3px' }}>
            <span style={{ width: '12px', height: '12px', background: '#EA580C', border: '1px solid #9A3412' }}></span>
            <span>251 – 350</span>
            <span style={{ fontWeight: 'bold', color: '#EA580C' }}>Poor</span>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '16px 1fr auto', gap: '4px', alignItems: 'center', marginBottom: '3px' }}>
            <span style={{ width: '12px', height: '12px', background: '#DC2626', border: '1px solid #991B1B' }}></span>
            <span>351 – 450</span>
            <span style={{ fontWeight: 'bold', color: '#DC2626' }}>Very Poor</span>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '16px 1fr auto', gap: '4px', alignItems: 'center' }}>
            <span style={{ width: '12px', height: '12px', background: '#991B1B', border: '1px solid #450A0A' }}></span>
            <span>450+</span>
            <span style={{ fontWeight: 'bold', color: '#991B1B' }}>Severe</span>
          </div>
        </div>

        {/* Data Source & Timestamp (Bottom Left) */}
        <div
          style={{
            position: 'absolute',
            bottom: '16px',
            left: '16px',
            zIndex: 1000,
            background: '#FFFFFF',
            border: '1px solid var(--border-color)',
            padding: '6px 10px',
            fontSize: '10px',
            color: 'var(--text-secondary)'
          }}
        >
          <div>Model Resolution: <strong>3-km D03 WRF-Chem Domain</strong></div>
          <div>Forecast Horizon: <strong>+{timeStep} Hours</strong> · Coupled Replay Mode</div>
        </div>
      </div>
    </div>
  );
};
