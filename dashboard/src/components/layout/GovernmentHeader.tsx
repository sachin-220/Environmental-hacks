import React from 'react';
import {
  MapPin,
  TrendingUp,
  Activity,
  Compass,
  Sliders,
  Table,
  ShieldCheck,
  CheckCircle2,
  BellRing,
  Cloud,
  Wind,
  ExternalLink,
  FileCheck
} from 'lucide-react';
import { NavigationPage } from '../../types';

interface GovernmentHeaderProps {
  currentPage: NavigationPage;
  onPageChange: (page: NavigationPage) => void;
  operatingMode?: string;
  lastUpdated?: string;
  modelStatus?: string;
}

export const GovernmentHeader: React.FC<GovernmentHeaderProps> = ({
  currentPage,
  onPageChange,
  operatingMode = 'LIVE REAL-TIME TELEMETRY (OpenAQ v3 + NASA FIRMS VIIRS)',
  lastUpdated = 'Live Synchronized',
  modelStatus = 'OPERATIONAL (RANK 12)'
}) => {
  const navItems: { id: NavigationPage; label: string; icon: React.ReactNode; badge?: string }[] = [
    { id: 'overview', label: 'Delhi Map & Heatmap', icon: <MapPin size={15} /> },
    { id: 'alerts', label: 'Citizen Alerts & Schools', icon: <BellRing size={15} color="#2D6A4F" />, badge: 'LIVE' },
    { id: 'forecast', label: '72h Forecast', icon: <TrendingUp size={15} /> },
    { id: 'atmosphere', label: 'Coupled Feedback & Inversion', icon: <Activity size={15} /> },
    { id: 'sources', label: 'Sources & Plumes', icon: <Compass size={15} /> },
    { id: 'intervention', label: 'Intervention & MPC', icon: <Sliders size={15} /> },
    { id: 'monitoring', label: 'Stations & Telemetry', icon: <Table size={15} /> },
    { id: 'aws', label: 'AWS Cloud Architecture', icon: <Cloud size={15} color="#2D6A4F" />, badge: 'FREE TIER' },
    { id: 'model', label: 'Model Verification', icon: <ShieldCheck size={15} /> }
  ];

  return (
    <header className="portal-header" style={{ background: '#FFFFFF', borderBottom: '1px solid var(--border-subtle)', boxShadow: 'var(--shadow-sm)' }}>
      <div className="portal-header-top" style={{ maxWidth: '1720px', margin: '0 auto', padding: '14px 32px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
        {/* Left: Brand & Atmospheric Title */}
        <div className="portal-title-block">
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div
              style={{
                width: '42px',
                height: '42px',
                borderRadius: '12px',
                background: 'linear-gradient(135deg, #1B4332 0%, #2D6A4F 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: '0 4px 14px rgba(27, 67, 50, 0.28)'
              }}
            >
              <Wind size={22} color="#FFFFFF" strokeWidth={2.2} />
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <h1 style={{ margin: 0, fontFamily: 'var(--font-display)', fontSize: '22px', fontWeight: 800, color: '#081C15', letterSpacing: '-0.5px' }}>
                  AERIS
                </h1>
                <span
                  style={{
                    fontSize: '11px',
                    fontWeight: 800,
                    background: '#E8F5E9',
                    color: '#1B4332',
                    padding: '3px 10px',
                    borderRadius: '999px',
                    border: '1px solid #C8E6C9',
                    letterSpacing: '0.4px'
                  }}
                >
                  AIRSHED INTELLIGENCE
                </span>
              </div>
              <div style={{ color: 'var(--text-muted)', fontSize: '12px', fontWeight: 500, marginTop: '1px' }}>
                Atmospheric Emission-Response Intelligence System
              </div>
            </div>
          </div>
        </div>

        {/* Center: Geographical Domain */}
        <div style={{ textAlign: 'center', background: 'var(--bg-surface-subtle)', padding: '6px 20px', borderRadius: '999px', border: '1px solid var(--border-subtle)' }}>
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              fontWeight: 800,
              color: 'var(--forest-900)',
              fontSize: '13.5px',
              fontFamily: 'var(--font-display)',
              letterSpacing: '0.3px'
            }}
          >
            <MapPin size={14} color="#2D6A4F" />
            DELHI NCR AIRSHED
          </div>
          <span style={{ color: 'var(--border-light)', margin: '0 8px' }}>·</span>
          <span style={{ color: 'var(--text-muted)', fontSize: '12px' }}>
            Grid: <strong>3-km WRF-Chem D03</strong> · Horizon: <strong>72 Hours</strong>
          </span>
        </div>

        {/* Right: Operational Status & Proof Evidence */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
          <a
            href="https://drive.google.com/drive/folders/14wepK-b2KQ7AW8vIA-dW0N1DARpN011R?usp=sharing"
            target="_blank"
            rel="noopener noreferrer"
            style={{
              background: 'linear-gradient(135deg, #0F5132 0%, #198754 100%)',
              color: '#FFFFFF',
              borderRadius: '999px',
              padding: '6px 14px',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              fontSize: '11.5px',
              fontWeight: 800,
              textDecoration: 'none',
              boxShadow: '0 2px 8px rgba(25, 135, 84, 0.3)',
              letterSpacing: '0.2px'
            }}
          >
            <FileCheck size={13} />
            <span>PROOF & VALIDATION ARTIFACTS</span>
            <ExternalLink size={11} />
          </a>

          <div
            style={{
              background: '#FFFFFF',
              border: '1px solid #C8E6C9',
              borderRadius: '999px',
              padding: '6px 14px',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '7px',
              boxShadow: 'var(--shadow-sm)'
            }}
          >
            <span className="status-dot-pulse" />
            <span style={{ fontSize: '12px', fontWeight: 800, color: 'var(--forest-800)' }}>
              LIVE TELEMETRY ACTIVE
            </span>
          </div>

          <div
            style={{
              background: 'var(--bg-surface-subtle)',
              border: '1px solid var(--border-subtle)',
              borderRadius: '999px',
              padding: '6px 12px',
              fontSize: '12px',
              fontWeight: 700,
              color: 'var(--text-secondary)',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '5px'
            }}
          >
            <CheckCircle2 size={13} color="#2D6A4F" />
            <span>{modelStatus}</span>
          </div>
        </div>
      </div>

      {/* Navigation Strip with All 9 Tabs Full Width */}
      <div style={{ background: '#F8FAF9', borderTop: '1px solid var(--border-subtle)' }}>
        <nav
          className="portal-nav"
          aria-label="AERIS Sections"
          style={{
            maxWidth: '1720px',
            margin: '0 auto',
            display: 'flex',
            justifyContent: 'flex-start',
            alignItems: 'center',
            gap: '6px',
            padding: '6px 32px',
            overflowX: 'auto'
          }}
        >
          {navItems.map((item) => {
            const isActive = currentPage === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onPageChange(item.id)}
                className={`portal-nav-item ${isActive ? 'active' : ''}`}
                style={{
                  background: isActive ? '#1B4332' : 'transparent',
                  color: isActive ? '#FFFFFF' : 'var(--text-secondary)',
                  border: isActive ? '1px solid #1B4332' : '1px solid transparent',
                  borderRadius: '999px',
                  padding: '7px 15px',
                  fontSize: '12.5px',
                  fontWeight: isActive ? 800 : 600,
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '6px',
                  cursor: 'pointer',
                  whiteSpace: 'nowrap',
                  transition: 'all 0.18s ease'
                }}
              >
                {React.cloneElement(item.icon as React.ReactElement, {
                  size: 14,
                  color: isActive ? '#FFFFFF' : '#40916C'
                })}
                <span>{item.label}</span>
                {item.badge && (
                  <span
                    style={{
                      fontSize: '9.5px',
                      fontWeight: 800,
                      padding: '1px 6px',
                      borderRadius: '999px',
                      background: isActive ? '#52B788' : '#E8F5E9',
                      color: isActive ? '#05130E' : '#1B4332',
                      marginLeft: '2px',
                      letterSpacing: '0.3px'
                    }}
                  >
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      </div>
    </header>
  );
};
