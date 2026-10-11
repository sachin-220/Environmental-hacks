import React from 'react';
import { Sparkles, Activity, RefreshCw } from 'lucide-react';
import { NavigationPage } from '../../types';

interface TopHeaderProps {
  currentPage: NavigationPage;
  onOpenActivity: () => void;
  onOpenTour: () => void;
  onRefresh: () => void;
  loading: boolean;
  operatingMode: string;
}

export const TopHeader: React.FC<TopHeaderProps> = ({
  currentPage,
  onOpenActivity,
  onOpenTour,
  onRefresh,
  loading,
  operatingMode
}) => {
  const pageTitles: Record<NavigationPage, string> = {
    overview: 'Overview',
    alerts: 'Citizen Alerts & Schools',
    monitoring: 'Monitoring',
    forecast: 'Forecast',
    atmosphere: 'Atmosphere',
    sources: 'Sources & Plume',
    intervention: 'Interventions',
    aws: 'AWS Cloud Architecture',
    model: 'Model & Validation'
  };

  const isReplay = operatingMode.includes('REPLAY');

  return (
    <header className="top-header">
      <div className="breadcrumb-area">
        <span className="breadcrumb-system">AERIS</span>
        <span style={{ color: '#CBD5E1' }}>/</span>
        <span className="breadcrumb-current">{pageTitles[currentPage]}</span>
      </div>

      <div className="header-center-info">
        <span>DELHI NCR</span>
        <span style={{ color: '#CBD5E1' }}>•</span>
        <span>3 KM D03</span>
        <span style={{ color: '#CBD5E1' }}>•</span>
        <span>72H OUTLOOK</span>
      </div>

      <div className="header-actions">
        {/* Subtle Live Pipeline Indicator */}
        <div
          className="pipeline-indicator"
          onClick={onOpenActivity}
          title="Click to view real-time backend pipeline activity"
        >
          <div className="pipeline-step ready">
            <span>DATA</span>
            <span className="status-dot green" />
          </div>
          <span style={{ color: '#94A3B8', fontSize: '0.65rem' }}>→</span>
          <div className="pipeline-step ready">
            <span>WRF</span>
            <span className="status-dot green" />
          </div>
          <span style={{ color: '#94A3B8', fontSize: '0.65rem' }}>→</span>
          <div className="pipeline-step ready">
            <span>DMDc</span>
            <span className="status-dot blue" />
          </div>
          <span style={{ color: '#94A3B8', fontSize: '0.65rem' }}>→</span>
          <div className="pipeline-step ready">
            <span>ATTR</span>
            <span className="status-dot green" />
          </div>
          <span style={{ color: '#94A3B8', fontSize: '0.65rem' }}>→</span>
          <div className="pipeline-step ready">
            <span>MPC</span>
            <span className="status-dot green" />
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.72rem', fontWeight: 600, color: '#16A34A', fontFamily: 'var(--font-mono)' }}>
          <span className="status-dot green" />
          <span>OPERATIONAL</span>
        </div>

        <span className="provenance-tag modelled" style={{ fontSize: '0.68rem', padding: '2px 8px' }}>
          {isReplay ? 'REPLAY' : 'LIVE'}
        </span>

        <button className="btn-clean" onClick={onOpenActivity} title="View backend activity log">
          <Activity size={14} color="#2563EB" />
          <span>Activity</span>
        </button>

        <button className="btn-clean primary" onClick={onOpenTour}>
          <Sparkles size={14} />
          <span>Demo Tour</span>
        </button>

        <button
          className="btn-clean"
          onClick={onRefresh}
          disabled={loading}
          title="Refresh real-time data"
          style={{ padding: '7px 10px' }}
        >
          <RefreshCw size={14} className={loading ? 'spinning' : ''} />
        </button>
      </div>
    </header>
  );
};
