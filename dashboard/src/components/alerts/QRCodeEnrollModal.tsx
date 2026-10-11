import React, { useState, useEffect } from 'react';
import {
  X,
  QrCode,
  Smartphone,
  Check,
  Copy,
  ExternalLink,
  ShieldCheck,
  Bell,
  Download,
  MessageSquare,
  Globe,
  Send,
  MapPin,
  CheckCircle2,
  GraduationCap,
  Sparkles,
  Mail,
  Inbox
} from 'lucide-react';
import QRCode from 'qrcode';

interface QRCodeEnrollModalProps {
  isOpen: boolean;
  onClose: () => void;
  onNavigateToCitizen: () => void;
}

interface WardOption {
  id: string;
  name: string;
  district: string;
  baseAqi: number;
}

const DELHI_WARDS: WardOption[] = [
  { id: 'anand_vihar', name: 'Anand Vihar', district: 'East Delhi', baseAqi: 388 },
  { id: 'punjabi_bagh', name: 'Punjabi Bagh', district: 'West Delhi', baseAqi: 320 },
  { id: 'bawana', name: 'Bawana Industrial', district: 'North-West Delhi', baseAqi: 375 },
  { id: 'dtu', name: 'DTU Shahbad Daulatpur', district: 'North Delhi', baseAqi: 310 },
  { id: 'rk_puram', name: 'R.K. Puram', district: 'South Delhi', baseAqi: 295 },
  { id: 'connaught_place', name: 'Connaught Place', district: 'Central Delhi', baseAqi: 240 },
  { id: 'noida_sec62', name: 'Noida Sector-62', district: 'Gautam Buddha Nagar', baseAqi: 315 },
  { id: 'gurugram_cybercity', name: 'Gurugram CyberCity', district: 'Gurugram NCR', baseAqi: 285 }
];

