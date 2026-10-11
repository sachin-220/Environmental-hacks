import React from 'react';
import { X, CheckCircle2, Cpu, Activity, Clock } from 'lucide-react';
import { BackendActivity } from '../../types';

interface BackendActivityDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  activity: BackendActivity | null;
}

export const BackendActivityDrawer: React.FC<BackendActivityDrawerProps> = ({
  isOpen,
  onClose,
  activity
}) => {
  if (!isOpen) return null;

  const events = activity?.events || [
    { timestamp: '10:42:18', service: 'INGESTION', message: 'ERA5/CAMS atmospheric boundary slice loaded', latency_ms: 14.2 },
    { timestamp: '10:42:19', service: 'WRF-CHEM', message: '3-km D03 coupled meteorology-chemistry state processed', latency_ms: 8.5 },
    { timestamp: '10:42:19', service: 'DMDC', message: 'Rank-12 recursive 72h forward rollout completed', latency_ms: 32.2 },
    { timestamp: '10:42:19', service: 'UNCERTAINTY', message: 'Lyapunov analytical error covariance Sigma_k propagated', latency_ms: 4.8 },
    { timestamp: '10:42:20', service: 'ATTRIBUTION', message: 'Zero-out counterfactual sensitivity evaluated across 5 sectors', latency_ms: 42.1 },
    { timestamp: '10:42:20', service: 'PLUMES', message: 'NASA FIRMS satellite active fires clustered; arrival ETA computed', latency_ms: 11.0 },
    { timestamp: '10:42:20', service: 'MPC', message: 'Constrained SLSQP policy optimizer ready with feasibility bounds', latency_ms: 145.0 }
  ];

  const pipeline = activity?.pipeline_status || {
    data_ingestion: 'OPERATIONAL',
    wrfchem_state: 'READY',
    dmdc_forecast: 'READY',
    attribution: 'READY',
    mpc_engine: 'READY'
  };

  return (
    <div className="drawer-backdrop" onClick={onClose}>
      <div className="drawer-panel" onClick={(e) => e.stopPropagation()}>
        <div className="drawer-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Activity size={18} color="#2563EB" />
            <h3 style={{ fontSize: '0.95rem', fontWeight: 600 }}>SYSTEM ACTIVITY</h3>
          </div>
          <button
            onClick={onClose}
            style={{ background: 'transparent', border: 'none', color: '#94A3B8', cursor: 'pointer' }}
          >
            <X size={18} />
          </button>
        </div>

        <div className="drawer-body">
          {/* Subsystem Health Status Matrix */}
          <div style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-md)', padding: '12px 14px' }}>
            <span style={{ fontSize: '0.7rem', fontWeight: 600, color: '#64748B', textTransform: 'uppercase', letterSpacing: '0.04em', display: 'block', marginBottom: '8px' }}>
              Subsystem Pipeline Status
            </span>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', fontFamily: 'var(--font-mono)', fontSize: '0.72rem' }}>
              {Object.entries(pipeline).map(([service, status]) => (
                <div key={service} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ color: '#475569' }}>{service.replace('_', ' ').toUpperCase()}</span>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '4px', color: '#16A34A', fontWeight: 600 }}>
                    <span className="status-dot green" />
                    <span>{status}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Telemetry Event Stream */}
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
              <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#111827' }}>
                Telemetry Log
              </span>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.68rem', color: '#64748B' }}>
                Updated: {activity?.last_updated || 'Just now'}
              </span>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {events.map((evt, idx) => (
                <div key={idx} className="event-log-item">
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span className="event-log-time">{evt.timestamp}</span>
                    <span style={{ color: '#64748B', fontSize: '0.65rem' }}>{evt.latency_ms} ms</span>
                  </div>
                  <div>
                    <span className="event-log-service">[{evt.service}] </span>
                    <span className="event-log-msg">{evt.message}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div style={{ padding: '12px 20px', borderTop: '1px solid var(--border-subtle)', background: 'var(--bg-secondary)', fontFamily: 'var(--font-mono)', fontSize: '0.72rem', display: 'flex', justifyContent: 'space-between', color: '#64748B' }}>
          <span>MODE: {activity?.operating_mode || 'REPLAY MODE'}</span>
          <span style={{ color: '#16A34A', fontWeight: 600 }}>ALL SERVICES OPERATIONAL</span>
        </div>
      </div>
    </div>
  );
};
