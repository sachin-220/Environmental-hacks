import React, { useState, useEffect } from 'react';
import { Clock, AlertOctagon, Zap, ShieldAlert, ArrowRight, Gauge, Activity } from 'lucide-react';
import { ActionWindowData } from '../../types';
import { fetchActionWindow } from '../../api';

export const ActionWindowCard: React.FC = () => {
  const [data, setData] = useState<ActionWindowData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [secondsRemaining, setSecondsRemaining] = useState<number>(3 * 3600 + 24 * 60 + 15);

  useEffect(() => {
    fetchActionWindow()
      .then((res) => {
        setData(res);
        if (res.hours_to_inversion_lid) {
          setSecondsRemaining(Math.round(res.hours_to_inversion_lid * 3600));
        }
      })
      .catch((err) => console.error('Failed to fetch action window:', err))
      .finally(() => setLoading(false));
  }, []);

  // Live seconds ticker
  useEffect(() => {
    const timer = setInterval(() => {
      setSecondsRemaining((prev) => (prev > 0 ? prev - 1 : 0));
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const formatCountdown = (totalSec: number) => {
    const h = Math.floor(totalSec / 3600);
    const m = Math.floor((totalSec % 3600) / 60);
    const s = totalSec % 60;
    return `${h.toString().padStart(2, '0')}h ${m.toString().padStart(2, '0')}m ${s.toString().padStart(2, '0')}s`;
  };

  const pbl = data?.current_pbl_height_m ?? 845;
  const pblNight = data?.projected_nocturnal_pbl_m ?? 210;
  const multiplier = data?.dispersion_efficiency_multiplier ?? 4.0;
  const isLocked = secondsRemaining === 0;

  return (
    <div
      className="glass-card"
      style={{
        border: '1px solid rgba(245, 158, 11, 0.4)',
        background: 'linear-gradient(135deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.85) 100%)',
        position: 'relative',
        overflow: 'hidden'
      }}
    >
      {/* Top Banner Accent */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: '3px',
          background: isLocked
            ? '#ef4444'
            : 'linear-gradient(90deg, #f59e0b, #ef4444, #f59e0b)',
          backgroundSize: '200% 100%',
          animation: isLocked ? 'none' : 'pulse 2s infinite'
        }}
      />

      <div className="card-header" style={{ paddingBottom: '10px' }}>
        <div className="card-title-group" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Clock size={18} color="#f59e0b" />
          <h3 style={{ fontSize: '0.92rem', fontWeight: 700, letterSpacing: '0.02em', color: '#f8fafc' }}>
            THE ATMOSPHERIC ACTION WINDOW
          </h3>
          <span
            style={{
              fontSize: '0.65rem',
              fontWeight: 700,
              padding: '2px 7px',
              borderRadius: '4px',
              background: isLocked ? 'rgba(239, 68, 68, 0.2)' : 'rgba(245, 158, 11, 0.2)',
              color: isLocked ? '#f87171' : '#fbbf24',
              border: `1px solid ${isLocked ? '#ef4444' : '#f59e0b'}`
            }}
          >
            {isLocked ? 'INVERSION LOCKED' : 'GOLDEN HOUR ACTIVE'}
          </span>
        </div>
        <span className="provenance-tag scenario">TIME-CRITICAL REACHABILITY</span>
      </div>

      <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
        {/* Main Countdown & Metric Grid */}
        <div style={{ display: 'grid', gridTemplateColumns: '1.4fr 1fr', gap: '16px', alignItems: 'center' }}>
          {/* Countdown Display Box */}
          <div
            style={{
              background: 'rgba(15, 23, 42, 0.8)',
              border: '1px solid rgba(245, 158, 11, 0.3)',
              borderRadius: '8px',
              padding: '14px 16px',
              display: 'flex',
              flexDirection: 'column',
              gap: '6px'
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '0.72rem', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                T-Minus to Inversion Lid Closure
              </span>
              <span style={{ fontSize: '0.7rem', color: '#f59e0b', fontFamily: 'var(--font-mono)' }}>
                Lockdown: 18:30 IST
              </span>
            </div>

            <div
              style={{
                fontFamily: 'var(--font-mono)',
                fontSize: '1.8rem',
                fontWeight: 800,
                color: isLocked ? '#ef4444' : '#fbbf24',
                letterSpacing: '0.05em',
                textShadow: isLocked ? '0 0 10px rgba(239, 68, 68, 0.4)' : '0 0 12px rgba(245, 158, 11, 0.35)'
              }}
            >
              {isLocked ? '00h 00m 00s' : formatCountdown(secondsRemaining)}
            </div>

            <div style={{ width: '100%', height: '6px', background: '#1e293b', borderRadius: '3px', overflow: 'hidden', marginTop: '4px' }}>
              <div
                style={{
                  width: `${Math.max(0, Math.min(100, (secondsRemaining / (4 * 3600)) * 100))}%`,
                  height: '100%',
                  background: isLocked
                    ? '#ef4444'
                    : 'linear-gradient(90deg, #10b981, #f59e0b, #ef4444)',
                  transition: 'width 1s linear'
                }}
              />
            </div>
            <span style={{ fontSize: '0.66rem', color: '#64748b', fontStyle: 'italic' }}>
              Timing beats Intensity: Action efficiency collapses by 75% once the nocturnal thermal lid seals.
            </span>
          </div>

          {/* Efficiency Multiplier Display */}
          <div
            style={{
              background: 'rgba(15, 23, 42, 0.8)',
              border: '1px solid rgba(16, 185, 129, 0.3)',
              borderRadius: '8px',
              padding: '14px 16px',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'center',
              gap: '6px'
            }}
          >
            <span style={{ fontSize: '0.72rem', color: '#94a3b8', textTransform: 'uppercase' }}>
              Daytime Dispersion Advantage
            </span>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px' }}>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: '1.8rem', fontWeight: 800, color: '#34d399' }}>
                {multiplier}×
              </span>
              <span style={{ fontSize: '0.74rem', color: '#94a3b8' }}>higher clean air yield</span>
            </div>
            <div style={{ fontSize: '0.68rem', color: '#cbd5e1', lineHeight: '1.3' }}>
              Current PBL: <strong style={{ color: '#38bdf8' }}>{pbl}m</strong> → Drops to <strong style={{ color: '#f43f5e' }}>{pblNight}m</strong> at night.
            </div>
          </div>
        </div>

        {/* Physics-Based Callout */}
        <div
          style={{
            background: 'rgba(245, 158, 11, 0.08)',
            border: '1px solid rgba(245, 158, 11, 0.25)',
            borderRadius: '6px',
            padding: '10px 12px',
            display: 'flex',
            alignItems: 'center',
            gap: '10px'
          }}
        >
          <Zap size={16} color="#f59e0b" style={{ flexShrink: 0 }} />
          <p style={{ fontSize: '0.73rem', color: '#fde68a', lineHeight: '1.4', margin: 0 }}>
            <strong>Operational Imperative:</strong> A <strong>20% traffic curtailment executed at 2:00 PM</strong> (while convective venting is active) prevents the severe spike. If delayed until <strong>8:00 PM</strong> (after the inversion lid forms), even a <strong>90% total city shutdown</strong> will fail to prevent hazardous air quality.
          </p>
        </div>
      </div>
    </div>
  );
};
