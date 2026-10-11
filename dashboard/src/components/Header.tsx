import React from 'react';
import { Activity, Compass, ShieldAlert, Cpu, Sparkles, RefreshCw } from 'lucide-react';
import { SystemHealth } from '../types';

interface HeaderProps {
  health: SystemHealth | null;
  onOpenTour: () => void;
  onOpenHealth: () => void;
  onRefresh: () => void;
  presentationMode: boolean;
  onTogglePresentation: () => void;
  loading: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  health,
  onOpenTour,
  onOpenHealth,
  onRefresh,
  presentationMode,
  onTogglePresentation,
  loading
}) => {
  return (
    <header className="header-bar">
      <div className="brand-section">
        <div className="brand-logo">
          <Activity size={26} />
        </div>
        <div className="brand-text">
          <h1>AERIS <span style={{ fontSize: '0.85rem', color: '#06b6d4', fontWeight: 600 }}>v5.0</span></h1>
          <p>Atmospheric Emission-Response Intelligence System • Delhi NCR</p>
        </div>
      </div>

      <div className="header-badges">
        <div className="system-badge">
          <Compass size={14} color="#06b6d4" />
          <span>3-km D03 AIRSHED</span>
        </div>

        <div className="system-badge">
          <span className="pulse-dot cyan"></span>
          <span>REPLAY MODE (2023-11-01)</span>
        </div>

        <div className="system-badge" style={{ cursor: 'pointer' }} onClick={onOpenHealth} title="Click to view DMDc mathematical specs">
          <Cpu size={14} color="#a855f7" />
          <span>DMDc RANK: {health?.dmdc_model?.rank || 12}</span>
        </div>

        <div className="system-badge">
          <span className="provenance-tag modelled">MODELLED</span>
        </div>

        <button
          className={`btn-interactive ${presentationMode ? 'btn-primary' : 'btn-secondary'}`}
          onClick={onTogglePresentation}
          title="Toggle Judge Presentation Mode"
        >
          <ShieldAlert size={14} />
          <span>{presentationMode ? 'Presentation ON' : 'Presentation Mode'}</span>
        </button>

        <button
          className="btn-interactive btn-primary"
          onClick={onOpenTour}
        >
          <Sparkles size={14} />
          <span>Guided Tour</span>
        </button>

        <button
          className="btn-interactive btn-secondary"
          onClick={onRefresh}
          disabled={loading}
          title="Refresh real-time predictions"
        >
          <RefreshCw size={14} className={loading ? 'spinning' : ''} />
        </button>
      </div>
    </header>
  );
};
