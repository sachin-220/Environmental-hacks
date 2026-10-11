import React from 'react';
import { Activity, Wind, Thermometer, Layers } from 'lucide-react';
import { CurrentState } from '../../types';

interface CurrentStateTilesProps {
  state: CurrentState | null;
}

export const CurrentStateTiles: React.FC<CurrentStateTilesProps> = ({ state }) => {
  const aqi = state?.aqi ?? 165;
  const pm25 = state?.pm25 ?? 85.0;
  const pm10 = state?.pm10 ?? 180.0;
  const pblh = state?.boundary_layer_height ?? 845.0;
  const wind = state?.wind_speed_10m ?? 2.5;
  const inv = state?.inversion_strength ?? 1.2;

  const isObserved = state?.provenance === 'OBSERVED';
  const tagLabel = isObserved ? 'OBSERVED LIVE' : 'MODELLED';

  const getAQIColor = (val: number): string => {
    if (val <= 50) return '#2D6A4F';
    if (val <= 100) return '#40916C';
    if (val <= 200) return '#D97706';
    if (val <= 300) return '#C2410C';
    if (val <= 400) return '#B91C1C';
    return '#7F1D1D';
  };

  const aqiColor = getAQIColor(aqi);

  // Normalized visual percentage helpers
  const pm25Pct = Math.min(100, Math.round((pm25 / 300) * 100));
  const pm10Pct = Math.min(100, Math.round((pm10 / 500) * 100));
  const pblhPct = Math.min(100, Math.round((pblh / 2000) * 100));
  const invPct = Math.min(100, Math.round((inv / 4.0) * 100));

  return (
    <div
      className="air-card"
      style={{
        padding: '20px 26px',
        marginBottom: '20px'
      }}
    >
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
          gap: '20px',
          alignItems: 'center'
        }}
      >
        {/* 1. Primary AQI Metric */}
        <div
          style={{
            borderRight: '1px solid var(--border-subtle)',
            paddingRight: '16px',
            display: 'flex',
            alignItems: 'center',
            gap: '14px'
          }}
        >
          <div
            style={{
              width: '56px',
              height: '56px',
              borderRadius: 'var(--radius-md)',
              background: `${aqiColor}12`,
              border: `2px solid ${aqiColor}`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0
            }}
          >
            <Activity size={28} color={aqiColor} />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ fontSize: '12px', fontWeight: 800, color: 'var(--text-muted)', letterSpacing: '0.4px' }}>
                CPCB NAQI
              </span>
              <span
                style={{
                  fontSize: '10.5px',
                  fontWeight: 800,
                  background: isObserved ? '#D8F3DC' : '#E8F5E9',
                  color: '#1B4332',
                  padding: '2px 7px',
                  borderRadius: '999px'
                }}
              >
                {tagLabel}
              </span>
            </div>
            <div
              style={{
                fontSize: '34px',
                fontWeight: 900,
                color: aqiColor,
                lineHeight: 1.05,
                fontFamily: 'var(--font-display)',
                letterSpacing: '-1px'
              }}
            >
              {Math.round(aqi)}
            </div>
            <div style={{ fontSize: '12px', fontWeight: 800, color: aqiColor, letterSpacing: '0.3px' }}>
              {state?.category?.toUpperCase() || 'MODERATE'}
            </div>
          </div>
        </div>

        {/* 2. PM2.5 Fine Particulate */}
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', fontSize: '13px', marginBottom: '6px' }}>
            <span style={{ color: 'var(--text-secondary)', fontWeight: 700 }}>PM2.5 Aerosol</span>
            <span style={{ fontWeight: 800, color: '#B91C1C', fontFamily: 'var(--font-mono)', fontSize: '15px' }}>
              {pm25} µg/m³
            </span>
          </div>
          <div style={{ width: '100%', height: '6px', background: 'var(--bg-surface-subtle)', borderRadius: '999px', overflow: 'hidden' }}>
            <div
              style={{
                width: `${pm25Pct}%`,
                height: '100%',
                background: pm25 > 120 ? '#B91C1C' : pm25 > 60 ? '#D97706' : '#2D6A4F',
                borderRadius: '999px',
                transition: 'width 0.4s ease'
              }}
            />
          </div>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px' }}>
            National Standard: 60 µg/m³
          </div>
        </div>

        {/* 3. PM10 Coarse Particulate */}
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', fontSize: '13px', marginBottom: '6px' }}>
            <span style={{ color: 'var(--text-secondary)', fontWeight: 700 }}>PM10 Respirable</span>
            <span style={{ fontWeight: 800, color: '#C2410C', fontFamily: 'var(--font-mono)', fontSize: '15px' }}>
              {pm10} µg/m³
            </span>
          </div>
          <div style={{ width: '100%', height: '6px', background: 'var(--bg-surface-subtle)', borderRadius: '999px', overflow: 'hidden' }}>
            <div
              style={{
                width: `${pm10Pct}%`,
                height: '100%',
                background: pm10 > 250 ? '#B91C1C' : pm10 > 100 ? '#C2410C' : '#2D6A4F',
                borderRadius: '999px',
                transition: 'width 0.4s ease'
              }}
            />
          </div>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px' }}>
            National Standard: 100 µg/m³
          </div>
        </div>

        {/* 4. Planetary Boundary Layer Height */}
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', fontSize: '13px', marginBottom: '6px' }}>
            <span style={{ color: 'var(--text-secondary)', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '5px' }}>
              <Layers size={14} color="#2D6A4F" /> PBL Height
            </span>
            <span style={{ fontWeight: 800, color: '#1B4332', fontFamily: 'var(--font-mono)', fontSize: '15px' }}>
              {Math.round(pblh)} m
            </span>
          </div>
          <div style={{ width: '100%', height: '6px', background: 'var(--bg-surface-subtle)', borderRadius: '999px', overflow: 'hidden' }}>
            <div
              style={{
                width: `${pblhPct}%`,
                height: '100%',
                background: '#2D6A4F',
                borderRadius: '999px',
                transition: 'width 0.4s ease'
              }}
            />
          </div>
          <div style={{ fontSize: '11px', color: pblh < 500 ? '#B91C1C' : '#2D6A4F', marginTop: '4px', fontWeight: 700 }}>
            {pblh < 500 ? 'Severe Inversion Compression' : 'Adequate Ventilation'}
          </div>
        </div>

        {/* 5. Inversion Lid & Surface Wind */}
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', fontSize: '13px', marginBottom: '6px' }}>
            <span style={{ color: 'var(--text-secondary)', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '5px' }}>
              <Thermometer size={14} color="#D97706" /> Thermal Lid
            </span>
            <span style={{ fontWeight: 800, color: '#D97706', fontFamily: 'var(--font-mono)', fontSize: '15px' }}>
              +{inv} K
            </span>
          </div>
          <div style={{ width: '100%', height: '6px', background: 'var(--bg-surface-subtle)', borderRadius: '999px', overflow: 'hidden' }}>
            <div
              style={{
                width: `${invPct}%`,
                height: '100%',
                background: inv > 1.0 ? '#B91C1C' : '#D97706',
                borderRadius: '999px',
                transition: 'width 0.4s ease'
              }}
            />
          </div>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px', display: 'flex', alignItems: 'center', gap: '5px' }}>
            <Wind size={13} color="#2D6A4F" />
            <span>Wind: <strong>{wind} m/s WNW</strong></span>
          </div>
        </div>
      </div>
    </div>
  );
};
