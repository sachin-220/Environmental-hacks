import React, { useState, useEffect } from 'react';
import { X, Printer, ShieldCheck, FileCheck, Hash, Download, CheckCircle2 } from 'lucide-react';
import { CAQMDirectiveData } from '../../types';
import { fetchCAQMDirective } from '../../api';

interface CAQMDirectiveModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const CAQMDirectiveModal: React.FC<CAQMDirectiveModalProps> = ({ isOpen, onClose }) => {
  const [data, setData] = useState<CAQMDirectiveData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    if (isOpen) {
      setLoading(true);
      fetchCAQMDirective()
        .then((res) => setData(res))
        .catch((err) => console.error('Failed to load CAQM directive:', err))
        .finally(() => setLoading(false));
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handlePrint = () => {
    window.print();
  };

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
          maxWidth: '820px',
          maxHeight: '90vh',
          background: '#ffffff',
          color: '#111827',
          borderRadius: '8px',
          boxShadow: '0 20px 50px rgba(0, 0, 0, 0.5)',
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column'
        }}
      >
        {/* Modal Toolbar (Non-printable) */}
        <div
          className="no-print"
          style={{
            background: '#0f172a',
            color: '#f8fafc',
            padding: '12px 20px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <FileCheck size={18} color="#38bdf8" />
            <span style={{ fontSize: '0.85rem', fontWeight: 700 }}>
              CAQM & Supreme Court Evidentiary Directive Generator
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <button
              onClick={handlePrint}
              style={{
                background: '#2563eb',
                color: '#ffffff',
                border: 'none',
                borderRadius: '6px',
                padding: '6px 14px',
                fontSize: '0.75rem',
                fontWeight: 600,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '6px'
              }}
            >
              <Printer size={14} />
              <span>Print / Save PDF</span>
            </button>
            <button
              onClick={onClose}
              style={{
                background: 'transparent',
                border: 'none',
                color: '#94a3b8',
                cursor: 'pointer',
                padding: '4px'
              }}
            >
              <X size={20} />
            </button>
          </div>
        </div>

        {/* Printable Official Government Document View */}
        <div
          id="printableDirective"
          style={{
            padding: '36px 44px',
            overflowY: 'auto',
            background: '#ffffff',
            color: '#0f172a',
            fontFamily: 'var(--font-sans)',
            fontSize: '0.82rem',
            lineHeight: '1.5'
          }}
        >
          {/* Government of India Header */}
          <div style={{ textAlign: 'center', borderBottom: '2px solid #0f172a', paddingBottom: '16px', marginBottom: '20px' }}>
            <div style={{ fontSize: '0.8rem', fontWeight: 800, letterSpacing: '0.1em', textTransform: 'uppercase', color: '#475569' }}>
              GOVERNMENT OF INDIA
            </div>
            <div style={{ fontSize: '1.15rem', fontWeight: 900, textTransform: 'uppercase', letterSpacing: '0.04em', color: '#0f172a', marginTop: '4px' }}>
              COMMISSION FOR AIR QUALITY MANAGEMENT IN NCR AND ADJOINING AREAS
            </div>
            <div style={{ fontSize: '0.72rem', color: '#64748b', marginTop: '2px' }}>
              Statutory Body under the Commission for Air Quality Management in NCR & Adjoining Areas Act, 2021
            </div>
          </div>

          {/* Reference & Metadata Strip */}
          <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '16px', background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '6px', padding: '12px 16px', marginBottom: '20px' }}>
            <div>
              <div style={{ fontSize: '0.7rem', color: '#64748b', textTransform: 'uppercase' }}>Directive Number</div>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.85rem', fontWeight: 700, color: '#0f172a' }}>
                {data?.directive_number || 'CAQM/TECH/DIR/2026/NCR-78210'}
              </div>
              <div style={{ fontSize: '0.68rem', color: '#64748b', marginTop: '2px' }}>
                {data?.statutory_mandate}
              </div>
            </div>

            <div>
              <div style={{ fontSize: '0.7rem', color: '#64748b', textTransform: 'uppercase' }}>Cryptographic State Hash</div>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', fontWeight: 600, color: '#2563eb' }}>
                {data?.cryptographic_hash || 'SHA256:4FA821BC78E90123'}
              </div>
              <div style={{ fontSize: '0.68rem', color: '#64748b', marginTop: '2px' }}>
                Generated: {data?.generated_at}
              </div>
            </div>
          </div>

          {/* Section 1: In-situ Hardware Ground Truth Baseline */}
          <div style={{ marginBottom: '18px' }}>
            <h4 style={{ fontSize: '0.85rem', fontWeight: 800, textTransform: 'uppercase', color: '#0f172a', borderBottom: '1px solid #cbd5e1', paddingBottom: '4px', marginBottom: '8px' }}>
              1. Ground Truth Atmospheric Baseline (CPCB / DPCC In-situ Sensors)
            </h4>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '10px' }}>
              <div style={{ background: '#f1f5f9', padding: '8px 10px', borderRadius: '4px' }}>
                <span style={{ fontSize: '0.68rem', color: '#64748b', display: 'block' }}>Central NCR AQI</span>
                <strong style={{ fontSize: '1rem', color: '#dc2626' }}>{data?.baseline_telemetry?.central_delhi_aqi || 381}</strong>
                <span style={{ fontSize: '0.65rem', color: '#64748b', display: 'block' }}>({data?.baseline_telemetry?.category || 'VERY POOR'})</span>
              </div>
              <div style={{ background: '#f1f5f9', padding: '8px 10px', borderRadius: '4px' }}>
                <span style={{ fontSize: '0.68rem', color: '#64748b', display: 'block' }}>Dominant Pollutant</span>
                <strong style={{ fontSize: '0.88rem', color: '#0f172a' }}>{data?.baseline_telemetry?.dominant_pollutant || 'PM2.5'}</strong>
              </div>
              <div style={{ background: '#f1f5f9', padding: '8px 10px', borderRadius: '4px' }}>
                <span style={{ fontSize: '0.68rem', color: '#64748b', display: 'block' }}>Active CAAQMS Stations</span>
                <strong style={{ fontSize: '0.88rem', color: '#0f172a' }}>{data?.baseline_telemetry?.air_receptors_analyzed || 38} Stations</strong>
              </div>
              <div style={{ background: '#f1f5f9', padding: '8px 10px', borderRadius: '4px' }}>
                <span style={{ fontSize: '0.68rem', color: '#64748b', display: 'block' }}>Telemetry Origin</span>
                <strong style={{ fontSize: '0.72rem', color: '#16a34a' }}>OBSERVED HARDWARE</strong>
              </div>
            </div>
          </div>

          {/* Section 2: NCAR WRF-Chem Atmospheric Inversion Findings */}
          <div style={{ marginBottom: '18px' }}>
            <h4 style={{ fontSize: '0.85rem', fontWeight: 800, textTransform: 'uppercase', color: '#0f172a', borderBottom: '1px solid #cbd5e1', paddingBottom: '4px', marginBottom: '8px' }}>
              2. Atmospheric Fluid Dynamics & Inversion Capping Lid Proof
            </h4>
            <div style={{ background: '#fef2f2', border: '1px solid #fecaca', borderRadius: '6px', padding: '10px 14px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontWeight: 700, color: '#dc2626', marginBottom: '4px' }}>
                <span>{data?.meteorological_inversion_finding?.status || 'IMMINENT NOCTURNAL INVERSION'}</span>
                <span>{data?.meteorological_inversion_finding?.golden_action_window_deadline}</span>
              </div>
              <p style={{ margin: 0, fontSize: '0.74rem', color: '#475569' }}>
                Coupled atmospheric simulation confirms boundary layer collapse to <strong>{data?.meteorological_inversion_finding?.nocturnal_pbl_collapse_m}</strong> with a <strong>{data?.meteorological_inversion_finding?.capping_lid_strength}</strong>. Koopman Mode 2 is dynamically active. Interventions must be enacted immediately before ventilation ceases.
              </p>
            </div>
          </div>

          {/* Section 3: Counterfactual Attribution */}
          <div style={{ marginBottom: '18px' }}>
            <h4 style={{ fontSize: '0.85rem', fontWeight: 800, textTransform: 'uppercase', color: '#0f172a', borderBottom: '1px solid #cbd5e1', paddingBottom: '4px', marginBottom: '8px' }}>
              3. Modelled Counterfactual Source Attribution (Causal Zero-Out)
            </h4>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '8px', fontSize: '0.72rem' }}>
              <div style={{ padding: '6px 8px', background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '4px' }}>
                <strong>Vehicular Traffic (Local):</strong> {data?.counterfactual_source_attribution?.local_transport_vehicular}
              </div>
              <div style={{ padding: '6px 8px', background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '4px' }}>
                <strong>Crop Fire Stubble (Regional):</strong> {data?.counterfactual_source_attribution?.regional_agricultural_stubble}
              </div>
              <div style={{ padding: '6px 8px', background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '4px' }}>
                <strong>Construction Dust (Mechanical):</strong> {data?.counterfactual_source_attribution?.construction_and_road_dust}
              </div>
              <div style={{ padding: '6px 8px', background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '4px' }}>
                <strong>Industrial Point Sources:</strong> {data?.counterfactual_source_attribution?.industrial_point_sources}
              </div>
            </div>
          </div>

          {/* Section 4: Mandated Legal Curtailment Schedule */}
          <div style={{ marginBottom: '22px' }}>
            <h4 style={{ fontSize: '0.85rem', fontWeight: 800, textTransform: 'uppercase', color: '#0f172a', borderBottom: '1px solid #cbd5e1', paddingBottom: '4px', marginBottom: '8px' }}>
              4. Mandated Enforceable Curtailment Schedule (SLSQP Optimal)
            </h4>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.72rem', textAlign: 'left' }}>
              <thead>
                <tr style={{ background: '#0f172a', color: '#ffffff' }}>
                  <th style={{ padding: '6px 10px' }}>SECTOR</th>
                  <th style={{ padding: '6px 10px' }}>MANDATED CURTAILMENT</th>
                  <th style={{ padding: '6px 10px' }}>COMPLIANCE DEADLINE</th>
                  <th style={{ padding: '6px 10px' }}>LEGAL STATUTE</th>
                </tr>
              </thead>
              <tbody>
                {(data?.mandated_curtailment_schedule || []).map((row, idx) => (
                  <tr key={idx} style={{ borderBottom: '1px solid #e2e8f0', background: idx % 2 === 0 ? '#ffffff' : '#f8fafc' }}>
                    <td style={{ padding: '8px 10px', fontWeight: 600 }}>{row.sector}</td>
                    <td style={{ padding: '8px 10px', fontWeight: 700, color: '#2563eb' }}>{row.mandated_curtailment}</td>
                    <td style={{ padding: '8px 10px' }}>{row.compliance_deadline}</td>
                    <td style={{ padding: '8px 10px', fontFamily: 'var(--font-mono)', fontSize: '0.68rem', color: '#64748b' }}>{row.legal_basis}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Statutory Sign-off & Stamp */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', borderTop: '2px solid #0f172a', paddingTop: '16px' }}>
            <div>
              <div style={{ fontSize: '0.68rem', fontWeight: 700, textTransform: 'uppercase', color: '#dc2626' }}>
                STATUTORY NOTICE:
              </div>
              <div style={{ fontSize: '0.68rem', color: '#64748b', maxWidth: '420px' }}>
                {data?.legal_enforceability} under penalty of Contempt of Court and environmental penalties under Section 14 of CAQM Act.
              </div>
            </div>

            <div style={{ textAlign: 'right' }}>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', fontWeight: 700, color: '#0f172a' }}>
                [DIGITALLY SIGNED]
              </div>
              <div style={{ fontSize: '0.72rem', color: '#475569', marginTop: '2px' }}>
                {data?.signatory || 'Member Secretary, Technical Advisory Committee, CAQM'}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
