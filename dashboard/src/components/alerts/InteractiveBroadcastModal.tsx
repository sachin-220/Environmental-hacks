import React, { useState } from 'react';
import {
  X,
  Send,
  BellRing,
  Radio,
  CheckCircle2,
  Smartphone,
  Mail,
  Share2,
  Tv,
  Users,
  Layers
} from 'lucide-react';
import { broadcastAlert } from '../../api';

interface InteractiveBroadcastModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAlertDispatched?: () => void;
}

export const InteractiveBroadcastModal: React.FC<InteractiveBroadcastModalProps> = ({
  isOpen,
  onClose,
  onAlertDispatched
}) => {
  const [wardId, setWardId] = useState<string>('all_delhi_ncr');
  const [severity, setSeverity] = useState<string>('SEVERE');
  const [category, setCategory] = useState<string>('NOCTURNAL_INVERSION_COLLAPSE');
  const [audiences, setAudiences] = useState<string[]>(['schools', 'citizens', 'hospitals']);
  const [channels, setChannels] = useState<string[]>([
    'web_push',
    'whatsapp',
    'sms',
    'sns_broadcast'
  ]);
  const [customHeadline, setCustomHeadline] = useState<string>(
    'CRITICAL AIR QUALITY & THERMAL INVERSION ADVISORY'
  );
  const [customMessage, setCustomMessage] = useState<string>(
    'AERIS 72h Model predicts AQI exceeding 380 by 19:30 IST. Nocturnal thermal inversion will trap particulates under 210m. Suspend outdoor school activities; N95 advised.'
  );

  const [isSending, setIsSending] = useState<boolean>(false);
  const [dispatchResult, setDispatchResult] = useState<any | null>(null);

  if (!isOpen) return null;

  const toggleAudience = (key: string) => {
    setAudiences((prev) =>
      prev.includes(key) ? prev.filter((a) => a !== key) : [...prev, key]
    );
  };

  const toggleChannel = (key: string) => {
    setChannels((prev) =>
      prev.includes(key) ? prev.filter((c) => c !== key) : [...prev, key]
    );
  };

  // Play synthesized audio tone
  const playAlertChime = () => {
    try {
      const AudioCtx = window.AudioContext || (window as any).webkitAudioContext;
      if (!AudioCtx) return;
      const ctx = new AudioCtx();
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = 'sawtooth';
      osc.frequency.setValueAtTime(659.25, ctx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(880, ctx.currentTime + 0.2);
      gain.gain.setValueAtTime(0.12, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.5);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start();
      osc.stop(ctx.currentTime + 0.55);
    } catch (e) {
      // Audio fallback
    }
  };

  // Trigger Native Browser Web Push Notification
  const triggerNativePushNotification = async (title: string, body: string) => {
    if (typeof window !== 'undefined' && 'Notification' in window) {
      try {
        let permission = Notification.permission;
        if (permission !== 'granted') {
          permission = await Notification.requestPermission();
        }
        if (permission === 'granted') {
          new Notification(title, {
            body: body,
            icon: '/favicon.ico',
            tag: 'aeris-emergency-alert'
          });
        }
      } catch (err) {
        console.warn('Browser Web Push notice:', err);
      }
    }
  };

  const handleDispatch = async () => {
    setIsSending(true);
    try {
      playAlertChime();

      const payload = {
        ward_id: wardId,
        severity: severity,
        category: category,
        title: customHeadline,
        message: customMessage,
        target_audiences: audiences,
        channels: channels
      };

      const res = await broadcastAlert(payload);
      setDispatchResult(res);

      if (channels.includes('web_push')) {
        await triggerNativePushNotification(
          `AERIS Air Alert: ${res.ward_name || 'Delhi NCR'}`,
          customMessage
        );
      }

      if (onAlertDispatched) {
        onAlertDispatched();
      }
    } catch (err) {
      console.error('Dispatch alert error:', err);
    } finally {
      setIsSending(false);
    }
  };

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        background: 'rgba(8, 28, 21, 0.82)',
        backdropFilter: 'blur(12px)',
        zIndex: 99999,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '20px'
      }}
    >
      <div
        className="air-card"
        style={{
          background: '#FFFFFF',
          borderRadius: 'var(--radius-xl)',
          width: '100%',
          maxWidth: '680px',
          maxHeight: '90vh',
          overflowY: 'auto',
          boxShadow: 'var(--shadow-xl)',
          border: '1px solid var(--border-light)',
          animation: 'fadeIn 0.25s cubic-bezier(0.16, 1, 0.3, 1)'
        }}
      >
        {/* Modal Header */}
        <div
          style={{
            background: 'linear-gradient(135deg, #081C15 0%, #1B4332 100%)',
            color: '#FFFFFF',
            padding: '20px 28px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div
              style={{
                background: 'rgba(255, 255, 255, 0.12)',
                padding: '8px',
                borderRadius: '10px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
            >
              <Radio size={20} color="#74C69D" />
            </div>
            <div>
              <h3 style={{ fontFamily: 'var(--font-display)', margin: 0, fontSize: '18px', fontWeight: 800, letterSpacing: '-0.3px' }}>
                GEO-ALERT DISPATCH CENTER
              </h3>
              <span style={{ fontSize: '12px', color: '#D8F3DC' }}>
                Multi-Channel Emergency Broadcast (Web Push • SNS • SMS • WhatsApp • VMS)
              </span>
            </div>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'transparent',
              border: 'none',
              color: '#B7E4C7',
              cursor: 'pointer',
              padding: '6px',
              borderRadius: '999px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
          >
            <X size={20} />
          </button>
        </div>

        {/* Modal Content */}
        <div style={{ padding: '28px' }}>
          {dispatchResult ? (
            /* Success Feedback Card */
            <div
              style={{
                background: '#D8F3DC',
                border: '1px solid #74C69D',
                borderRadius: 'var(--radius-lg)',
                padding: '24px',
                textAlign: 'center'
              }}
            >
              <div
                style={{
                  width: '52px',
                  height: '52px',
                  background: '#FFFFFF',
                  borderRadius: '50%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  margin: '0 auto 14px auto',
                  boxShadow: 'var(--shadow-sm)'
                }}
              >
                <CheckCircle2 size={28} color="#2D6A4F" />
              </div>
              <h4 style={{ fontFamily: 'var(--font-display)', margin: '0 0 8px 0', fontSize: '18px', fontWeight: 800, color: '#1B4332' }}>
                EMERGENCY GEO-ALERT DISPATCHED
              </h4>
              <p style={{ margin: '0 0 18px 0', fontSize: '13.5px', color: '#2D6A4F' }}>
                Delivered to <strong>{dispatchResult.ward_name}</strong> across{' '}
                <strong>{dispatchResult.channels_used?.join(', ')}</strong>.
              </p>

              <div
                style={{
                  background: '#FFFFFF',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--border-subtle)',
                  padding: '14px',
                  fontSize: '12.5px',
                  textAlign: 'left',
                  marginBottom: '20px',
                  display: 'grid',
                  gridTemplateColumns: '1fr 1fr',
                  gap: '10px'
                }}
              >
                <div>
                  <span style={{ color: 'var(--text-muted)' }}>Audit Log ID:</span>{' '}
                  <strong style={{ fontFamily: 'var(--font-mono)' }}>{dispatchResult.alert_id}</strong>
                </div>
                <div>
                  <span style={{ color: 'var(--text-muted)' }}>Recipients Reached:</span>{' '}
                  <strong style={{ color: '#2D6A4F' }}>{dispatchResult.recipients_reached} Active Nodes</strong>
                </div>
                <div>
                  <span style={{ color: 'var(--text-muted)' }}>Web Push Notification:</span>{' '}
                  <strong style={{ color: '#2D6A4F' }}>TRIGGERED (0ms)</strong>
                </div>
                <div>
                  <span style={{ color: 'var(--text-muted)' }}>Amazon SNS Delivery:</span>{' '}
                  <strong style={{ color: '#2D6A4F' }}>ONLINE</strong>
                </div>
              </div>

              <div style={{ display: 'flex', gap: '10px', justifyContent: 'center' }}>
                <button
                  onClick={() => setDispatchResult(null)}
                  className="air-btn-primary"
                  style={{ padding: '9px 18px', fontSize: '12.5px' }}
                >
                  DISPATCH ANOTHER ALERT
                </button>
                <button
                  onClick={onClose}
                  className="air-btn-secondary"
                  style={{ padding: '9px 18px', fontSize: '12.5px' }}
                >
                  CLOSE
                </button>
              </div>
            </div>
          ) : (
            /* Alert Configuration Form */
            <div style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
              {/* Row 1: Target Ward & Severity */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '12px', fontWeight: 700, color: 'var(--forest-900)', marginBottom: '5px' }}>
                    TARGET AIRSHED / WARD:
                  </label>
                  <select
                    value={wardId}
                    onChange={(e) => setWardId(e.target.value)}
                    style={{
                      width: '100%',
                      padding: '9px 12px',
                      borderRadius: 'var(--radius-sm)',
                      border: '1px solid var(--border-light)',
                      fontSize: '13px',
                      background: 'var(--bg-canvas)'
                    }}
                  >
                    <option value="all_delhi_ncr">All Delhi NCR Airshed (Broadcast)</option>
                    <option value="anand_vihar">Anand Vihar / East Delhi (AQI 388)</option>
                    <option value="bawana_dtu">Bawana / DTU &amp; North Delhi (AQI 345)</option>
                    <option value="rohini">Rohini Sector 16 (AQI 362)</option>
                    <option value="noida_sec62">Noida Sector 62 / Indirapuram (AQI 328)</option>
                    <option value="punjabi_bagh">Punjabi Bagh / West Delhi (AQI 371)</option>
                    <option value="connaught_place">Connaught Place / Central (AQI 275)</option>
                    <option value="gurugram_cyber">Gurugram Cyber City (AQI 298)</option>
                    <option value="dwarka_sec8">Dwarka Sector 8 (AQI 312)</option>
                  </select>
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '12px', fontWeight: 700, color: 'var(--forest-900)', marginBottom: '5px' }}>
                    ALERT SEVERITY LEVEL:
                  </label>
                  <select
                    value={severity}
                    onChange={(e) => setSeverity(e.target.value)}
                    style={{
                      width: '100%',
                      padding: '9px 12px',
                      borderRadius: 'var(--radius-sm)',
                      border: '1px solid var(--border-light)',
                      fontSize: '13px',
                      fontWeight: 700,
                      color: severity === 'EMERGENCY' || severity === 'SEVERE' ? '#991B1B' : '#D97706',
                      background: 'var(--bg-canvas)'
                    }}
                  >
                    <option value="SEVERE">Severe (AQI 301 - 400)</option>
                    <option value="EMERGENCY">Emergency / Hazardous (AQI 400+)</option>
                    <option value="VERY_POOR">Very Poor (AQI 251 - 300)</option>
                    <option value="POOR">Poor (AQI 201 - 250)</option>
                  </select>
                </div>
              </div>

              {/* Row 2: Category Trigger */}
              <div>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 700, color: 'var(--forest-900)', marginBottom: '5px' }}>
                  PHYSICAL DEGRADATION TRIGGER:
                </label>
                <select
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '9px 12px',
                    borderRadius: 'var(--radius-sm)',
                    border: '1px solid var(--border-light)',
                    fontSize: '13px',
                    background: 'var(--bg-canvas)'
                  }}
                >
                  <option value="NOCTURNAL_INVERSION_COLLAPSE">
                    Atmospheric Boundary Layer Collapse &amp; Capping Lid (PBL &lt; 210m)
                  </option>
                  <option value="UPWIND_STUBBLE_PLUME_SURGE">
                    Transboundary Stubble Smoke Plume Advection (NASA FIRMS Detected)
                  </option>
                  <option value="ROAD_TRANSPORT_PEAK_STAGNATION">
                    High Vehicular Inversion Trapping on Major Ring Corridors
                  </option>
                  <option value="INDUSTRIAL_DUST_SPIKE">
                    Construction &amp; Industrial Particulate Resuspension Surge
                  </option>
                </select>
              </div>

              {/* Target Audiences */}
              <div>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 700, color: 'var(--forest-900)', marginBottom: '6px' }}>
                  TARGET STAKEHOLDER RECIPIENTS:
                </label>
                <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                  {[
                    { id: 'schools', label: '2,840 Schools & Daycares' },
                    { id: 'citizens', label: 'Vulnerable Citizens & RWAs' },
                    { id: 'hospitals', label: 'Hospital ICUs & Pulmonology' },
                    { id: 'traffic', label: 'Traffic Police & RTO' },
                    { id: 'construction', label: 'Construction Wardens' }
                  ].map((aud) => (
                    <button
                      key={aud.id}
                      type="button"
                      onClick={() => toggleAudience(aud.id)}
                      style={{
                        padding: '6px 12px',
                        borderRadius: 'var(--radius-pill)',
                        fontSize: '12px',
                        fontWeight: 700,
                        border: audiences.includes(aud.id) ? '1px solid #2D6A4F' : '1px solid var(--border-light)',
                        background: audiences.includes(aud.id) ? '#D8F3DC' : 'var(--bg-canvas)',
                        color: audiences.includes(aud.id) ? '#1B4332' : 'var(--text-secondary)',
                        cursor: 'pointer',
                        transition: 'all 0.15s'
                      }}
                    >
                      {aud.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Dispatch Channels */}
              <div>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 700, color: 'var(--forest-900)', marginBottom: '6px' }}>
                  ACTIVE DISPATCH CHANNELS:
                </label>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: '8px' }}>
                  {[
                    { id: 'web_push', label: 'Web Push', icon: <BellRing size={13} /> },
                    { id: 'whatsapp', label: 'WhatsApp', icon: <Smartphone size={13} /> },
                    { id: 'sms', label: 'SMS Gateway', icon: <Mail size={13} /> },
                    { id: 'sns_broadcast', label: 'AWS SNS Topic', icon: <Share2 size={13} /> },
                    { id: 'smart_vms', label: 'Smart City VMS', icon: <Tv size={13} /> }
                  ].map((ch) => (
                    <button
                      key={ch.id}
                      type="button"
                      onClick={() => toggleChannel(ch.id)}
                      style={{
                        padding: '8px 12px',
                        borderRadius: 'var(--radius-sm)',
                        fontSize: '12px',
                        fontWeight: 700,
                        border: channels.includes(ch.id) ? '1px solid #2D6A4F' : '1px solid var(--border-light)',
                        background: channels.includes(ch.id) ? '#D8F3DC' : 'var(--bg-canvas)',
                        color: channels.includes(ch.id) ? '#1B4332' : 'var(--text-secondary)',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px',
                        transition: 'all 0.15s'
                      }}
                    >
                      {ch.icon}
                      <span>{ch.label}</span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Message Preview */}
              <div>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 700, color: 'var(--forest-900)', marginBottom: '4px' }}>
                  DISPATCH MESSAGE BODY:
                </label>
                <textarea
                  value={customMessage}
                  onChange={(e) => setCustomMessage(e.target.value)}
                  rows={3}
                  style={{
                    width: '100%',
                    padding: '10px 12px',
                    borderRadius: 'var(--radius-sm)',
                    border: '1px solid var(--border-light)',
                    fontSize: '13px',
                    background: 'var(--bg-canvas)',
                    fontFamily: 'inherit',
                    resize: 'vertical'
                  }}
                />
              </div>

              {/* Action Submit Button */}
              <button
                type="button"
                onClick={handleDispatch}
                disabled={isSending}
                className="air-btn-primary"
                style={{
                  justifyContent: 'center',
                  padding: '13px 20px',
                  fontSize: '14px',
                  marginTop: '4px'
                }}
              >
                <Send size={16} />
                <span>{isSending ? 'DISPATCHING TO ALL CHANNELS...' : 'DISPATCH LIVE MULTI-CHANNEL GEO-ALERT'}</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
