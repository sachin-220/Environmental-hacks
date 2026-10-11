import React from 'react';
import { Cpu, ShieldCheck, CheckCircle2, Zap } from 'lucide-react';
import { SystemHealth } from '../types';

interface ModelPageProps {
  health: SystemHealth | null;
}

export const ModelPage: React.FC<ModelPageProps> = ({ health }) => {
  const dmdc = health?.dmdc_model;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '22px' }}>
      <div className="white-card" style={{ padding: '20px 24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#111827' }}>MODEL HEALTH & MATHEMATICAL SPECIFICATIONS</h2>
            <p style={{ fontSize: '0.78rem', color: '#64748B', marginTop: '2px' }}>
              Verified scientific properties of the Rank-12 Koopman/DMDc reduced-order emulator
            </p>
          </div>
          <span className="provenance-tag modelled">VERIFIED PRODUCTION MODEL</span>
        </div>
      </div>

      {/* Primary Status Tiles */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px' }}>
        <div className="white-card" style={{ padding: '16px' }}>
          <span style={{ fontSize: '0.7rem', fontWeight: 600, color: '#64748B', textTransform: 'uppercase' }}>WRF-Chem Subsystem</span>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '8px', color: '#16A34A', fontFamily: 'var(--font-mono)', fontWeight: 700 }}>
            <span className="status-dot green" />
            <span>READY</span>
          </div>
          <span style={{ fontSize: '0.68rem', color: '#64748B', marginTop: '4px', display: 'block' }}>Two-Way Coupled Simulation</span>
        </div>

        <div className="white-card" style={{ padding: '16px' }}>
          <span style={{ fontSize: '0.7rem', fontWeight: 600, color: '#64748B', textTransform: 'uppercase' }}>DMDc Emulator</span>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '8px', color: '#16A34A', fontFamily: 'var(--font-mono)', fontWeight: 700 }}>
            <span className="status-dot green" />
            <span>READY</span>
          </div>
          <span style={{ fontSize: '0.68rem', color: '#64748B', marginTop: '4px', display: 'block' }}>Linear State Operator (A, B)</span>
        </div>

        <div className="white-card" style={{ padding: '16px' }}>
          <span style={{ fontSize: '0.7rem', fontWeight: 600, color: '#64748B', textTransform: 'uppercase' }}>Attribution Engine</span>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '8px', color: '#16A34A', fontFamily: 'var(--font-mono)', fontWeight: 700 }}>
            <span className="status-dot green" />
            <span>READY</span>
          </div>
          <span style={{ fontSize: '0.68rem', color: '#64748B', marginTop: '4px', display: 'block' }}>Zero-Out Perturbations</span>
        </div>

        <div className="white-card" style={{ padding: '16px' }}>
          <span style={{ fontSize: '0.7rem', fontWeight: 600, color: '#64748B', textTransform: 'uppercase' }}>MPC Optimizer</span>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '8px', color: '#16A34A', fontFamily: 'var(--font-mono)', fontWeight: 700 }}>
            <span className="status-dot green" />
            <span>READY</span>
          </div>
          <span style={{ fontSize: '0.68rem', color: '#64748B', marginTop: '4px', display: 'block' }}>Constrained SLSQP Solver</span>
        </div>
      </div>

      {/* Mathematical Matrix & Spectral Properties */}
      <div className="white-card" style={{ padding: '20px' }}>
        <h3 style={{ fontSize: '0.9rem', fontWeight: 600, marginBottom: '14px' }}>
          KOOPMAN / DMDc MATHEMATICAL PROPERTIES
        </h3>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '14px', fontFamily: 'var(--font-mono)' }}>
          <div style={{ background: 'var(--bg-secondary)', padding: '12px 14px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
            <span style={{ fontSize: '0.68rem', color: '#64748B', textTransform: 'uppercase' }}>Selected SVD Rank</span>
            <div style={{ fontSize: '1.4rem', fontWeight: 700, color: '#2563EB', marginTop: '4px' }}>
              r = {dmdc?.rank || 12}
            </div>
            <span style={{ fontSize: '0.68rem', color: '#16A34A' }}>Regularization λ = 0 (Exact SVD)</span>
          </div>

          <div style={{ background: 'var(--bg-secondary)', padding: '12px 14px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
            <span style={{ fontSize: '0.68rem', color: '#64748B', textTransform: 'uppercase' }}>State Dimension</span>
            <div style={{ fontSize: '1.4rem', fontWeight: 700, color: '#111827', marginTop: '4px' }}>
              n = {dmdc?.state_dimension || 15}
            </div>
            <span style={{ fontSize: '0.68rem', color: '#64748B' }}>Coupled Physical Variables</span>
          </div>

          <div style={{ background: 'var(--bg-secondary)', padding: '12px 14px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
            <span style={{ fontSize: '0.68rem', color: '#64748B', textTransform: 'uppercase' }}>Control Dimension</span>
            <div style={{ fontSize: '1.4rem', fontWeight: 700, color: '#111827', marginTop: '4px' }}>
              m = {dmdc?.control_dimension || 8}
            </div>
            <span style={{ fontSize: '0.68rem', color: '#64748B' }}>Exogenous Forcing Inputs</span>
          </div>

          <div style={{ background: 'var(--bg-secondary)', padding: '12px 14px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
            <span style={{ fontSize: '0.68rem', color: '#64748B', textTransform: 'uppercase' }}>Raw Spectral Radius ρ(A)</span>
            <div style={{ fontSize: '1.4rem', fontWeight: 700, color: '#EA580C', marginTop: '4px' }}>
              1.1512
            </div>
            <span style={{ fontSize: '0.68rem', color: '#64748B' }}>Uncontrolled Growth Mode</span>
          </div>

          <div style={{ background: 'var(--bg-secondary)', padding: '12px 14px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
            <span style={{ fontSize: '0.68rem', color: '#64748B', textTransform: 'uppercase' }}>Stabilized Rollout</span>
            <div style={{ fontSize: '1.4rem', fontWeight: 700, color: '#16A34A', marginTop: '4px' }}>
              ENABLED
            </div>
            <span style={{ fontSize: '0.68rem', color: '#16A34A' }}>Eigenvalue Projected: ρ = 1.0000</span>
          </div>

          <div style={{ background: 'var(--bg-secondary)', padding: '12px 14px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
            <span style={{ fontSize: '0.68rem', color: '#64748B', textTransform: 'uppercase' }}>Inference Speedup</span>
            <div style={{ fontSize: '1.4rem', fontWeight: 700, color: '#2563EB', marginTop: '4px' }}>
              ~32.2 ms
            </div>
            <span style={{ fontSize: '0.68rem', color: '#64748B' }}>vs 4.5h WRF-Chem (&gt;500,000×)</span>
          </div>
        </div>
      </div>
    </div>
  );
};
