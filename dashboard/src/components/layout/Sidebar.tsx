import React from 'react';
import {
  LayoutDashboard,
  CloudSun,
  TrendingUp,
  PieChart,
  Clock,
  ShieldCheck,
  Cpu,
  FileText
} from 'lucide-react';
import { NavigationPage } from '../../types';

interface SidebarProps {
  currentPage: NavigationPage;
  onNavigate: (page: NavigationPage) => void;
  systemReady: boolean;
  operatingMode: string;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentPage,
  onNavigate,
  systemReady,
  operatingMode
}) => {
  const navItems = [
    { id: 'overview', label: 'Overview', icon: LayoutDashboard },
    { id: 'atmosphere', label: 'Atmosphere', icon: CloudSun },
    { id: 'forecast', label: 'Forecast', icon: TrendingUp },
    { id: 'sources', label: 'Sources', icon: PieChart },
    { id: 'plume_clock', label: 'Plume Clock', icon: Clock },
    { id: 'interventions', label: 'Interventions', icon: ShieldCheck },
    { id: 'model', label: 'Model', icon: Cpu },
    { id: 'reports', label: 'Reports', icon: FileText },
  ] as const;

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="sidebar-brand">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#2563EB" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="10" />
            <path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20" />
            <path d="M2 12h20" />
          </svg>
          <div>
            <h1>AERIS</h1>
            <div className="sidebar-subtitle">Atmospheric Emission-Response Intelligence System</div>
          </div>
        </div>
      </div>

      <nav className="sidebar-nav">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentPage === item.id;
          return (
            <button
              key={item.id}
              className={`nav-item ${isActive ? 'active' : ''}`}
              onClick={() => onNavigate(item.id as NavigationPage)}
            >
              <Icon size={17} />
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>

      <div className="sidebar-footer">
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.72rem', fontWeight: 600, color: '#16A34A', fontFamily: 'var(--font-mono)' }}>
          <span className="status-dot green" />
          <span>{systemReady ? 'SYSTEM READY' : 'INITIALIZING'}</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.68rem', fontWeight: 600, color: '#475569', fontFamily: 'var(--font-mono)' }}>
          <span className="provenance-tag modelled" style={{ fontSize: '0.62rem', padding: '1px 5px' }}>
            {operatingMode.includes('REPLAY') ? 'REPLAY MODE' : 'OPERATIONAL'}
          </span>
        </div>
      </div>
    </aside>
  );
};
