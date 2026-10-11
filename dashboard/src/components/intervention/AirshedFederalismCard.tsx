import React, { useState, useEffect } from 'react';
import { Landmark, TrendingUp, DollarSign, ArrowRight, ShieldCheck, Scale, Sparkles, CheckCircle2 } from 'lucide-react';
import { AirshedFederalismData } from '../../types';
import { fetchAirshedFederalism } from '../../api';

export const AirshedFederalismCard: React.FC = () => {
  const [data, setData] = useState<AirshedFederalismData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [activeTab, setActiveTab] = useState<'arbitrage' | 'compact'>('arbitrage');

  useEffect(() => {
    fetchAirshedFederalism()
      .then((res) => setData(res))
      .catch((err) => console.error('Failed to fetch federalism data:', err))
      .finally(() => setLoading(false));
  }, []);

  const dTruck = data?.policies_compared?.intra_delhi_truck_ban ?? {
    name: 'Intra-Delhi Commercial Heavy Diesel Truck Ban (50,000 trucks)',
    state: 'NCT of Delhi',
    economic_disruption_cr_per_day: 45.0,
    pm25_reduction_ugm3: 14.2,
    cost_efficiency_cr_per_ug: 3.17,
    societal_impact: 'Severe logistics bottlenecks, wholesale market paralysis, supply chain inflation'
  };

  const pStubble = data?.policies_compared?.punjab_stubble_subsidy ?? {
    name: 'In-Situ Bio-Decomposer & Happy Seeder Subsidies (1,200 active fire clusters)',
    state: 'Punjab (Sangrur, Firozpur, Tarn Taran, Bathinda)',
    economic_disruption_cr_per_day: 6.5,
    pm25_reduction_ugm3: 42.8,
    cost_efficiency_cr_per_ug: 0.15,
    societal_impact: 'Direct farmer compensation, zero agrarian unrest, rapid soil carbon enrichment'
  };

  const compact = data?.cooperative_compact ?? {
    mechanism: 'Inter-State Clean Air Compensation Compact (DMC -> Punjab Ag Dept)',
    daily_fiscal_transfer_cr: 6.5,
    net_delhi_economic_savings_cr_per_day: 38.5,
    net_delhi_air_quality_gain_pct: '+201% cleaner air yield',
    game_theory_resolution: 'Breaks the non-cooperative Nash deadlock where both states suffer mutual economic and respiratory losses.'
  };

  return (
    <div
      className="glass-card"
      style={{
        border: '1px solid rgba(56, 189, 248, 0.35)',
        background: 'linear-gradient(135deg, rgba(15, 23, 42, 0.85) 0%, rgba(30, 41, 59, 0.6) 100%)',
        position: 'relative'
      }}
    >
      <div className="card-header" style={{ paddingBottom: '12px' }}>
        <div className="card-title-group" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Landmark size={18} color="#38bdf8" />
          <h3 style={{ fontSize: '0.92rem', fontWeight: 700, color: '#f8fafc', letterSpacing: '0.02em' }}>
            AIRSHED FEDERALISM: CROSS-BORDER ECONOMIC ARBITRAGE
          </h3>
          <span
            style={{
              fontSize: '0.65rem',
              fontWeight: 700,
              padding: '2px 8px',
              borderRadius: '4px',
              background: 'rgba(56, 189, 248, 0.15)',
              color: '#38bdf8',
              border: '1px solid rgba(56, 189, 248, 0.4)'
            }}
          >
            GAME THEORY / NASH EQUILIBRIUM
          </span>
        </div>
        <span className="provenance-tag scenario">FISCAL ARBITRAGE</span>
      </div>

      <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        {/* Headline Arbitrage Box */}
        <div
          style={{
            background: 'linear-gradient(90deg, rgba(16, 185, 129, 0.15) 0%, rgba(56, 189, 248, 0.15) 100%)',
            border: '1px solid rgba(16, 185, 129, 0.35)',
            borderRadius: '8px',
            padding: '14px 18px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
          }}
        >
          <div>
            <span style={{ fontSize: '0.7rem', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Clean Air Return On Investment (ROI)
            </span>
            <div style={{ fontSize: '0.88rem', fontWeight: 700, color: '#f8fafc', marginTop: '3px' }}>
              Inter-State Abatement Arbitrage
            </div>
            <p style={{ fontSize: '0.73rem', color: '#cbd5e1', marginTop: '3px', margin: 0 }}>
              Delhi Municipal Corporation funding stubble remediation in Punjab yields <strong>6.9× higher clean air return per rupee</strong> than shutting down intra-Delhi transport.
            </p>
          </div>

          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              background: '#070c14',
              padding: '10px 18px',
              borderRadius: '8px',
              border: '1px solid rgba(16, 185, 129, 0.4)',
              minWidth: '110px'
            }}
          >
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '1.9rem', fontWeight: 800, color: '#34d399', lineHeight: '1' }}>
              6.9×
            </span>
            <span style={{ fontSize: '0.62rem', color: '#94a3b8', textTransform: 'uppercase', marginTop: '3px' }}>
              Yield Multiplier
            </span>
          </div>
        </div>

        {/* Side-by-side Policy Comparison Cards */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
          {/* Intra-Delhi Policy */}
          <div
            style={{
              background: 'rgba(239, 68, 68, 0.06)',
              border: '1px solid rgba(239, 68, 68, 0.25)',
              borderRadius: '8px',
              padding: '14px'
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <span style={{ fontSize: '0.68rem', fontWeight: 700, color: '#fca5a5', textTransform: 'uppercase' }}>
                Option A: Intra-Delhi Curfew
              </span>
              <span style={{ fontSize: '0.65rem', background: 'rgba(239, 68, 68, 0.2)', color: '#f87171', padding: '2px 6px', borderRadius: '4px' }}>
                STATUS QUO
              </span>
            </div>

            <div style={{ fontSize: '0.8rem', fontWeight: 600, color: '#f1f5f9', marginBottom: '10px', minHeight: '38px' }}>
              {dTruck.name}
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', background: 'rgba(15, 23, 42, 0.6)', padding: '10px', borderRadius: '6px' }}>
              <div>
                <span style={{ fontSize: '0.65rem', color: '#94a3b8' }}>Economic Disruption</span>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: '1.1rem', fontWeight: 700, color: '#f87171' }}>
                  ₹{dTruck.economic_disruption_cr_per_day} Cr<span style={{ fontSize: '0.7rem' }}>/day</span>
                </div>
              </div>
              <div>
                <span style={{ fontSize: '0.65rem', color: '#94a3b8' }}>PM2.5 Reduction</span>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: '1.1rem', fontWeight: 700, color: '#cbd5e1' }}>
                  -{dTruck.pm25_reduction_ugm3} µg/m³
                </div>
              </div>
            </div>

            <div style={{ marginTop: '10px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.7rem', color: '#94a3b8' }}>
              <span>Cost per µg reduced:</span>
              <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color: '#f87171' }}>
                ₹{dTruck.cost_efficiency_cr_per_ug.toFixed(2)} Cr / µg
              </span>
            </div>
          </div>

          {/* Upwind Punjab Stubble Remediation */}
          <div
            style={{
              background: 'rgba(16, 185, 129, 0.08)',
              border: '1px solid rgba(16, 185, 129, 0.35)',
              borderRadius: '8px',
              padding: '14px'
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <span style={{ fontSize: '0.68rem', fontWeight: 700, color: '#6ee7b7', textTransform: 'uppercase' }}>
                Option B: Punjab Stubble Remediation
              </span>
              <span style={{ fontSize: '0.65rem', background: 'rgba(16, 185, 129, 0.2)', color: '#34d399', padding: '2px 6px', borderRadius: '4px' }}>
                AERIS OPTIMAL
              </span>
            </div>

            <div style={{ fontSize: '0.8rem', fontWeight: 600, color: '#f1f5f9', marginBottom: '10px', minHeight: '38px' }}>
              {pStubble.name}
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', background: 'rgba(15, 23, 42, 0.6)', padding: '10px', borderRadius: '6px' }}>
              <div>
                <span style={{ fontSize: '0.65rem', color: '#94a3b8' }}>Intervention Cost</span>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: '1.1rem', fontWeight: 700, color: '#34d399' }}>
                  ₹{pStubble.economic_disruption_cr_per_day} Cr<span style={{ fontSize: '0.7rem' }}>/day</span>
                </div>
              </div>
              <div>
                <span style={{ fontSize: '0.65rem', color: '#94a3b8' }}>PM2.5 Reduction</span>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: '1.1rem', fontWeight: 700, color: '#34d399' }}>
                  -{pStubble.pm25_reduction_ugm3} µg/m³
                </div>
              </div>
            </div>

            <div style={{ marginTop: '10px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.7rem', color: '#94a3b8' }}>
              <span>Cost per µg reduced:</span>
              <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color: '#34d399' }}>
                ₹{pStubble.cost_efficiency_cr_per_ug.toFixed(2)} Cr / µg
              </span>
            </div>
          </div>
        </div>

        {/* Cooperative Compact Resolution */}
        <div
          style={{
            background: 'rgba(56, 189, 248, 0.08)',
            border: '1px solid rgba(56, 189, 248, 0.25)',
            borderRadius: '8px',
            padding: '12px 16px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
          }}
        >
          <div>
            <span style={{ fontSize: '0.7rem', fontWeight: 700, color: '#38bdf8', textTransform: 'uppercase' }}>
              Airshed Cooperative Compact Outcome:
            </span>
            <div style={{ fontSize: '0.74rem', color: '#cbd5e1', marginTop: '2px' }}>
              Delhi saves <strong style={{ color: '#34d399' }}>₹{compact.net_delhi_economic_savings_cr_per_day} Cr/day</strong> in avoided logistics disruptions while gaining <strong style={{ color: '#38bdf8' }}>{compact.net_delhi_air_quality_gain_pct}</strong>.
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#34d399', fontSize: '0.72rem', fontWeight: 700 }}>
            <CheckCircle2 size={16} />
            <span>NASH EQUILIBRIUM ACHIEVED</span>
          </div>
        </div>
      </div>
    </div>
  );
};
