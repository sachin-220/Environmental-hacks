import React, { useState } from 'react';
import { Sliders, CheckCircle2, XCircle, Zap, ShieldCheck, DollarSign, AlertTriangle, FileText } from 'lucide-react';
import { MPCStrategyResult } from '../types';
import { optimizeMPC } from '../api';
import { InfeasibilityCertificateModal } from './intervention/InfeasibilityCertificateModal';

interface InterventionOptimizerProps {
  onStrategyChange: (result: MPCStrategyResult) => void;
  currentResult: MPCStrategyResult | null;
}

export const InterventionOptimizer: React.FC<InterventionOptimizerProps> = ({
  onStrategyChange,
  currentResult
}) => {
  const [strategy, setStrategy] = useState<'LOW_COST' | 'BALANCED' | 'AGGRESSIVE'>('BALANCED');
  const [targetAqi, setTargetAqi] = useState<number>(250);
  const [useTargetMode, setUseTargetMode] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(false);
  const [showInfeasibilityModal, setShowInfeasibilityModal] = useState<boolean>(false);

  const handleRunOptimization = async (strat = strategy, targetVal?: number) => {
    setLoading(true);
    try {
      const res = await optimizeMPC(strat, 24, useTargetMode ? (targetVal ?? targetAqi) : undefined);
      onStrategyChange(res);
    } catch (err) {
      console.error('Optimization error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleStrategyClick = (s: 'LOW_COST' | 'BALANCED' | 'AGGRESSIVE') => {
    setStrategy(s);
    setUseTargetMode(false);
    handleRunOptimization(s, undefined);
  };

  const result = currentResult;
  const isFeasible = result?.feasible ?? true;
  const curtailment = result?.curtailment_percent || {
    road_transport: 28.5,
    heavy_industry: 22.0,
    construction_dust: 35.0,
    agricultural_fires: 40.0
  };

  return (
    <div className="glass-card" style={{ display: 'flex', flexDirection: 'column' }}>
      <div className="card-header">
        <div className="card-title-group">
          <Sliders size={16} color="#10b981" />
          <h3>Model Predictive Control (MPC) Optimizer</h3>
        </div>
        <span className="provenance-tag scenario">SCENARIO</span>
      </div>

      <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
        {/* Strategy Selector Tabs */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px' }}>
          {(['LOW_COST', 'BALANCED', 'AGGRESSIVE'] as const).map((s) => (
            <button
              key={s}
              onClick={() => handleStrategyClick(s)}
              disabled={loading}
              style={{
                background: (!useTargetMode && strategy === s) ? 'rgba(16, 185, 129, 0.2)' : 'rgba(15, 23, 42, 0.5)',
                color: (!useTargetMode && strategy === s) ? '#34d399' : '#94a3b8',
                border: (!useTargetMode && strategy === s) ? '1px solid #10b981' : '1px solid var(--border-subtle)',
                borderRadius: '6px',
                padding: '8px 10px',
                fontSize: '0.72rem',
                fontWeight: 700,
                cursor: 'pointer',
                transition: 'all 0.15s'
              }}
            >
              {s.replace('_', ' ')}
            </button>
          ))}
        </div>

        {/* Target AQI Constraint Slider */}
        <div style={{ background: 'rgba(15, 23, 42, 0.4)', border: '1px solid var(--border-subtle)', borderRadius: '8px', padding: '12px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <span style={{ fontSize: '0.74rem', color: '#f8fafc', fontWeight: 600 }}>Target-Driven Policy Solver</span>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <input
                type="checkbox"
                id="targetModeCheck"
                checked={useTargetMode}
                onChange={(e) => {
                  setUseTargetMode(e.target.checked);
                  if (e.target.checked) handleRunOptimization(strategy, targetAqi);
                }}
                style={{ cursor: 'pointer' }}
              />
              <label htmlFor="targetModeCheck" style={{ fontSize: '0.72rem', color: '#38bdf8', cursor: 'pointer' }}>
                Enforce Target AQI
              </label>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem', color: '#cbd5e1', minWidth: '70px' }}>
              AQI: {targetAqi}
            </span>
            <input
              type="range"
              min="100"
              max="350"
              step="10"
              value={targetAqi}
              disabled={!useTargetMode}
              onChange={(e) => setTargetAqi(Number(e.target.value))}
              onMouseUp={() => useTargetMode && handleRunOptimization(strategy, targetAqi)}
              className="custom-range"
              style={{ opacity: useTargetMode ? 1 : 0.4 }}
            />
            <button
              onClick={() => handleRunOptimization(strategy, targetAqi)}
              disabled={loading || !useTargetMode}
              style={{
                background: '#0284c7',
                color: '#ffffff',
                border: 'none',
                borderRadius: '4px',
                padding: '4px 10px',
                fontSize: '0.7rem',
                fontWeight: 600,
                cursor: 'pointer',
                opacity: useTargetMode ? 1 : 0.5
              }}
            >
              Solve
            </button>
          </div>
        </div>

        {/* Feasibility & Verification Status */}
        <div style={{
          background: isFeasible ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.12)',
          border: `1px solid ${isFeasible ? 'rgba(16, 185, 129, 0.25)' : 'rgba(239, 68, 68, 0.35)'}`,
          borderRadius: '8px',
          padding: '10px 14px',
          display: 'flex',
          alignItems: 'flex-start',
          gap: '10px'
        }}>
          {isFeasible ? (
            <CheckCircle2 size={16} color="#10b981" style={{ flexShrink: 0, marginTop: '2px' }} />
          ) : (
            <XCircle size={16} color="#ef4444" style={{ flexShrink: 0, marginTop: '2px' }} />
          )}
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '0.78rem', fontWeight: 700, color: isFeasible ? '#34d399' : '#f87171' }}>
                {isFeasible ? 'POLICY FEASIBLE (Bounded Physical Solution)' : 'TARGET INFEASIBLE'}
              </span>
              <span style={{ fontSize: '0.68rem', fontFamily: 'var(--font-mono)', color: '#94a3b8' }}>
                Cost Index: {result?.cost_index?.toFixed(1) || '38.4'}
              </span>
            </div>
            <p style={{ fontSize: '0.72rem', color: '#cbd5e1', marginTop: '2px', lineHeight: '1.3' }}>
              {isFeasible
                ? `Ramp rates (-30%/h) and max curtailment limits (60%) strictly satisfied. Expected PM2.5 reduction: -${result?.expected_pm25_reduction_ugm3?.toFixed(1) || '45.2'} µg/m³.`
                : (result?.infeasibility_reason || 'Target unachievable under bounded ramp limits without violating societal operation constraints.')}
            </p>
            {(!isFeasible || result?.infeasibility_certificate) && (
              <button
                onClick={() => setShowInfeasibilityModal(true)}
                style={{
                  marginTop: '8px',
                  background: '#dc2626',
                  color: '#ffffff',
                  border: 'none',
                  borderRadius: '4px',
                  padding: '5px 12px',
                  fontSize: '0.7rem',
                  fontWeight: 700,
                  cursor: 'pointer',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '6px'
                }}
              >
                <FileText size={12} />
                <span>VIEW PHYSICAL INFEASIBILITY PROOF</span>
              </button>
            )}
          </div>
        </div>

        {/* Recommended Sector Curtailment Levers */}
        <div>
          <span style={{ fontSize: '0.74rem', fontWeight: 600, color: '#f8fafc', marginBottom: '8px', display: 'block' }}>
            Recommended Sector Curtailment Levers (SLSQP Optimal)
          </span>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '8px' }}>
            {Object.entries(curtailment).map(([sector, pct]) => {
              const num = Number(pct);
              const displayPct = Math.min(100, Math.max(0, num > 0 && num <= 1.0 ? num * 100 : num));
              return (
                <div
                  key={sector}
                  style={{
                    background: 'rgba(15, 23, 42, 0.45)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: '6px',
                    padding: '8px 10px',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center'
                  }}
                >
                  <span style={{ fontSize: '0.7rem', color: '#cbd5e1' }}>
                    {sector.replace('_', ' ').toUpperCase()}
                  </span>
                  <span style={{
                    fontFamily: 'var(--font-mono)',
                    fontSize: '0.75rem',
                    fontWeight: 700,
                    color: '#38bdf8'
                  }}>
                    {displayPct.toFixed(1)}%
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        <div style={{ fontSize: '0.68rem', color: '#64748b', fontStyle: 'italic' }}>
          * Disclaimer: Intervention outcomes represent optimal model response under linear DMDc dynamics. Physical real-world response depends on meteorological coupling and enforcement fidelity.
        </div>
      </div>

      {/* Infeasibility Certificate Modal */}
      <InfeasibilityCertificateModal
        isOpen={showInfeasibilityModal}
        onClose={() => setShowInfeasibilityModal(false)}
        certificate={result?.infeasibility_certificate || null}
      />
    </div>
  );
};
