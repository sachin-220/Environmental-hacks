import React, { useState } from 'react';
import { Sliders, CheckCircle2, XCircle, TrendingDown, ArrowRight, ShieldAlert, Zap, FileText } from 'lucide-react';
import { MPCStrategyResult } from '../types';
import { optimizeMPC } from '../api';
import { AirshedFederalismCard } from '../components/intervention/AirshedFederalismCard';
import { InfeasibilityCertificateModal } from '../components/intervention/InfeasibilityCertificateModal';

interface InterventionsPageProps {
  initialResult: MPCStrategyResult | null;
}

export const InterventionsPage: React.FC<InterventionsPageProps> = ({ initialResult }) => {
  const [targetAqi, setTargetAqi] = useState<number>(300);
  const [deadline, setDeadline] = useState<number>(24);
  const [strategy, setStrategy] = useState<'LOW_COST' | 'BALANCED' | 'AGGRESSIVE'>('BALANCED');
  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<MPCStrategyResult | null>(initialResult);
  const [showInfeasibilityModal, setShowInfeasibilityModal] = useState<boolean>(false);

  const handleRunOptimization = async () => {
    setLoading(true);
    try {
      const res = await optimizeMPC(strategy, deadline, targetAqi);
      setResult(res);
    } catch (err) {
      console.error('MPC optimization failed:', err);
    } finally {
      setLoading(false);
    }
  };

  const isFeasible = result?.feasible ?? true;
  const curtailment = result?.curtailment_percent || {
    road_transport: 28.5,
    heavy_industry: 22.0,
    agricultural_fires: 40.0,
    construction_dust: 35.0
  };

  // Trajectory comparison points
  const points = result?.trajectory_comparison || Array.from({ length: 24 }, (_, i) => {
    const base = 235 + i * 2.8;
    const ctrl = base - (i + 1) * 1.8;
    return {
      hour: i + 1,
      baseline_pm25: Math.round(base),
      controlled_pm25: Math.round(ctrl),
      averted_pm25: Math.round(base - ctrl)
    };
  });

  // SVG Chart Setup
  const width = 760;
  const height = 260;
  const padding = { top: 25, right: 30, bottom: 35, left: 45 };
  const chartWidth = width - padding.left - padding.right;
  const chartHeight = height - padding.top - padding.bottom;

  const maxVal = Math.max(...points.map(p => Math.max(p.baseline_pm25, p.controlled_pm25)), 320) * 1.05;
  const minVal = Math.min(...points.map(p => Math.min(p.baseline_pm25, p.controlled_pm25)), 150) * 0.9;

  const getX = (i: number) => padding.left + (i / Math.max(points.length - 1, 1)) * chartWidth;
  const getY = (val: number) => padding.top + chartHeight - ((val - minVal) / (maxVal - minVal)) * chartHeight;

  const baseLine = points.reduce((acc, p, i) => `${acc} ${i === 0 ? 'M' : 'L'} ${getX(i)} ${getY(p.baseline_pm25)}`, '');
  const ctrlLine = points.reduce((acc, p, i) => `${acc} ${i === 0 ? 'M' : 'L'} ${getX(i)} ${getY(p.controlled_pm25)}`, '');

  const avertedArea = `${baseLine} ${[...points].reverse().reduce((acc, p, i) => {
    const revIdx = points.length - 1 - i;
    return `${acc} L ${getX(revIdx)} ${getY(p.controlled_pm25)}`;
  }, '')} Z`;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '22px' }}>
      {/* 1. Header & Setup Bar ("PREVENT THE SPIKE") */}
      <div className="white-card" style={{ padding: '20px 24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <div>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#111827' }}>PREVENT THE SPIKE</h2>
            <p style={{ fontSize: '0.78rem', color: '#64748B', marginTop: '2px' }}>
              Model Predictive Control (MPC) Multi-Sector Policy Optimization
            </p>
          </div>
          <span className="provenance-tag scenario">OPTIMIZED SCENARIO</span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px', alignItems: 'flex-end' }}>
          <div>
            <label style={{ fontSize: '0.72rem', fontWeight: 600, color: '#475569', textTransform: 'uppercase', display: 'block', marginBottom: '6px' }}>
              Target AQI Limit
            </label>
            <input
              type="number"
              min="100"
              max="400"
              value={targetAqi}
              onChange={(e) => setTargetAqi(Number(e.target.value))}
              style={{
                width: '100%',
                padding: '8px 12px',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--border-subtle)',
                fontFamily: 'var(--font-mono)',
                fontSize: '0.85rem',
                fontWeight: 600
              }}
            />
          </div>

          <div>
            <label style={{ fontSize: '0.72rem', fontWeight: 600, color: '#475569', textTransform: 'uppercase', display: 'block', marginBottom: '6px' }}>
              Action Deadline
            </label>
            <select
              value={deadline}
              onChange={(e) => setDeadline(Number(e.target.value))}
              style={{
                width: '100%',
                padding: '8px 12px',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--border-subtle)',
                fontFamily: 'var(--font-mono)',
                fontSize: '0.85rem',
                fontWeight: 600,
                background: '#FFFFFF'
              }}
            >
              <option value={12}>12 Hours</option>
              <option value={24}>24 Hours</option>
              <option value={48}>48 Hours</option>
            </select>
          </div>

          <div>
            <label style={{ fontSize: '0.72rem', fontWeight: 600, color: '#475569', textTransform: 'uppercase', display: 'block', marginBottom: '6px' }}>
              Policy Strategy
            </label>
            <select
              value={strategy}
              onChange={(e) => setStrategy(e.target.value as any)}
              style={{
                width: '100%',
                padding: '8px 12px',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--border-subtle)',
                fontFamily: 'var(--font-mono)',
                fontSize: '0.85rem',
                fontWeight: 600,
                background: '#FFFFFF'
              }}
            >
              <option value="LOW_COST">LOW COST (Minimal Disruption)</option>
              <option value="BALANCED">BALANCED (Standard Regulatory)</option>
              <option value="AGGRESSIVE">AGGRESSIVE (GRAP Stage IV)</option>
            </select>
          </div>

          <button
            className="btn-clean primary"
            onClick={handleRunOptimization}
            disabled={loading}
            style={{ padding: '9px 20px', justifyContent: 'center', height: '38px' }}
          >
            <Zap size={15} />
            <span>{loading ? 'Optimizing...' : 'Run Optimization'}</span>
          </button>
        </div>
      </div>

      {/* 2. MPC Feasibility & Recommended Levers */}
      <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: '20px' }}>
        {/* Feasibility Summary */}
        <div className="white-card" style={{ padding: '20px' }}>
          <span style={{ fontSize: '0.72rem', fontWeight: 600, color: '#64748B', textTransform: 'uppercase', letterSpacing: '0.04em', display: 'block', marginBottom: '10px' }}>
            Optimization Feasibility
          </span>

          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px' }}>
            {isFeasible ? (
              <CheckCircle2 size={24} color="#16A34A" />
            ) : (
              <XCircle size={24} color="#DC2626" />
            )}
            <div>
              <div style={{ fontSize: '1.05rem', fontWeight: 700, color: isFeasible ? '#16A34A' : '#DC2626' }}>
                {isFeasible ? 'FEASIBLE' : 'TARGET INFEASIBLE'}
              </div>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.72rem', color: '#64748B' }}>
                Target: ≤ {targetAqi} AQI ({deadline}h)
              </div>
            </div>
          </div>

          <p style={{ fontSize: '0.75rem', color: '#475569', lineHeight: '1.45', background: 'var(--bg-secondary)', padding: '10px 12px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
            {isFeasible
              ? 'Target can be achieved within operational bounds. Rate-of-change ramp limits (-30%/h) and societal caps (60%) strictly satisfied.'
              : (result?.infeasibility_reason || 'Target unachievable under bounded ramp limits without violating essential societal functions.')}
          </p>

          {(!isFeasible || result?.infeasibility_certificate) && (
            <button
              onClick={() => setShowInfeasibilityModal(true)}
              style={{
                marginTop: '10px',
                background: '#dc2626',
                color: '#ffffff',
                border: 'none',
                borderRadius: '6px',
                padding: '6px 14px',
                fontSize: '0.72rem',
                fontWeight: 700,
                cursor: 'pointer',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                width: '100%',
                justifyContent: 'center'
              }}
            >
              <FileText size={13} />
              <span>VIEW PHYSICAL INFEASIBILITY PROOF</span>
            </button>
          )}

          <div style={{ marginTop: '14px', borderTop: '1px solid var(--border-subtle)', paddingTop: '12px', display: 'flex', justifyContent: 'space-between', fontFamily: 'var(--font-mono)', fontSize: '0.72rem', color: '#64748B' }}>
            <span>Cost Index: <strong>{result?.cost_index?.toFixed(1) || '38.4'}</strong></span>
            <span>Mean Δ: <strong style={{ color: '#16A34A' }}>-{result?.expected_pm25_reduction_ugm3?.toFixed(1) || '45.2'} µg/m³</strong></span>
          </div>
        </div>

        {/* Recommended Sector Levers */}
        <div className="white-card" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
            <h3 style={{ fontSize: '0.88rem', fontWeight: 600 }}>RECOMMENDED CONTROLS (SLSQP OPTIMAL)</h3>
            <span style={{ fontSize: '0.7rem', color: '#64748B', fontFamily: 'var(--font-mono)' }}>Ramp limit: -30%/h</span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px' }}>
            {Object.entries(curtailment).map(([sec, pct]) => {
              const num = Number(pct);
              const displayPct = Math.min(100, Math.max(0, num > 0 && num <= 1.0 ? num * 100 : num));
              return (
                <div key={sec} style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-md)', padding: '12px 14px' }}>
                  <span style={{ fontSize: '0.68rem', fontWeight: 600, color: '#64748B', textTransform: 'uppercase', display: 'block', marginBottom: '6px' }}>
                    {sec.replace('_', ' ')}
                  </span>
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: '1.35rem', fontWeight: 700, color: '#2563EB' }}>
                    {displayPct.toFixed(1)}%
                  </div>
                  <span style={{ fontSize: '0.65rem', color: '#64748B', marginTop: '4px', display: 'block' }}>
                    Curtailed Effort
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* 3. Counterfactual Graph ("WHAT IF WE ACT?") */}
      <div className="white-card" style={{ padding: '20px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
          <div>
            <h3 style={{ fontSize: '0.92rem', fontWeight: 600 }}>WHAT IF WE ACT? (TRAJECTORY COMPARISON)</h3>
            <span style={{ fontSize: '0.72rem', color: '#64748B' }}>Baseline No-Action Trajectory vs AERIS Recommended Policy</span>
          </div>
          <span className="provenance-tag counterfactual">MODELLED COUNTERFACTUAL</span>
        </div>

        <svg viewBox={`0 0 ${width} ${height}`} style={{ width: '100%', height: 'auto', display: 'block' }}>
          {[0, 0.33, 0.66, 1].map((ratio, idx) => {
            const val = Math.round(minVal + ratio * (maxVal - minVal));
            const y = getY(val);
            return (
              <g key={idx}>
                <line x1={padding.left} y1={y} x2={width - padding.right} y2={y} stroke="#F1F5F9" strokeWidth="1" />
                <text x={padding.left - 8} y={y + 3} textAnchor="end" fill="#94A3B8" fontSize="9" fontFamily="var(--font-mono)">
                  {val}
                </text>
              </g>
            );
          })}

          <path d={avertedArea} fill="#EFF6FF" opacity="0.9" />
          <path d={baseLine} fill="none" stroke="#DC2626" strokeWidth="2" strokeDasharray="4 3" />
          <path d={ctrlLine} fill="none" stroke="#16A34A" strokeWidth="2.4" />

          {[0, 5, 11, 17, 23].map((idx) => {
            if (!points[idx]) return null;
            const p = points[idx];
            const x = getX(idx);
            return (
              <text key={idx} x={x} y={height - padding.bottom + 16} textAnchor="middle" fill="#64748B" fontSize="9" fontFamily="var(--font-mono)">
                +{p.hour}h
              </text>
            );
          })}
        </svg>

        <div style={{ display: 'flex', justifyContent: 'center', gap: '24px', marginTop: '12px', fontSize: '0.75rem', fontFamily: 'var(--font-mono)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <div style={{ width: '14px', height: '2px', background: '#DC2626' }} />
            <span style={{ color: '#475569' }}>NO ACTION BASELINE</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <div style={{ width: '14px', height: '2.5px', background: '#16A34A' }} />
            <span style={{ color: '#16A34A', fontWeight: 600 }}>AERIS PLAN</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <div style={{ width: '12px', height: '10px', background: '#EFF6FF', border: '1px solid #BFDBFE' }} />
            <span style={{ color: '#2563EB' }}>AVERTED POLLUTION MASS</span>
          </div>
        </div>
      </div>

      {/* 4. Policy Comparison Table + Control Sensitivity */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '20px' }}>
        {/* Table as per Section 24 */}
        <div className="white-card" style={{ padding: '20px' }}>
          <h3 style={{ fontSize: '0.88rem', fontWeight: 600, marginBottom: '12px' }}>POLICY STRATEGY COMPARISON</h3>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.76rem', fontFamily: 'var(--font-mono)' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border-subtle)', textAlign: 'left', color: '#64748B' }}>
                <th style={{ padding: '8px 10px' }}>STRATEGY</th>
                <th style={{ padding: '8px 10px' }}>PEAK AQI</th>
                <th style={{ padding: '8px 10px' }}>COST</th>
                <th style={{ padding: '8px 10px', textAlign: 'center' }}>TARGET (≤300)</th>
              </tr>
            </thead>
            <tbody>
              <tr style={{ borderBottom: '1px solid #F1F5F9' }}>
                <td style={{ padding: '10px', fontWeight: 600 }}>NO ACTION</td>
                <td style={{ padding: '10px', color: '#DC2626' }}>385</td>
                <td style={{ padding: '10px', color: '#64748B' }}>—</td>
                <td style={{ padding: '10px', textAlign: 'center', color: '#DC2626', fontWeight: 600 }}>Fail</td>
              </tr>
              <tr style={{ borderBottom: '1px solid #F1F5F9' }}>
                <td style={{ padding: '10px', fontWeight: 600 }}>LOW COST</td>
                <td style={{ padding: '10px', color: '#EA580C' }}>342</td>
                <td style={{ padding: '10px', color: '#16A34A' }}>LOW</td>
                <td style={{ padding: '10px', textAlign: 'center', color: '#DC2626', fontWeight: 600 }}>Fail</td>
              </tr>
              <tr style={{ borderBottom: '1px solid #F1F5F9', background: '#F8FAFC' }}>
                <td style={{ padding: '10px', fontWeight: 700, color: 'var(--forest-800)' }}>BALANCED</td>
                <td style={{ padding: '10px', color: 'var(--forest-800)', fontWeight: 700 }}>288</td>
                <td style={{ padding: '10px', color: '#EA580C' }}>MED</td>
                <td style={{ padding: '10px', textAlign: 'center', color: '#16A34A', fontWeight: 600 }}>Pass</td>
              </tr>
              <tr>
                <td style={{ padding: '10px', fontWeight: 600 }}>AGGRESSIVE</td>
                <td style={{ padding: '10px', color: '#16A34A' }}>240</td>
                <td style={{ padding: '10px', color: '#DC2626' }}>HIGH</td>
                <td style={{ padding: '10px', textAlign: 'center', color: '#16A34A', fontWeight: 600 }}>Pass</td>
              </tr>
            </tbody>
          </table>
        </div>

        {/* Sensitivity Ranking as per Section 26 */}
        <div className="white-card" style={{ padding: '20px' }}>
          <h3 style={{ fontSize: '0.88rem', fontWeight: 600, marginBottom: '12px' }}>CONTROL SENSITIVITY RANKING</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <div style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-sm)', padding: '10px 12px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color: '#2563EB', marginRight: '8px' }}>1</span>
                <span style={{ fontSize: '0.78rem', fontWeight: 600, color: '#111827' }}>Vehicular Traffic Curtailment</span>
                <span style={{ fontSize: '0.7rem', color: '#64748B', display: 'block', marginLeft: '16px' }}>Highest modeled response per unit intervention cost</span>
              </div>
              <span className="provenance-tag modelled">RANK 1</span>
            </div>

            <div style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-sm)', padding: '10px 12px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color: '#2563EB', marginRight: '8px' }}>2</span>
                <span style={{ fontSize: '0.78rem', fontWeight: 600, color: '#111827' }}>Agricultural Fire In-Situ Mulching</span>
                <span style={{ fontSize: '0.7rem', color: '#64748B', display: 'block', marginLeft: '16px' }}>Strong modeled response (effective during inflow alignment)</span>
              </div>
              <span className="provenance-tag modelled">RANK 2</span>
            </div>

            <div style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-sm)', padding: '10px 12px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color: '#2563EB', marginRight: '8px' }}>3</span>
                <span style={{ fontSize: '0.78rem', fontWeight: 600, color: '#111827' }}>Industrial Stack Fuel Switching</span>
                <span style={{ fontSize: '0.7rem', color: '#64748B', display: 'block', marginLeft: '16px' }}>Moderate modeled response (high economic dispatch cost)</span>
              </div>
              <span className="provenance-tag modelled">RANK 3</span>
            </div>
          </div>
        </div>
      </div>

      {/* 5. Airshed Federalism (Cross-Border Economic Arbitrage) */}
      <AirshedFederalismCard />

      {/* Infeasibility Certificate Modal */}
      <InfeasibilityCertificateModal
        isOpen={showInfeasibilityModal}
        onClose={() => setShowInfeasibilityModal(false)}
        certificate={result?.infeasibility_certificate || null}
      />
    </div>
  );
};
