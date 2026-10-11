import React, { useState } from 'react';
import {
  Radio,
  QrCode,
  Volume2,
  VolumeX,
  Send,
  ChevronDown,
  ChevronUp,
  ShieldAlert,
  GraduationCap,
  BellRing,
  HeartPulse
} from 'lucide-react';
import { ActiveAlertsResponse } from '../../types';

interface EmergencyAlertRibbonProps {
  alertsData: ActiveAlertsResponse | null;
  onOpenBroadcastModal: () => void;
  onOpenQRModal: () => void;
  onNavigateToCitizen: () => void;
}

export const EmergencyAlertRibbon: React.FC<EmergencyAlertRibbonProps> = ({
  alertsData,
  onOpenBroadcastModal,
  onOpenQRModal,
  onNavigateToCitizen
}) => {
  const [isExpanded, setIsExpanded] = useState<boolean>(false);
  const [soundEnabled, setSoundEnabled] = useState<boolean>(false);

  // Synthesized harmonic chime via Web Audio API
  const playAlertChime = () => {
    try {
      const AudioContext = window.AudioContext || (window as any).webkitAudioContext;
      if (!AudioContext) return;
      const ctx = new AudioContext();

      const osc1 = ctx.createOscillator();
      const osc2 = ctx.createOscillator();
      const gain = ctx.createGain();

      osc1.type = 'sine';
      osc2.type = 'triangle';

      osc1.frequency.setValueAtTime(587.33, ctx.currentTime);
      osc1.frequency.exponentialRampToValueAtTime(880, ctx.currentTime + 0.3);

      osc2.frequency.setValueAtTime(440, ctx.currentTime);
      osc2.frequency.exponentialRampToValueAtTime(659.25, ctx.currentTime + 0.3);

      gain.gain.setValueAtTime(0.12, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.6);

      osc1.connect(gain);
      osc2.connect(gain);
      gain.connect(ctx.destination);

      osc1.start();
      osc2.start();
      osc1.stop(ctx.currentTime + 0.65);
      osc2.stop(ctx.currentTime + 0.65);
    } catch (e) {
      console.warn('Audio chime notice:', e);
    }
  };

  const handleToggleSound = () => {
    const nextState = !soundEnabled;
    setSoundEnabled(nextState);
    if (nextState) {
      playAlertChime();
    }
  };

  if (!alertsData) return null;

  const topAlert = alertsData.alerts?.[0];
  const activeCount = alertsData.active_alerts_count || 8;

  return (
    <div
      style={{
        background: 'linear-gradient(90deg, #0D281E 0%, #1B4332 50%, #0D281E 100%)',
        color: '#FFFFFF',
        borderBottom: '1.5px solid rgba(82, 183, 136, 0.3)',
        boxShadow: '0 4px 18px rgba(8, 28, 21, 0.25)',
        position: 'relative',
        zIndex: 45
      }}
    >
      {/* Primary Clean One-Row Alert Bar */}
      <div
        style={{
          maxWidth: '1440px',
          margin: '0 auto',
          padding: '8px 24px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '12px'
        }}
      >
        {/* Left: Unified Status Pill & Headline */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap', flex: 1, minWidth: '300px' }}>
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              background: 'rgba(217, 119, 6, 0.95)',
              color: '#FFFFFF',
              padding: '4px 10px',
              borderRadius: '999px',
              fontSize: '11px',
              fontWeight: 800,
              letterSpacing: '0.4px',
              boxShadow: '0 2px 6px rgba(217, 119, 6, 0.4)'
            }}
          >
            <Radio size={12} className="animate-pulse" />
            <span>EARLY WARNING</span>
          </div>

          <div style={{ fontSize: '13px', fontWeight: 700, color: '#F4FBF7', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span>High-Risk Atmospheric Inversion Advisory Across Delhi NCR Airshed</span>
            <span
              style={{
                background: 'rgba(255, 255, 255, 0.12)',
                padding: '2px 8px',
                borderRadius: '999px',
                fontSize: '11px',
                color: '#B7E4C7',
                fontWeight: 700
              }}
            >
              {activeCount} Wards
            </span>
          </div>
        </div>

        {/* Right: Unified Action Toolbar */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            background: 'rgba(0, 0, 0, 0.28)',
            padding: '4px 6px',
            borderRadius: '999px',
            border: '1px solid rgba(255, 255, 255, 0.12)'
          }}
        >
          {/* Audio Chime Toggle */}
          <button
            onClick={handleToggleSound}
            title={soundEnabled ? 'Mute Audio Chimes' : 'Enable Audio Warning Chimes'}
            style={{
              background: soundEnabled ? '#2D6A4F' : 'transparent',
              color: soundEnabled ? '#FFFFFF' : '#D8F3DC',
              border: 'none',
              borderRadius: '999px',
              padding: '5px 10px',
              fontSize: '11px',
              fontWeight: 700,
              cursor: 'pointer',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '5px',
              transition: 'all 0.15s ease'
            }}
          >
            {soundEnabled ? <Volume2 size={13} color="#95D5B2" /> : <VolumeX size={13} />}
            <span>{soundEnabled ? 'AUDIO ON' : 'AUDIO OFF'}</span>
          </button>

          <span style={{ width: '1px', height: '14px', background: 'rgba(255,255,255,0.18)' }} />

          {/* Citizen QR Scanner */}
          <button
            onClick={onOpenQRModal}
            style={{
              background: '#FFFFFF',
              color: '#081C15',
              border: 'none',
              borderRadius: '999px',
              padding: '5px 12px',
              fontSize: '11.5px',
              fontWeight: 800,
              cursor: 'pointer',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '5px',
              boxShadow: '0 2px 6px rgba(0,0,0,0.12)',
              transition: 'all 0.15s ease'
            }}
          >
            <QrCode size={13} color="#1B4332" />
            <span>CITIZEN QR</span>
          </button>

          {/* School Safety Quick Link */}
          <button
            onClick={onNavigateToCitizen}
            style={{
              background: 'transparent',
              color: '#E8F5E9',
              border: 'none',
              borderRadius: '999px',
              padding: '5px 11px',
              fontSize: '11.5px',
              fontWeight: 700,
              cursor: 'pointer',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '5px',
              transition: 'all 0.15s ease'
            }}
          >
            <GraduationCap size={13} color="#74C69D" />
            <span>SCHOOL PROTOCOL</span>
          </button>

          {/* Dispatch Geo-Alert Button */}
          <button
            onClick={onOpenBroadcastModal}
            style={{
              background: '#D97706',
              color: '#FFFFFF',
              border: 'none',
              borderRadius: '999px',
              padding: '5px 12px',
              fontSize: '11.5px',
              fontWeight: 800,
              cursor: 'pointer',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '5px',
              boxShadow: '0 2px 8px rgba(217, 119, 6, 0.4)',
              transition: 'all 0.15s ease'
            }}
          >
            <Send size={12} />
            <span>DISPATCH ALERT</span>
          </button>

          <span style={{ width: '1px', height: '14px', background: 'rgba(255,255,255,0.18)' }} />

          {/* Expand Details Toggle */}
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            style={{
              background: 'transparent',
              border: 'none',
              color: '#D8F3DC',
              cursor: 'pointer',
              padding: '4px 6px',
              borderRadius: '999px',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '3px',
              fontSize: '11px',
              fontWeight: 600
            }}
          >
            <span>{isExpanded ? 'LESS' : 'DETAILS'}</span>
            {isExpanded ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
          </button>
        </div>
      </div>

      {/* Expandable Atmospheric Early Warning Drawer */}
      {isExpanded && topAlert && (
        <div
          style={{
            background: 'rgba(8, 28, 21, 0.96)',
            backdropFilter: 'blur(10px)',
            borderTop: '1px solid rgba(82, 183, 136, 0.25)',
            padding: '20px 28px',
            animation: 'fadeIn 0.2s ease-out'
          }}
        >
          <div
            style={{
              maxWidth: '1440px',
              margin: '0 auto',
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
              gap: '16px'
            }}
          >
            {/* Box 1: Atmospheric Inversion Alert */}
            <div
              style={{
                background: 'rgba(255, 255, 255, 0.05)',
                border: '1px solid rgba(255, 255, 255, 0.12)',
                borderRadius: 'var(--radius-md)',
                padding: '14px 16px'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#FCD34D', fontWeight: 800, fontSize: '12.5px', marginBottom: '6px' }}>
                <ShieldAlert size={15} />
                <span>ATMOSPHERIC TRAPPING DRIVER</span>
              </div>
              <p style={{ fontSize: '12px', color: '#D1D5DB', margin: '0 0 8px 0', lineHeight: 1.45 }}>
                {topAlert.primary_driver}
              </p>
              <div style={{ fontSize: '11.5px', color: '#9CA3AF' }}>
                Projected Peak AQI: <strong style={{ color: '#F87171' }}>{topAlert.projected_peak_aqi}</strong> at {topAlert.projected_peak_time}
              </div>
            </div>

            {/* Box 2: School Protocol Notice */}
            <div
              style={{
                background: 'rgba(255, 255, 255, 0.05)',
                border: '1px solid rgba(255, 255, 255, 0.12)',
                borderRadius: 'var(--radius-md)',
                padding: '14px 16px'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#74C69D', fontWeight: 800, fontSize: '12.5px', marginBottom: '6px' }}>
                <GraduationCap size={15} />
                <span>MANDATORY SCHOOL DIRECTIVE</span>
              </div>
              <p style={{ fontSize: '12px', color: '#D1D5DB', margin: '0 0 8px 0', lineHeight: 1.45 }}>
                {topAlert.school_protocol.recommendation}
              </p>
              <button
                onClick={onNavigateToCitizen}
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: '#52B788',
                  fontSize: '11.5px',
                  fontWeight: 700,
                  cursor: 'pointer',
                  padding: 0,
                  textDecoration: 'underline'
                }}
              >
                View Full School Safety Matrix →
              </button>
            </div>

            {/* Box 3: Citizen Protection */}
            <div
              style={{
                background: 'rgba(255, 255, 255, 0.05)',
                border: '1px solid rgba(255, 255, 255, 0.12)',
                borderRadius: 'var(--radius-md)',
                padding: '14px 16px'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#60A5FA', fontWeight: 800, fontSize: '12.5px', marginBottom: '6px' }}>
                <HeartPulse size={15} />
                <span>CITIZEN HEALTH ACTION</span>
              </div>
              <p style={{ fontSize: '12px', color: '#D1D5DB', margin: '0 0 8px 0', lineHeight: 1.45 }}>
                {topAlert.health_advisory.outdoor_jogging}
              </p>
              <div style={{ fontSize: '11.5px', color: '#9CA3AF' }}>
                Purifiers: <span style={{ color: '#D1D5DB' }}>{topAlert.health_advisory.air_purifiers}</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
