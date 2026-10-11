import React from 'react';
import { TrendingUp, AlertCircle, Zap } from 'lucide-react';
import { CleanForecastChart } from '../components/forecast/CleanForecastChart';
import { ForecastData } from '../types';

interface ForecastPageProps {
  forecast: ForecastData | null;
}

export const ForecastPage: React.FC<ForecastPageProps> = ({ forecast }) => {
  const timeline = forecast?.hourly_timeline || [];
  const checkpoints = [0, 5, 11, 23, 47, 71].map(i => timeline[i]).filter(Boolean);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '22px' }}>
      <div className="white-card" style={{ padding: '20px 24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#111827' }}>72-HOUR FORWARD FORECAST INTELLIGENCE</h2>
            <p style={{ fontSize: '0.78rem', color: '#64748B', marginTop: '2px' }}>
              Recursive state rollout via Rank-12 Koopman Operator (A, B) with analytical Lyapunov uncertainty propagation
            </p>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.72rem', color: '#16A34A', fontWeight: 600 }}>
              Rollout: ~32.2 ms
            </span>
            <span className="provenance-tag modelled">MODELLED</span>
          </div>
        </div>
      </div>

      <CleanForecastChart forecast={forecast} />

      {/* Checkpoints Multi-Horizon Table */}
      <div className="white-card" style={{ padding: '20px' }}>
        <h3 style={{ fontSize: '0.9rem', fontWeight: 600, marginBottom: '14px' }}>
          MULTI-HORIZON EVALUATION CHECKPOINTS
        </h3>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.76rem', fontFamily: 'var(--font-mono)' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border-subtle)', textAlign: 'left', color: '#64748B' }}>
                <th style={{ padding: '8px 12px' }}>HORIZON</th>
                <th style={{ padding: '8px 12px' }}>CPCB NAQI</th>
                <th style={{ padding: '8px 12px' }}>CATEGORY</th>
                <th style={{ padding: '8px 12px' }}>PM2.5 (µg/m³)</th>
                <th style={{ padding: '8px 12px' }}>95% UNCERTAINTY BAND</th>
                <th style={{ padding: '8px 12px' }}>PBL HEIGHT</th>
                <th style={{ padding: '8px 12px' }}>WIND SPEED</th>
              </tr>
            </thead>
            <tbody>
              {checkpoints.map((pt) => (
                <tr key={pt.hour} style={{ borderBottom: '1px solid #F1F5F9' }}>
                  <td style={{ padding: '10px 12px', fontWeight: 700, color: '#2563EB' }}>+{pt.hour}h</td>
                  <td style={{ padding: '10px 12px', fontWeight: 700, color: pt.aqi > 400 ? '#991B1B' : '#DC2626' }}>{pt.aqi}</td>
                  <td style={{ padding: '10px 12px' }}>
                    <span style={{
                      padding: '2px 6px',
                      borderRadius: '4px',
                      fontSize: '0.68rem',
                      fontWeight: 600,
                      background: pt.aqi > 400 ? '#FEF2F2' : '#FFFBEB',
                      color: pt.aqi > 400 ? '#DC2626' : '#D97706'
                    }}>
                      {pt.category}
                    </span>
                  </td>
                  <td style={{ padding: '10px 12px', fontWeight: 600 }}>{pt.pm25}</td>
                  <td style={{ padding: '10px 12px', color: '#64748B' }}>[{pt.pm25_lower} – {pt.pm25_upper}]</td>
                  <td style={{ padding: '10px 12px' }}>{pt.boundary_layer_height} m</td>
                  <td style={{ padding: '10px 12px' }}>{pt.wind_speed_10m} m/s</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
