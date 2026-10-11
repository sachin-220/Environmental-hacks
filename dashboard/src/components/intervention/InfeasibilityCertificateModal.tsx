import React from 'react';
import { X, ShieldAlert, AlertTriangle, Scale, FileText, Check, ArrowRight } from 'lucide-react';
import { InfeasibilityCertificate } from '../../types';

interface InfeasibilityCertificateModalProps {
  isOpen: boolean;
  onClose: () => void;
  certificate: InfeasibilityCertificate | null;
}

export const InfeasibilityCertificateModal: React.FC<InfeasibilityCertificateModalProps> = ({
  isOpen,
  onClose,
  certificate
}) => {
  if (!isOpen || !certificate) return null;

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(2, 6, 23, 0.85)',
        backdropFilter: 'blur(8px)',
        zIndex: 9999,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '20px'
      }}
    >
      <div
        className="glass-card"
        style={{
          width: '100%',
          maxWidth: '680px',
          background: '#090d16',
          border: '2px solid #ef4444',
          borderRadius: '12px',
          boxShadow: '0 0 35px rgba(239, 68, 68, 0.35)',
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column'
        }}
      >
        {/* Header with Official Stamp styling */}
        <div
          style={{
            background: 'linear-gradient(90deg, rgba(239, 68, 68, 0.25) 0%, rgba(153, 27, 27, 0.4) 100%)',
            borderBottom: '1px solid rgba(239, 68, 68, 0.4)',
            padding: '16px 20px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div
              style={{
                width: '34px',
                height: '34px',
                borderRadius: '8px',
                background: 'rgba(239, 68, 68, 0.2)',
                border: '1px solid #ef4444',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
            >
              <ShieldAlert size={20} color="#ef4444" />
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span
                  style={{
                    fontSize: '0.68rem',
                    fontFamily: 'var(--font-mono)',
                    color: '#fca5a5',
                    background: 'rgba(239, 68, 68, 0.3)',
                    padding: '2px 6px',
                    borderRadius: '4px',
                    border: '1px solid rgba(239, 68, 68, 0.5)'
                  }}
                >
                  {certificate.certificate_id}
                </span>
                <span style={{ fontSize: '0.68rem', color: '#94a3b8' }}>ANTI-GREENWASHING PROOF</span>
              </div>
              <h2 style={{ fontSize: '1.05rem', fontWeight: 800, color: '#fee2e2', marginTop: '2px', letterSpacing: '0.02em' }}>
                PHYSICAL INFEASIBILITY CERTIFICATE
              </h2>
            </div>
          </div>

          <button
            onClick={onClose}
            style={{
              background: 'transparent',
              border: 'none',
              color: '#94a3b8',
              cursor: 'pointer',
              padding: '6px'
            }}
          >
            <X size={20} />
          </button>
        </div>

        {/* Certificate Body */}
        <div style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px', maxHeight: '80vh', overflowY: 'auto' }}>
          {/* Status Banner */}
          <div
            style={{
              border: '2px dashed rgba(239, 68, 68, 0.6)',
              borderRadius: '8px',
              padding: '14px 18px',
              background: 'rgba(239, 68, 68, 0.08)',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center'
            }}
          >
            <div>
              <div style={{ fontSize: '0.72rem', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                Governing Physical Law
              </div>
              <div style={{ fontSize: '0.92rem', fontWeight: 700, color: '#f87171', marginTop: '2px' }}>
                {certificate.governing_law}
              </div>
              <div style={{ fontSize: '0.72rem', color: '#cbd5e1', marginTop: '4px' }}>
                Issued by: {certificate.authority}
              </div>
            </div>

            {/* Official Red Stamp Box */}
            <div
              style={{
                border: '3px solid #ef4444',
                color: '#ef4444',
                padding: '6px 14px',
                borderRadius: '6px',
                fontWeight: 900,
                fontSize: '0.82rem',
                letterSpacing: '0.08em',
                transform: 'rotate(-5deg)',
                textAlign: 'center',
                textTransform: 'uppercase',
                background: 'rgba(239, 68, 68, 0.12)'
              }}
            >
              PHYSICALLY<br />INFEASIBLE
            </div>
          </div>

          {/* Numerical Proof Breakdown */}
          <div style={{ background: 'rgba(15, 23, 42, 0.7)', border: '1px solid var(--border-subtle)', borderRadius: '8px', padding: '16px' }}>
            <h4 style={{ fontSize: '0.78rem', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: '12px' }}>
              Conservation of Mass Breakdown (Airshed Boundary Conditions)
            </h4>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px' }}>
              <div style={{ background: '#070c14', padding: '12px', borderRadius: '6px', border: '1px solid rgba(255, 255, 255, 0.06)' }}>
                <span style={{ fontSize: '0.68rem', color: '#94a3b8', display: 'block' }}>Transboundary Stubble Inflow</span>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: '1.25rem', fontWeight: 700, color: '#f59e0b' }}>
                  {certificate.transboundary_advection_pm25} µg/m³
                </span>
                <span style={{ fontSize: '0.65rem', color: '#64748b' }}>Uncontrollable intra-Delhi</span>
              </div>

              <div style={{ background: '#070c14', padding: '12px', borderRadius: '6px', border: '1px solid rgba(239, 68, 68, 0.3)' }}>
                <span style={{ fontSize: '0.68rem', color: '#fca5a5', display: 'block' }}>Zero-Emission Local Floor</span>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: '1.25rem', fontWeight: 700, color: '#ef4444' }}>
                  {certificate.zero_local_emission_floor_pm25} µg/m³
                </span>
                <span style={{ fontSize: '0.65rem', color: '#f87171' }}>Theoretical Min. (AQI {certificate.zero_local_emission_floor_aqi})</span>
              </div>

              <div style={{ background: '#070c14', padding: '12px', borderRadius: '6px', border: '1px solid rgba(16, 185, 129, 0.3)' }}>
                <span style={{ fontSize: '0.68rem', color: '#6ee7b7', display: 'block' }}>Max Achievable Target</span>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: '1.25rem', fontWeight: 700, color: '#10b981' }}>
                  AQI ≤ {certificate.minimum_achievable_aqi}
                </span>
                <span style={{ fontSize: '0.65rem', color: '#34d399' }}>Realistic physical bound</span>
              </div>
            </div>
          </div>

          {/* Mathematical Proof Narrative */}
          <div style={{ background: 'rgba(239, 68, 68, 0.05)', borderLeft: '3px solid #ef4444', padding: '12px 16px', borderRadius: '0 6px 6px 0' }}>
            <span style={{ fontSize: '0.74rem', fontWeight: 700, color: '#fca5a5', textTransform: 'uppercase', display: 'block', marginBottom: '4px' }}>
              Mathematical Proof of Infeasibility
            </span>
            <p style={{ fontSize: '0.74rem', color: '#cbd5e1', lineHeight: '1.45', margin: 0 }}>
              {certificate.mathematical_proof}
            </p>
          </div>

          {/* Anti-Greenwashing Recommendation */}
          <div style={{ background: 'rgba(30, 41, 59, 0.5)', borderRadius: '6px', padding: '12px 14px', border: '1px solid rgba(255, 255, 255, 0.08)' }}>
            <span style={{ fontSize: '0.72rem', fontWeight: 700, color: '#38bdf8', display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '4px' }}>
              <Scale size={14} /> Regulatory & Judicial Guidance:
            </span>
            <p style={{ fontSize: '0.72rem', color: '#94a3b8', lineHeight: '1.4', margin: 0 }}>
              Mandating local Delhi shutdowns to achieve <strong>AQI {certificate.demanded_target_aqi}</strong> constitutes wasteful public expenditure without physical clean-air yield. AERIS advises authorities to adjust the target to <strong>AQI {certificate.minimum_achievable_aqi}</strong> or engage the <strong>Airshed Federalism Compact</strong> to remediate upwind stubble burning.
            </p>
          </div>

          {/* Actions */}
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '4px' }}>
            <button
              onClick={onClose}
              style={{
                background: '#1e293b',
                color: '#cbd5e1',
                border: '1px solid var(--border-subtle)',
                borderRadius: '6px',
                padding: '8px 16px',
                fontSize: '0.75rem',
                fontWeight: 600,
                cursor: 'pointer'
              }}
            >
              Close Proof
            </button>
            <button
              onClick={() => {
                alert(`Certificate ${certificate.certificate_id} recorded in statutory compliance audit log.`);
                onClose();
              }}
              style={{
                background: '#dc2626',
                color: '#ffffff',
                border: 'none',
                borderRadius: '6px',
                padding: '8px 16px',
                fontSize: '0.75rem',
                fontWeight: 700,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '6px'
              }}
            >
              <FileText size={14} />
              <span>Record In Audit Log</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
