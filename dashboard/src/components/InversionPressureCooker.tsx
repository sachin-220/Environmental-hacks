import React from 'react';
import { Layers, Thermometer, Wind, AlertTriangle, ShieldCheck } from 'lucide-react';
import { CurrentState } from '../types';

interface InversionPressureCookerProps {
  state: CurrentState | null;
}

export const InversionPressureCooker: React.FC<InversionPressureCookerProps> = ({ state }) => {
  const pblh = state?.boundary_layer_height ?? 869.0;
  const invStrength = state?.inversion_strength ?? 1.76;
  const windSpeed = state?.wind_speed_10m ?? 2.8;

  // Ventilation coefficient: V_c = WindSpeed * PBLH
  const ventCoeff = Math.round(windSpeed * pblh);
  const ventThreshold = 6000;
  const isSevereTrapping = ventCoeff < 2000;

  // Visual column dimensions
  const colHeight = 220;
  const maxAlt = 2000; // meters
  const pblhY = colHeight - (pblh / maxAlt) * colHeight;

  return (
    <div className="glass-card" style={{ display: 'flex', flexDirection: 'column' }}>
      <div className="card-header">
        <div className="card-title-group">
          <Layers size={16} color="#f43f5e" />
          <h3>Vertical Column & Inversion Trap</h3>
        </div>
        <span className="provenance-tag modelled">MODELLED</span>
      </div>

      <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
        {/* Pressure Cooker Diagram */}
        <div style={{ display: 'grid', gridTemplateColumns: '140px 1fr', gap: '16px', alignItems: 'center' }}>
          {/* Vertical Atmospheric Column SVG */}
          <div style={{ background: '#070c14', borderRadius: '8px', border: '1px solid rgba(255, 255, 255, 0.08)', padding: '10px 8px', position: 'relative' }}>
            <svg viewBox="0 0 120 220" style={{ width: '100%', height: 'auto', display: 'block' }}>
              <defs>
                <linearGradient id="trappedGrad" x1="0" y1="1" x2="0" y2="0">
                  <stop offset="0%" stopColor="rgba(153, 27, 27, 0.85)" />
                  <stop offset="70%" stopColor="rgba(239, 68, 68, 0.6)" />
                  <stop offset="100%" stopColor="rgba(249, 115, 22, 0.3)" />
                </linearGradient>
                <linearGradient id="freeAtmosGrad" x1="0" y1="1" x2="0" y2="0">
                  <stop offset="0%" stopColor="rgba(30, 41, 59, 0.4)" />
                  <stop offset="100%" stopColor="rgba(15, 23, 42, 0.8)" />
                </linearGradient>
              </defs>

              {/* Free atmosphere above PBL */}
              <rect x="15" y="10" width="70" height={pblhY - 10} fill="url(#freeAtmosGrad)" rx="2" />
              <text x="50" y="30" textAnchor="middle" fill="#64748b" fontSize="8" fontFamily="var(--font-mono)">
                Free Troposphere
              </text>

              {/* Capping Inversion Thermal Lid */}
              <line x1="10" y1={pblhY} x2="90" y2={pblhY} stroke="#f43f5e" strokeWidth="3" strokeDasharray="4 2" />
              <polygon points={`50,${pblhY - 4} 45,${pblhY - 9} 55,${pblhY - 9}`} fill="#f43f5e" />

              {/* Trapped Mixing Layer */}
              <rect x="15" y={pblhY} width="70" height={colHeight - 20 - pblhY} fill="url(#trappedGrad)" rx="2" />

              {/* Ground level line */}
              <line x1="5" y1={colHeight - 20} x2="95" y2={colHeight - 20} stroke="#94a3b8" strokeWidth="2" />
              <text x="50" y={colHeight - 6} textAnchor="middle" fill="#94a3b8" fontSize="8" fontFamily="var(--font-sans)">
                Surface (28.61°N)
              </text>

              {/* Altitude labels */}
              <text x="100" y="18" fill="#64748b" fontSize="7" fontFamily="var(--font-mono)">2000m</text>
              <text x="100" y={pblhY + 3} fill="#f43f5e" fontSize="7" fontFamily="var(--font-mono)" fontWeight="700">
                {Math.round(pblh)}m
              </text>
              <text x="100" y={colHeight - 18} fill="#64748b" fontSize="7" fontFamily="var(--font-mono)">0m</text>
            </svg>
          </div>

          {/* Physics Diagnostics */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <div style={{ background: 'rgba(15, 23, 42, 0.6)', border: '1px solid var(--border-subtle)', borderRadius: '8px', padding: '10px 12px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                <span style={{ fontSize: '0.72rem', color: '#94a3b8', textTransform: 'uppercase' }}>Ventilation Coefficient (Vc)</span>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.85rem', fontWeight: 700, color: isSevereTrapping ? '#ef4444' : '#f59e0b' }}>
                  {ventCoeff} m²/s
                </span>
              </div>
              <div style={{ width: '100%', height: '4px', background: '#1e293b', borderRadius: '2px', overflow: 'hidden' }}>
                <div style={{ width: `${Math.min((ventCoeff / ventThreshold) * 100, 100)}%`, height: '100%', background: isSevereTrapping ? '#ef4444' : '#f59e0b' }} />
              </div>
              <span style={{ fontSize: '0.68rem', color: '#64748b', marginTop: '4px', display: 'block' }}>
                Critical dispersion threshold: 6,000 m²/s
              </span>
            </div>

            <div style={{ background: 'rgba(244, 63, 94, 0.1)', border: '1px solid rgba(244, 63, 94, 0.25)', borderRadius: '8px', padding: '10px 12px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#fb7185', fontWeight: 700, fontSize: '0.75rem', marginBottom: '4px' }}>
                <Thermometer size={14} />
                <span>Thermal Lid Potential Jump</span>
              </div>
              <p style={{ fontSize: '0.72rem', color: '#cbd5e1', lineHeight: '1.4' }}>
                <strong style={{ color: '#ffffff' }}>+{invStrength} K</strong> nocturnal inversion lid traps pollutants below <strong style={{ color: '#ffffff' }}>{Math.round(pblh)}m</strong>, suppressing vertical dispersion like a sealed pressure cooker.
              </p>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', color: '#94a3b8', fontFamily: 'var(--font-mono)' }}>
              <span>Richardson Number: <strong style={{ color: '#f87171' }}>Ri &gt; 0.25</strong></span>
              <span>Turbulence: <strong style={{ color: '#f87171' }}>Suppressed</strong></span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