export const QRCodeEnrollModal: React.FC<QRCodeEnrollModalProps> = ({
  isOpen,
  onClose,
  onNavigateToCitizen
}) => {
  const [activeTab, setActiveTab] = useState<'email' | 'whatsapp' | 'web'>('email');
  const [selectedWardId, setSelectedWardId] = useState<string>('anand_vihar');
  const [copied, setCopied] = useState<boolean>(false);
  const [qrDataUrl, setQrDataUrl] = useState<string>('');

  // Email quick-dispatch state
  const [testEmail, setTestEmail] = useState<string>('samplebot.reply@gmail.com');
  const [testName, setTestName] = useState<string>('Delhi Resident');
  const [sendingEmail, setSendingEmail] = useState<boolean>(false);
  const [emailSuccess, setEmailSuccess] = useState<any | null>(null);

  const selectedWard = DELHI_WARDS.find((w) => w.id === selectedWardId) || DELHI_WARDS[0];

  const localNetworkHost = typeof window !== 'undefined' && window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1'
    ? window.location.host
    : '192.168.1.102:8000';
  const mobilePortalUrl = `http://${localNetworkHost}/mobile?ward=${selectedWard.id}`;
  const whatsappPhone = '919876543210';
  const whatsappText = `START AERIS AIR ALERTS ${selectedWard.name.toUpperCase()}`;
  const whatsappUrl = `https://wa.me/${whatsappPhone}?text=${encodeURIComponent(whatsappText)}`;
  const webPortalUrl = `http://${localNetworkHost}/mobile`;

  const activeTargetUrl = activeTab === 'email' ? mobilePortalUrl : activeTab === 'whatsapp' ? whatsappUrl : webPortalUrl;

  useEffect(() => {
    if (isOpen) {
      QRCode.toDataURL(activeTargetUrl, {
        width: 250,
        margin: 2,
        color: {
          dark: '#081C15',
          light: '#FFFFFF'
        },
        errorCorrectionLevel: 'M'
      })
        .then((url) => setQrDataUrl(url))
        .catch((err) => console.error('QR code generation error:', err));
    }
  }, [isOpen, activeTargetUrl, activeTab]);

  if (!isOpen) return null;

  const handleCopyLink = () => {
    navigator.clipboard?.writeText(activeTargetUrl);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  const handleDownloadQR = () => {
    if (!qrDataUrl) return;
    const a = document.createElement('a');
    a.href = qrDataUrl;
    a.download = `AERIS-${activeTab}-alerts-${selectedWard.id}.png`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  const handleSendInstantEmail = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!testEmail || !testEmail.includes('@')) return;
    setSendingEmail(true);
    try {
      const res = await fetch('/api/alerts/subscribe', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: testName || 'Citizen',
          email: testEmail,
          ward_id: selectedWard.id,
          role: 'citizen',
          channels: ['email', 'push']
        })
      });
      const data = await res.json();
      setEmailSuccess(data);
    } catch (err) {
      console.error('Email registration error:', err);
    } finally {
      setSendingEmail(false);
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
        background: 'rgba(8, 28, 21, 0.85)',
        backdropFilter: 'blur(12px)',
        zIndex: 99999,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '20px',
        overflowY: 'auto'
      }}
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        className="air-card"
        style={{
          background: '#FFFFFF',
          borderRadius: 'var(--radius-xl)',
          width: '100%',
          maxWidth: '580px',
          maxHeight: '94vh',
          overflowY: 'auto',
          boxShadow: '0 25px 60px -10px rgba(0, 0, 0, 0.45)',
          border: '1.5px solid rgba(82, 183, 136, 0.3)',
          animation: 'fadeIn 0.22s cubic-bezier(0.16, 1, 0.3, 1)',
          position: 'relative',
          zIndex: 100000
        }}
      >
        {/* Modal Header */}
        <div
          style={{
            background: 'linear-gradient(135deg, #081C15 0%, #1B4332 60%, #2D6A4F 100%)',
            color: '#FFFFFF',
            padding: '20px 24px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            borderBottom: '1px solid rgba(255, 255, 255, 0.1)'
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
              <QrCode size={20} color="#74C69D" />
            </div>
            <div>
              <h3 style={{ fontFamily: 'var(--font-display)', margin: 0, fontSize: '17px', fontWeight: 800, letterSpacing: '-0.3px' }}>
                CITIZEN &amp; SCHOOL QR ALERT GATEWAY
              </h3>
              <span style={{ fontSize: '12px', color: '#D8F3DC' }}>
                Real-Time Email &amp; WhatsApp Air Quality Warnings
              </span>
            </div>
          </div>
          <button
            onClick={onClose}
            aria-label="Close modal"
            style={{
              background: 'transparent',
              border: 'none',
              color: '#B7E4C7',
              cursor: 'pointer',
              padding: '6px',
              borderRadius: '999px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              transition: 'background 0.15s ease'
            }}
          >
            <X size={20} />
          </button>
        </div>

        {/* 3-Tab Selection Header */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr 1fr',
            background: '#F4F2EB',
            padding: '6px 10px',
            gap: '6px',
            borderBottom: '1px solid var(--border-subtle)'
          }}
        >
          <button
            onClick={() => setActiveTab('email')}
            style={{
              padding: '8px 10px',
              borderRadius: 'var(--radius-pill)',
              border: 'none',
              background: activeTab === 'email' ? '#1B4332' : 'transparent',
              color: activeTab === 'email' ? '#FFFFFF' : 'var(--text-secondary)',
              fontWeight: 800,
              fontSize: '11.5px',
              cursor: 'pointer',
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '5px',
              transition: 'all 0.15s ease',
              boxShadow: activeTab === 'email' ? '0 2px 8px rgba(27, 67, 50, 0.25)' : 'none'
            }}
          >
            <Mail size={13} color={activeTab === 'email' ? '#74C69D' : undefined} />
            <span>EMAIL ALERTS</span>
          </button>

          <button
            onClick={() => setActiveTab('whatsapp')}
            style={{
              padding: '8px 10px',
              borderRadius: 'var(--radius-pill)',
              border: 'none',
              background: activeTab === 'whatsapp' ? '#1B4332' : 'transparent',
              color: activeTab === 'whatsapp' ? '#FFFFFF' : 'var(--text-secondary)',
              fontWeight: 800,
              fontSize: '11.5px',
              cursor: 'pointer',
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '5px',
              transition: 'all 0.15s ease',
              boxShadow: activeTab === 'whatsapp' ? '0 2px 8px rgba(27, 67, 50, 0.25)' : 'none'
            }}
          >
            <MessageSquare size={13} color={activeTab === 'whatsapp' ? '#74C69D' : undefined} />
            <span>WHATSAPP</span>
          </button>

          <button
            onClick={() => setActiveTab('web')}
            style={{
              padding: '8px 10px',
              borderRadius: 'var(--radius-pill)',
              border: 'none',
              background: activeTab === 'web' ? '#1B4332' : 'transparent',
              color: activeTab === 'web' ? '#FFFFFF' : 'var(--text-secondary)',
              fontWeight: 800,
              fontSize: '11.5px',
              cursor: 'pointer',
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '5px',
              transition: 'all 0.15s ease',
              boxShadow: activeTab === 'web' ? '0 2px 8px rgba(27, 67, 50, 0.25)' : 'none'
            }}
          >
            <Globe size={13} color={activeTab === 'web' ? '#74C69D' : undefined} />
            <span>WEB VIEW</span>
          </button>
        </div>

        {/* Modal Body */}
        <div style={{ padding: '22px 26px', textAlign: 'center' }}>
          
          {/* Ward Target Selector */}
          <div
            style={{
              background: '#F8FAF9',
              border: '1px solid #CBD5E1',
              borderRadius: 'var(--radius-md)',
              padding: '10px 14px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: '12px',
              marginBottom: '16px',
              textAlign: 'left'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <MapPin size={16} color="#1B4332" />
              <div>
                <div style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text-muted)' }}>TARGET AIRSHED WARD:</div>
                <div style={{ fontSize: '13px', fontWeight: 800, color: 'var(--forest-900)' }}>
                  {selectedWard.name} ({selectedWard.district})
                </div>
              </div>
            </div>

            <select
              value={selectedWardId}
              onChange={(e) => setSelectedWardId(e.target.value)}
              style={{
                background: '#FFFFFF',
                border: '1px solid #CBD5E1',
                borderRadius: '6px',
                padding: '5px 10px',
                fontSize: '12px',
                fontWeight: 700,
                color: '#0F172A',
                outline: 'none',
                cursor: 'pointer'
              }}
            >
              {DELHI_WARDS.map((w) => (
                <option key={w.id} value={w.id}>
                  {w.name} — AQI {w.baseAqi}
                </option>
              ))}
            </select>
          </div>

          {/* Description Text */}
          <p style={{ fontSize: '13px', color: 'var(--text-secondary)', margin: '0 0 14px 0', lineHeight: 1.5 }}>
            {activeTab === 'email' ? (
              <>
                Scan with any phone camera to open the <strong>Mobile Registration Form</strong>, enter your email, and receive instant 6-hour advance air warnings directly in your inbox.
              </>
            ) : activeTab === 'whatsapp' ? (
              <>
                Scan with any phone camera or Google Lens to immediately open <strong>WhatsApp</strong> and subscribe for automated air pollution warnings.
              </>
            ) : (
              <>
                Scan with any phone camera to open the full interactive <strong>Mobile Web Dashboard</strong> with live 3D plumes and station telemetry.
              </>
            )}
          </p>

          {/* Scannable QR Container */}
          <div
            style={{
              background: '#FFFFFF',
              border: '2px solid #CBD5E1',
              borderRadius: 'var(--radius-lg)',
              padding: '10px',
              display: 'inline-block',
              margin: '0 auto 14px auto',
              boxShadow: '0 6px 24px rgba(8, 28, 21, 0.08)'
            }}
          >
            {qrDataUrl ? (
              <img
                src={qrDataUrl}
                alt="AERIS Scannable Alert QR Code"
                style={{ width: '180px', height: '180px', display: 'block', borderRadius: '6px' }}
              />
            ) : (
              <div style={{ width: '180px', height: '180px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', fontSize: '12px' }}>
                Generating Scannable QR...
              </div>
            )}
          </div>

          {/* TAB 1: Instant Email Registration & Live Test Box */}
          {activeTab === 'email' && (
            <div
              style={{
                background: '#F0FDF4',
                border: '1px solid #BBF7D0',
                borderRadius: 'var(--radius-md)',
                padding: '16px',
                marginBottom: '16px',
                textAlign: 'left'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#166534', fontWeight: 800, fontSize: '12.5px', marginBottom: '8px' }}>
                <Mail size={15} />
                <span>INSTANT MOBILE EMAIL REGISTRATION &amp; TEST DISPATCH</span>
              </div>
              <p style={{ fontSize: '11.5px', color: '#14532D', margin: '0 0 10px 0', lineHeight: 1.45 }}>
                Enter your email address below (or scan on your mobile phone) to register in the system and trigger an immediate real-time air quality warning email:
              </p>

              {emailSuccess ? (
                <div style={{ background: '#FFFFFF', border: '1.5px solid #22C55E', borderRadius: '8px', padding: '12px', marginTop: '6px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#15803D', fontWeight: 800, fontSize: '13px' }}>
                    <CheckCircle2 size={16} />
                    <span>EMAIL DISPATCHED SUCCESSFULLY!</span>
                  </div>
                  <p style={{ fontSize: '12px', color: '#374151', margin: '6px 0 8px 0', lineHeight: 1.45 }}>
                    {emailSuccess.message}
                  </p>
                  <div style={{ fontSize: '11px', color: '#15803D', background: '#F0FDF4', padding: '6px 10px', borderRadius: '4px', fontFamily: 'monospace' }}>
                    Sent to: <strong>{emailSuccess.email_sent_to}</strong>
                  </div>
                  <button
                    onClick={() => setEmailSuccess(null)}
                    className="air-btn-secondary"
                    style={{ marginTop: '10px', padding: '5px 12px', fontSize: '11.5px' }}
                  >
                    SEND TO ANOTHER EMAIL
                  </button>
                </div>
              ) : (
                <form onSubmit={handleSendInstantEmail} style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                    <div>
                      <label style={{ fontSize: '10.5px', fontWeight: 700, color: '#14532D', display: 'block', marginBottom: '2px' }}>
                        YOUR NAME / SCHOOL:
                      </label>
                      <input
                        type="text"
                        value={testName}
                        onChange={(e) => setTestName(e.target.value)}
                        placeholder="e.g. Ramesh Kumar"
                        style={{ width: '100%', padding: '7px 10px', fontSize: '12px', borderRadius: '5px', border: '1px solid #CBD5E1', background: '#FFFFFF' }}
                      />
                    </div>
                    <div>
                      <label style={{ fontSize: '10.5px', fontWeight: 700, color: '#14532D', display: 'block', marginBottom: '2px' }}>
                        EMAIL ADDRESS:
                      </label>
                      <input
                        type="email"
                        required
                        value={testEmail}
                        onChange={(e) => setTestEmail(e.target.value)}
                        placeholder="yourname@gmail.com"
                        style={{ width: '100%', padding: '7px 10px', fontSize: '12px', borderRadius: '5px', border: '1px solid #CBD5E1', background: '#FFFFFF' }}
                      />
                    </div>
                  </div>

                  <button
                    type="submit"
                    disabled={sendingEmail}
                    className="air-btn-primary"
                    style={{ justifyContent: 'center', padding: '9px', fontSize: '12.5px', marginTop: '4px' }}
                  >
                    <Send size={13} />
                    <span>{sendingEmail ? 'REGISTERING & DISPATCHING EMAIL...' : 'REGISTER & DISPATCH AIR WARNING EMAIL NOW'}</span>
                  </button>
                </form>
              )}
            </div>
          )}

          {/* TAB 2: WhatsApp Preview Box */}
          {activeTab === 'whatsapp' && (
            <div
              style={{
                background: '#F0FDF4',
                border: '1px solid #BBF7D0',
                borderRadius: 'var(--radius-md)',
                padding: '14px',
                marginBottom: '16px',
                textAlign: 'left'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#166534', fontWeight: 800, fontSize: '12px', marginBottom: '6px' }}>
                <MessageSquare size={14} />
                <span>WHAT HAPPENS ON SCAN:</span>
              </div>
              <ol style={{ margin: '0 0 10px 0', paddingLeft: '18px', fontSize: '12px', color: '#14532D', lineHeight: 1.5 }}>
                <li>Opens WhatsApp with pre-filled message: <strong>"{whatsappText}"</strong></li>
                <li>Tap <strong>Send</strong> in WhatsApp.</li>
                <li>AERIS Cloud instantly replies with live AQI, 6-hour inversion warning, and school guidelines!</li>
              </ol>

              {/* Simulated WhatsApp Reply Bubble */}
              <div
                style={{
                  background: '#FFFFFF',
                  border: '1px solid #DCFCE7',
                  borderLeft: '4px solid #16A34A',
                  borderRadius: '6px',
                  padding: '10px 12px',
                  fontSize: '11.5px',
                  color: '#1F2937',
                  lineHeight: 1.45,
                  boxShadow: '0 1px 3px rgba(0,0,0,0.05)'
                }}
              >
                <div style={{ fontWeight: 800, color: '#166534', marginBottom: '3px' }}>
                  AERIS AIRSHED BOT • {selectedWard.name.toUpperCase()}
                </div>
                <div>Current AQI: <strong>{selectedWard.baseAqi} (Severe)</strong> • Dominant: PM2.5</div>
                <div style={{ color: '#DC2626', fontWeight: 700, marginTop: '2px' }}>
                  Warning: Severe thermal capping lid expected from 19:30 IST.
                </div>
                <div style={{ color: '#0369A1', marginTop: '2px' }}>
                  School Action: Suspend outdoor assemblies & sports.
                </div>
              </div>
            </div>
          )}

          {/* Action Row */}
          <div style={{ display: 'flex', justifyContent: 'center', gap: '8px', marginBottom: '16px', flexWrap: 'wrap' }}>
            <button
              onClick={handleDownloadQR}
              style={{
                background: '#FFFFFF',
                color: 'var(--forest-800)',
                border: '1px solid #CBD5E1',
                borderRadius: '999px',
                padding: '7px 16px',
                fontSize: '12px',
                fontWeight: 700,
                cursor: 'pointer',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                boxShadow: 'var(--shadow-sm)'
              }}
            >
              <Download size={13} />
              <span>DOWNLOAD POSTER QR (PNG)</span>
            </button>

            {activeTab === 'whatsapp' ? (
              <a
                href={whatsappUrl}
                target="_blank"
                rel="noreferrer"
                style={{
                  background: '#16A34A',
                  color: '#FFFFFF',
                  border: 'none',
                  borderRadius: '999px',
                  padding: '7px 16px',
                  fontSize: '12px',
                  fontWeight: 800,
                  cursor: 'pointer',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '6px',
                  textDecoration: 'none',
                  boxShadow: '0 2px 8px rgba(22, 163, 74, 0.3)'
                }}
              >
                <MessageSquare size={13} />
                <span>OPEN IN WHATSAPP WEB</span>
              </a>
            ) : (
              <button
                onClick={handleCopyLink}
                style={{
                  background: copied ? '#2D6A4F' : '#1B4332',
                  color: '#FFFFFF',
                  border: 'none',
                  borderRadius: '999px',
                  padding: '7px 16px',
                  fontSize: '12px',
                  fontWeight: 700,
                  cursor: 'pointer',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '5px'
                }}
              >
                {copied ? <Check size={13} /> : <Copy size={13} />}
                <span>{copied ? 'LINK COPIED' : 'COPY REGISTRATION LINK'}</span>
              </button>
            )}
          </div>

          {/* Value Highlights */}
          <div style={{ display: 'flex', justifyContent: 'center', gap: '8px', marginBottom: '16px', flexWrap: 'wrap' }}>
            <span style={{ fontSize: '11px', background: '#D8F3DC', color: '#1B4332', padding: '3px 9px', borderRadius: '999px', fontWeight: 700, display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
              <ShieldCheck size={12} /> 100% Free Public System
            </span>
            <span style={{ fontSize: '11px', background: '#E8F5E9', color: '#2D6A4F', padding: '3px 9px', borderRadius: '999px', fontWeight: 700, display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
              <Smartphone size={12} /> Instant Mobile Email Registration
            </span>
            <span style={{ fontSize: '11px', background: '#FEF3C7', color: '#92400E', padding: '3px 9px', borderRadius: '999px', fontWeight: 700, display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
              <Bell size={12} /> Real-Time Inversion Alerts
            </span>
          </div>

          {/* Footer Navigation Button */}
          <button
            onClick={() => {
              onClose();
              onNavigateToCitizen();
            }}
            className="air-btn-primary"
            style={{
              width: '100%',
              justifyContent: 'center',
              padding: '11px',
              fontSize: '13px'
            }}
          >
            <span>VIEW CITIZEN &amp; SCHOOL SAFETY DASHBOARD</span>
            <ExternalLink size={14} />
          </button>
        </div>
      </div>
    </div>
  );
};
