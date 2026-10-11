import React, { useState, useEffect } from 'react';
import {
  ShieldAlert,
  GraduationCap,
  HeartPulse,
  Wind,
  Home,
  QrCode,
  Smartphone,
  Mail,
  CheckCircle2,
  Download,
  Bell,
  MapPin,
  Send,
  Activity,
  ArrowUpRight,
  FileText,
  Clock,
  AlertTriangle,
  Building2,
  Users
} from 'lucide-react';
import {
  ActiveAlertsResponse,
  ActiveGeoAlert,
  WardInfo,
  SchoolSafetyProtocolResponse
} from '../../types';
import { fetchActiveAlerts, fetchWards, fetchSchoolSafety, subscribeCitizen } from '../../api';

interface CitizenCommunityPortalProps {
  onOpenBroadcastModal: () => void;
  onOpenQRModal: () => void;
}

export const CitizenCommunityPortal: React.FC<CitizenCommunityPortalProps> = ({
  onOpenBroadcastModal,
  onOpenQRModal
}) => {
  const [alertsData, setAlertsData] = useState<ActiveAlertsResponse | null>(null);
  const [wards, setWards] = useState<WardInfo[]>([]);
  const [schoolProtocol, setSchoolProtocol] = useState<SchoolSafetyProtocolResponse | null>(null);
  const [selectedWardId, setSelectedWardId] = useState<string>('anand_vihar');
  const [loading, setLoading] = useState<boolean>(true);

  // Subscription Form State
  const [subName, setSubName] = useState<string>('');
  const [subPhone, setSubPhone] = useState<string>('');
  const [subEmail, setSubEmail] = useState<string>('');
  const [subRole, setSubRole] = useState<string>('citizen');
  const [subChannels, setSubChannels] = useState<string[]>(['push', 'whatsapp']);
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [subSuccess, setSubSuccess] = useState<any | null>(null);

  useEffect(() => {
    const loadAll = async () => {
      setLoading(true);
      try {
        const [a, w, s] = await Promise.allSettled([
          fetchActiveAlerts(),
          fetchWards(),
          fetchSchoolSafety()
        ]);
        if (a.status === 'fulfilled') setAlertsData(a.value);
        if (w.status === 'fulfilled') setWards(w.value?.wards || []);
        if (s.status === 'fulfilled') setSchoolProtocol(s.value);
      } catch (err) {
        console.error('Citizen portal load error:', err);
      } finally {
        setLoading(false);
      }
    };
    loadAll();
  }, []);

  const selectedAlert: ActiveGeoAlert | undefined = alertsData?.alerts?.find(
    (a) => a.ward_id === selectedWardId
  ) || alertsData?.alerts?.[0];

  const selectedWardInfo: WardInfo | undefined = wards.find((w) => w.id === selectedWardId);

  const toggleSubChannel = (ch: string) => {
    setSubChannels((prev) =>
      prev.includes(ch) ? prev.filter((c) => c !== ch) : [...prev, ch]
    );
  };

  const handleSubscribe = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!subName.trim()) return;
    setSubmitting(true);
    try {
      const res = await subscribeCitizen({
        name: subName,
        phone: subPhone,
        email: subEmail,
        ward_id: selectedWardId,
        role: subRole,
        channels: subChannels
      });
      setSubSuccess(res);
      setSubName('');
      setSubPhone('');
      setSubEmail('');
    } catch (err) {
      console.error('Subscription error:', err);
    } finally {
      setSubmitting(false);
    }
  };

  const handlePrintSchoolAdvisory = () => {
    const win = window.open('', '_blank');
    if (!win) return;
    win.document.write(`
      <!DOCTYPE html>
      <html>
        <head>
          <title>AERIS Official School Air Safety Advisory</title>
          <style>
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; padding: 40px; color: #081C15; background: #FAF9F5; line-height: 1.5; }
            h1 { color: #1B4332; border-bottom: 2px solid #2D6A4F; padding-bottom: 10px; font-size: 20px; }
            .badge { background: #1B4332; color: white; padding: 4px 12px; border-radius: 999px; font-weight: bold; font-size: 13px; }
            table { width: 100%; border-collapse: collapse; margin-top: 24px; font-size: 13px; }
            th, td { border: 1px solid #CBD5E1; padding: 12px 14px; text-align: left; }
            th { background: #E8F5E9; color: #1B4332; font-weight: 800; }
            ul { margin-top: 10px; padding-left: 20px; }
            li { margin-bottom: 8px; }
            .footer { margin-top: 40px; font-size: 11px; color: #64748B; border-top: 1px solid #CBD5E1; padding-top: 12px; }
          </style>
        </head>
        <body>
          <h1>AERIS — OFFICIAL SCHOOL AIR SAFETY & EARLY WARNING DIRECTIVE</h1>
          <p><strong>Airshed Ward:</strong> ${selectedAlert?.ward_name || 'Delhi NCR Airshed'}</p>
          <p><strong>Issued Date:</strong> ${new Date().toLocaleDateString('en-IN', { day: 'numeric', month: 'long', year: 'numeric' })}</p>
          <p><strong>Air Quality Status:</strong> <span class="badge">AQI ${selectedAlert?.current_aqi || 388} (${selectedAlert?.severity || 'SEVERE'})</span></p>
          <p><strong>Statutory Reference:</strong> CAQM & NCPCR Guidelines for Child Respiratory Protection</p>
          
          <h3 style="margin-top: 24px; color: #1B4332;">MANDATORY DIRECTIVES FOR SCHOOL ADMINISTRATORS:</h3>
          <ul>
            <li><strong>Morning Assemblies:</strong> SUSPEND ALL OUTDOOR GATHERINGS. Shift to classroom intercom or indoor halls.</li>
            <li><strong>Sports & Recess:</strong> Restrict all physical sports and outdoor running activities.</li>
            <li><strong>Student Transit:</strong> Recommend N95/FFP2 masks during morning transit hours (06:30 - 09:30 IST).</li>
            <li><strong>Indoor Purification:</strong> Operate HEPA filtration units continuously in primary wings and libraries.</li>
          </ul>

          <div class="footer">
            Issued by AERIS Atmospheric Decision Intelligence System · Powered by Koopman Operator Dynamical Rollouts.
          </div>
        </body>
      </html>
    `);
    win.document.close();
    win.print();
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '22px' }}>
      
      {/* 1. Header Banner */}
      <div
        className="air-card"
        style={{
          background: 'linear-gradient(135deg, #081C15 0%, #1B4332 55%, #2D6A4F 100%)',
          borderRadius: 'var(--radius-xl)',
          padding: '28px 32px',
          color: '#FFFFFF',
          boxShadow: 'var(--shadow-lg)'
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
              <span
                style={{
                  background: 'rgba(255, 255, 255, 0.14)',
                  color: '#D8F3DC',
                  fontSize: '11px',
                  fontWeight: 800,
                  padding: '3px 10px',
                  borderRadius: '999px',
                  letterSpacing: '0.4px',
                  border: '1px solid rgba(216, 243, 220, 0.2)'
                }}
              >
                PUBLIC AIRSHED &amp; SCHOOL SAFETY
              </span>
              <span style={{ color: '#95D5B2', fontSize: '12px' }}>
                Track 01: Air • 72h Early Warnings
              </span>
            </div>

            <h2 style={{ fontFamily: 'var(--font-display)', fontSize: '24px', fontWeight: 800, margin: '0 0 6px 0', letterSpacing: '-0.4px' }}>
              Neighborhood Air Quality Alerts &amp; School Safety Protocol
            </h2>

            <p style={{ margin: 0, fontSize: '13.5px', color: '#D8F3DC', lineHeight: 1.5, opacity: 0.9, maxWidth: '750px' }}>
              Real-time atmospheric hazard intelligence with 6-hour advance lead times before nocturnal boundary layer collapse.
            </p>
          </div>

          <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
            <button
              onClick={onOpenQRModal}
              className="air-btn-secondary"
              style={{
                background: '#FFFFFF',
                color: '#1B4332',
                border: 'none',
                padding: '10px 18px',
                fontSize: '13px'
              }}
            >
              <QrCode size={16} />
              <span>SCAN MOBILE QR</span>
            </button>

            <button
              onClick={onOpenBroadcastModal}
              style={{
                background: '#D97706',
                color: '#FFFFFF',
                border: 'none',
                borderRadius: '999px',
                padding: '10px 20px',
                fontSize: '13px',
                fontWeight: 800,
                cursor: 'pointer',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '7px',
                boxShadow: '0 4px 14px rgba(217, 119, 6, 0.35)'
              }}
            >
              <Send size={14} />
              <span>DISPATCH GEO-ALERT</span>
            </button>
          </div>
        </div>
      </div>

      {/* 2. Ward Selector Pill Bar */}
      <div
        className="air-card"
        style={{
          padding: '14px 20px',
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          flexWrap: 'wrap'
        }}
      >
        <span style={{ fontSize: '12.5px', fontWeight: 800, color: 'var(--forest-900)', display: 'flex', alignItems: 'center', gap: '6px' }}>
          <MapPin size={15} color="#2D6A4F" /> SELECT WARD:
        </span>

        <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', flex: 1 }}>
          {wards.map((w) => {
            const isSelected = w.id === selectedWardId;
            return (
              <button
                key={w.id}
                onClick={() => setSelectedWardId(w.id)}
                style={{
                  padding: '6px 12px',
                  borderRadius: 'var(--radius-pill)',
                  fontSize: '12px',
                  fontWeight: isSelected ? 800 : 600,
                  border: isSelected ? '1.5px solid #2D6A4F' : '1px solid var(--border-subtle)',
                  background: isSelected ? '#D8F3DC' : '#FFFFFF',
                  color: isSelected ? '#1B4332' : 'var(--text-secondary)',
                  cursor: 'pointer',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '6px',
                  transition: 'all 0.15s ease'
                }}
              >
                <span>{w.name}</span>
                <span
                  style={{
                    background: w.base_aqi > 350 ? '#FEE2E2' : w.base_aqi > 300 ? '#FFEDD5' : '#E8F5E9',
                    color: w.base_aqi > 350 ? '#991B1B' : w.base_aqi > 300 ? '#C2410C' : '#1B4332',
                    padding: '1px 6px',
                    borderRadius: '999px',
                    fontSize: '10px',
                    fontWeight: 800
                  }}
                >
                  AQI {w.base_aqi}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* 3. Executive KPI Cards for Selected Ward */}
      {selectedAlert && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '14px' }}>
          
          {/* KPI 1: Current AQI */}
          <div className="air-card" style={{ padding: '18px 20px', borderLeft: '4px solid #991B1B' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
              <span style={{ fontSize: '11.5px', color: 'var(--text-muted)', fontWeight: 700 }}>CURRENT AIR QUALITY</span>
              <span className="status-tag status-severe">{selectedAlert.severity}</span>
            </div>
            <div style={{ fontSize: '26px', fontWeight: 800, color: 'var(--forest-900)', fontFamily: 'var(--font-mono)' }}>
              AQI {selectedAlert.current_aqi}
            </div>
            <div style={{ fontSize: '11.5px', color: 'var(--text-secondary)', marginTop: '4px' }}>
              Dominant: <strong>PM2.5</strong> ({selectedWardInfo?.district})
            </div>
          </div>

          {/* KPI 2: Projected Peak */}
          <div className="air-card" style={{ padding: '18px 20px', borderLeft: '4px solid #D97706' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
              <span style={{ fontSize: '11.5px', color: 'var(--text-muted)', fontWeight: 700 }}>PROJECTED 24h PEAK</span>
              <span className="status-tag status-poor">Inversion Surge</span>
            </div>
            <div style={{ fontSize: '26px', fontWeight: 800, color: '#991B1B', fontFamily: 'var(--font-mono)' }}>
              AQI {selectedAlert.projected_peak_aqi}
            </div>
            <div style={{ fontSize: '11.5px', color: 'var(--text-secondary)', marginTop: '4px' }}>
              Peak Window: <strong>19:30 – 23:00 IST</strong>
            </div>
          </div>

          {/* KPI 3: School Alert Status */}
          <div className="air-card" style={{ padding: '18px 20px', borderLeft: '4px solid #DC2626' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
              <span style={{ fontSize: '11.5px', color: 'var(--text-muted)', fontWeight: 700 }}>SCHOOL ACTION LEVEL</span>
              <span className="status-tag status-very-poor">RED ALERT</span>
            </div>
            <div style={{ fontSize: '20px', fontWeight: 800, color: 'var(--forest-900)' }}>
              Outdoor Activities Suspended
            </div>
            <div style={{ fontSize: '11.5px', color: 'var(--text-secondary)', marginTop: '4px' }}>
              Covering <strong>{selectedWardInfo?.schools_count || 48}</strong> schools in zone
            </div>
          </div>

          {/* KPI 4: Action Lead Time */}
          <div className="air-card" style={{ padding: '18px 20px', borderLeft: '4px solid #2D6A4F' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
              <span style={{ fontSize: '11.5px', color: 'var(--text-muted)', fontWeight: 700 }}>PRE-INVERSION LEAD TIME</span>
              <span className="status-tag status-good">ACTIONABLE</span>
            </div>
            <div style={{ fontSize: '26px', fontWeight: 800, color: '#1B4332', fontFamily: 'var(--font-mono)' }}>
              +{selectedAlert.action_window_hours_left} Hours
            </div>
            <div style={{ fontSize: '11.5px', color: 'var(--text-secondary)', marginTop: '4px' }}>
              Advance mitigation window active
            </div>
          </div>
        </div>
      )}

      {/* 4. Visual 4-Card Health Directive Grid */}
      {selectedAlert && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '14px' }}>
          
          {/* Card 1: Sports / Jogging */}
          <div className="air-card" style={{ padding: '20px', background: '#FFFDF5', border: '1px solid #FEF3C7' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '10px' }}>
              <div style={{ background: '#FEF3C7', padding: '8px', borderRadius: '8px', color: '#B45309' }}>
                <Activity size={18} />
              </div>
              <div>
                <h4 style={{ margin: 0, fontSize: '14px', fontWeight: 800, color: '#92400E' }}>
                  Outdoor Sports &amp; Jogging
                </h4>
                <span style={{ fontSize: '11px', color: '#B45309' }}>Morning &amp; Evening Restriction</span>
              </div>
            </div>
            <p style={{ margin: 0, fontSize: '12.5px', color: '#78350F', lineHeight: 1.45 }}>
              {selectedAlert.health_advisory.outdoor_jogging}
            </p>
          </div>

          {/* Card 2: Vulnerable Groups */}
          <div className="air-card" style={{ padding: '20px', background: '#F8FAFC', border: '1px solid #E2E8F0' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '10px' }}>
              <div style={{ background: '#EFF6FF', padding: '8px', borderRadius: '8px', color: '#1D4ED8' }}>
                <HeartPulse size={18} />
              </div>
              <div>
                <h4 style={{ margin: 0, fontSize: '14px', fontWeight: 800, color: '#1E40AF' }}>
                  Vulnerable &amp; Asthmatics
                </h4>
                <span style={{ fontSize: '11px', color: '#3B82F6' }}>Children &amp; Senior Citizens</span>
              </div>
            </div>
            <p style={{ margin: 0, fontSize: '12.5px', color: '#1E3A8A', lineHeight: 1.45 }}>
              {selectedAlert.health_advisory.vulnerable_groups}
            </p>
          </div>

          {/* Card 3: Indoor Air */}
          <div className="air-card" style={{ padding: '20px', background: '#F2FAF5', border: '1px solid #D8F3DC' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '10px' }}>
              <div style={{ background: '#D8F3DC', padding: '8px', borderRadius: '8px', color: '#1B4332' }}>
                <Home size={18} />
              </div>
              <div>
                <h4 style={{ margin: 0, fontSize: '14px', fontWeight: 800, color: '#1B4332' }}>
                  Indoor Air Protection
                </h4>
                <span style={{ fontSize: '11px', color: '#2D6A4F' }}>Home &amp; Office Ventilation</span>
              </div>
            </div>
            <p style={{ margin: 0, fontSize: '12.5px', color: '#2D6A4F', lineHeight: 1.45 }}>
              {selectedAlert.health_advisory.air_purifiers}
            </p>
          </div>

          {/* Card 4: School Protocol */}
          <div className="air-card" style={{ padding: '20px', background: '#FEF2F2', border: '1px solid #FEE2E2' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '10px' }}>
              <div style={{ background: '#FEE2E2', padding: '8px', borderRadius: '8px', color: '#991B1B' }}>
                <GraduationCap size={18} />
              </div>
              <div>
                <h4 style={{ margin: 0, fontSize: '14px', fontWeight: 800, color: '#991B1B' }}>
                  School Mandatory Protocol
                </h4>
                <span style={{ fontSize: '11px', color: '#B91C1C' }}>CAQM Directives</span>
              </div>
            </div>
            <p style={{ margin: 0, fontSize: '12.5px', color: '#7F1D1D', lineHeight: 1.45 }}>
              {selectedAlert.school_protocol.recommendation}
            </p>
          </div>
        </div>
      )}

      {/* 5. Comprehensive School Safety Protocol Table */}
      {schoolProtocol && (
        <div className="air-card" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px', flexWrap: 'wrap', gap: '12px' }}>
            <div>
              <h3 style={{ fontFamily: 'var(--font-display)', margin: 0, fontSize: '17px', fontWeight: 800, color: 'var(--forest-900)' }}>
                CPCB &amp; AERIS COMPREHENSIVE SCHOOL AIR SAFETY PROTOCOL
              </h3>
              <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                Automated statutory guidelines covering {schoolProtocol.total_schools_covered_ncr} educational institutions
              </span>
            </div>

            <button
              onClick={handlePrintSchoolAdvisory}
              className="air-btn-secondary"
              style={{
                padding: '8px 16px',
                fontSize: '12px'
              }}
            >
              <Download size={14} />
              <span>EXPORT SCHOOL NOTICE (PDF)</span>
            </button>
          </div>

          {/* Clean Spacious Table */}
          <div className="table-responsive">
            <table className="portal-table">
              <thead>
                <tr>
                  <th style={{ width: '22%' }}>AQI Exposure Tier</th>
                  <th style={{ width: '22%' }}>Morning Assembly</th>
                  <th style={{ width: '20%' }}>Sports &amp; Recess</th>
                  <th style={{ width: '16%' }}>Mask Protocol</th>
                  <th style={{ width: '20%' }}>Indoor Classrooms</th>
                </tr>
              </thead>
              <tbody>
                {schoolProtocol.school_guidelines.map((g, idx) => {
                  const isCurrent = g.aqi_tier.includes('CURRENT') || g.aqi_tier.includes('301');
                  return (
                    <tr
                      key={idx}
                      style={{
                        background: isCurrent ? 'rgba(254, 242, 242, 0.7)' : undefined
                      }}
                    >
                      <td>
                        <div style={{ fontWeight: 800, color: isCurrent ? '#991B1B' : 'var(--forest-900)' }}>
                          {g.aqi_tier}
                        </div>
                      </td>
                      <td>
                        <strong style={{ color: isCurrent ? '#991B1B' : 'inherit' }}>
                          {g.outdoor_assemblies}
                        </strong>
                      </td>
                      <td>{g.sports_recess}</td>
                      <td>
                        <span
                          style={{
                            display: 'inline-block',
                            padding: '2px 8px',
                            borderRadius: '4px',
                            fontSize: '11px',
                            fontWeight: 700,
                            background: g.mask_protocol.includes('Mandatory') ? '#FEE2E2' : '#F1F5F9',
                            color: g.mask_protocol.includes('Mandatory') ? '#991B1B' : 'var(--text-secondary)'
                          }}
                        >
                          {g.mask_protocol}
                        </span>
                      </td>
                      <td style={{ color: 'var(--text-secondary)' }}>{g.indoor_action}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* 6. Citizen Enrollment & Alert Center Form */}
      <div
        className="air-card"
        style={{
          padding: '26px',
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
          gap: '24px'
        }}
      >
        {/* Left Form */}
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
            <Bell size={18} color="#2D6A4F" />
            <h3 style={{ fontFamily: 'var(--font-display)', margin: 0, fontSize: '17px', fontWeight: 800, color: 'var(--forest-900)' }}>
              FREE CITIZEN &amp; SCHOOL ALERT SUBSCRIPTION
            </h3>
          </div>
          <p style={{ fontSize: '12.5px', color: 'var(--text-secondary)', margin: '0 0 16px 0', lineHeight: 1.45 }}>
            Automated SMS, WhatsApp &amp; Push alerts dispatched via Amazon SNS before nocturnal thermal inversions.
          </p>

          {subSuccess ? (
            <div style={{ background: '#D8F3DC', border: '1px solid #74C69D', borderRadius: 'var(--radius-md)', padding: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#1B4332', fontWeight: 800, fontSize: '13.5px' }}>
                <CheckCircle2 size={17} color="#1B4332" /> SUBSCRIPTION ACTIVE
              </div>
              <p style={{ fontSize: '12.5px', color: '#2D6A4F', margin: '6px 0 10px 0' }}>
                {subSuccess.message}
              </p>
              <div style={{ fontSize: '11px', color: 'var(--text-secondary)', background: '#FFFFFF', padding: '8px', borderRadius: 'var(--radius-sm)' }}>
                Subscription ID: <strong style={{ fontFamily: 'monospace' }}>{subSuccess.subscription_id}</strong>
              </div>
              <button
                onClick={() => setSubSuccess(null)}
                className="air-btn-secondary"
                style={{ marginTop: '12px', padding: '6px 14px', fontSize: '11.5px' }}
              >
                ENROLL ANOTHER CITIZEN
              </button>
            </div>
          ) : (
            <form onSubmit={handleSubscribe} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '11.5px', fontWeight: 700, color: 'var(--forest-900)', marginBottom: '3px' }}>
                  NAME OR SCHOOL / INSTITUTION:
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Ramesh Kumar / Delhi Public School Admin"
                  value={subName}
                  onChange={(e) => setSubName(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '8px 12px',
                    borderRadius: 'var(--radius-sm)',
                    border: '1px solid var(--border-light)',
                    background: 'var(--bg-canvas)',
                    fontSize: '12.5px'
                  }}
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '11.5px', fontWeight: 700, color: 'var(--forest-900)', marginBottom: '3px' }}>
                    WHATSAPP / PHONE:
                  </label>
                  <input
                    type="tel"
                    placeholder="+91 98XXXXXXXX"
                    value={subPhone}
                    onChange={(e) => setSubPhone(e.target.value)}
                    style={{
                      width: '100%',
                      padding: '8px 12px',
                      borderRadius: 'var(--radius-sm)',
                      border: '1px solid var(--border-light)',
                      background: 'var(--bg-canvas)',
                      fontSize: '12.5px'
                    }}
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '11.5px', fontWeight: 700, color: 'var(--forest-900)', marginBottom: '3px' }}>
                    EMAIL ADDRESS:
                  </label>
                  <input
                    type="email"
                    placeholder="name@domain.com"
                    value={subEmail}
                    onChange={(e) => setSubEmail(e.target.value)}
                    style={{
                      width: '100%',
                      padding: '8px 12px',
                      borderRadius: 'var(--radius-sm)',
                      border: '1px solid var(--border-light)',
                      background: 'var(--bg-canvas)',
                      fontSize: '12.5px'
                    }}
                  />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '11.5px', fontWeight: 700, color: 'var(--forest-900)', marginBottom: '3px' }}>
                    ROLE:
                  </label>
                  <select
                    value={subRole}
                    onChange={(e) => setSubRole(e.target.value)}
                    style={{
                      width: '100%',
                      padding: '8px 12px',
                      borderRadius: 'var(--radius-sm)',
                      border: '1px solid var(--border-light)',
                      fontSize: '12px',
                      background: 'var(--bg-canvas)'
                    }}
                  >
                    <option value="citizen">Citizen / Resident</option>
                    <option value="school_admin">School Principal / Admin</option>
                    <option value="hospital_admin">Hospital / Medical Officer</option>
                    <option value="rwa_president">RWA Federation</option>
                  </select>
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '11.5px', fontWeight: 700, color: 'var(--forest-900)', marginBottom: '3px' }}>
                    TARGET WARD:
                  </label>
                  <select
                    value={selectedWardId}
                    onChange={(e) => setSelectedWardId(e.target.value)}
                    style={{
                      width: '100%',
                      padding: '8px 12px',
                      borderRadius: 'var(--radius-sm)',
                      border: '1px solid var(--border-light)',
                      fontSize: '12px',
                      background: 'var(--bg-canvas)'
                    }}
                  >
                    {wards.map((w) => (
                      <option key={w.id} value={w.id}>
                        {w.name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '11.5px', fontWeight: 700, color: 'var(--forest-900)', marginBottom: '5px' }}>
                  DISPATCH CHANNELS:
                </label>
                <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                  {[
                    { id: 'push', label: 'Web Push' },
                    { id: 'whatsapp', label: 'WhatsApp' },
                    { id: 'sms', label: 'SMS' },
                    { id: 'email', label: 'Email' }
                  ].map((ch) => (
                    <button
                      key={ch.id}
                      type="button"
                      onClick={() => toggleSubChannel(ch.id)}
                      style={{
                        padding: '5px 11px',
                        borderRadius: 'var(--radius-pill)',
                        fontSize: '11.5px',
                        fontWeight: 700,
                        border: subChannels.includes(ch.id) ? '1px solid #2D6A4F' : '1px solid var(--border-light)',
                        background: subChannels.includes(ch.id) ? '#D8F3DC' : 'var(--bg-canvas)',
                        color: subChannels.includes(ch.id) ? '#1B4332' : 'var(--text-secondary)',
                        cursor: 'pointer'
                      }}
                    >
                      {ch.label}
                    </button>
                  ))}
                </div>
              </div>

              <button
                type="submit"
                disabled={submitting}
                className="air-btn-primary"
                style={{
                  justifyContent: 'center',
                  padding: '11px',
                  marginTop: '4px',
                  fontSize: '13px'
                }}
              >
                <span>{submitting ? 'ENROLLING...' : 'ENROLL FOR HYPER-LOCAL AIR ALERTS'}</span>
              </button>
            </form>
          )}
        </div>

        {/* Right: Interactive Mobile Smartphone Simulator */}
        <div
          style={{
            background: 'linear-gradient(145deg, #081C15 0%, #1B4332 100%)',
            borderRadius: 'var(--radius-xl)',
            padding: '24px 20px',
            boxShadow: 'var(--shadow-xl)',
            border: '2px solid rgba(82, 183, 136, 0.3)',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center'
          }}
        >
          <div style={{ textAlign: 'center', marginBottom: '14px', width: '100%' }}>
            <span
              style={{
                background: 'rgba(255, 255, 255, 0.12)',
                color: '#D8F3DC',
                fontSize: '11px',
                fontWeight: 800,
                padding: '3px 10px',
                borderRadius: '999px',
                border: '1px solid rgba(216, 243, 220, 0.2)'
              }}
            >
              LIVE MOBILE DEVICE SIMULATOR
            </span>
            <h4 style={{ margin: '6px 0 2px 0', fontSize: '15px', fontWeight: 800, color: '#FFFFFF' }}>
              Smartphone Scan-to-Email Experience
            </h4>
            <p style={{ margin: 0, fontSize: '12px', color: '#B7E4C7' }}>
              Simulates a citizen scanning the physical QR code poster on their phone.
            </p>
          </div>

          {/* Smartphone Hardware Frame (Mobile Shaped Black-Coloured Frame for Video Editing Placement) */}
          <div
            id="mobile-phone-overlay-container"
            style={{
              width: '100%',
              maxWidth: '280px',
              height: '500px',
              background: '#0B0F19',
              borderRadius: '34px',
              padding: '10px',
              border: '3.5px solid #334155',
              boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.7), 0 0 0 1px rgba(255,255,255,0.08)',
              position: 'relative',
              display: 'flex',
              flexDirection: 'column',
              boxSizing: 'border-box'
            }}
          >
            {/* Dynamic Island / Top Camera Cutout */}
            <div
              style={{
                position: 'absolute',
                top: '14px',
                left: '50%',
                transform: 'translateX(-50%)',
                width: '74px',
                height: '16px',
                background: '#000000',
                borderRadius: '10px',
                zIndex: 10,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '5px'
              }}
            >
              <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#1E293B' }} />
              <div style={{ width: '3px', height: '3px', borderRadius: '50%', background: '#0F172A' }} />
            </div>

            {/* Pure Black Mobile Screen (#000000) for Video Insertion */}
            <div
              id="mobile-black-screen-placeholder"
              style={{
                flex: 1,
                background: '#000000',
                borderRadius: '24px',
                border: '1px solid #1E293B',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                padding: '16px',
                position: 'relative',
                boxSizing: 'border-box',
                overflow: 'hidden'
              }}
            >
              {/* Placement Alignment Guide inside the Black Screen */}
              <div
                style={{
                  border: '1.5px dashed rgba(74, 222, 128, 0.45)',
                  borderRadius: '16px',
                  width: '100%',
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  textAlign: 'center',
                  padding: '14px',
                  boxSizing: 'border-box',
                  background: 'rgba(0, 0, 0, 0.95)'
                }}
              >
                <div
                  style={{
                    background: 'rgba(74, 222, 128, 0.15)',
                    border: '1px solid rgba(74, 222, 128, 0.4)',
                    borderRadius: '999px',
                    padding: '4px 10px',
                    fontSize: '9.5px',
                    fontWeight: 800,
                    color: '#4ADE80',
                    letterSpacing: '0.5px',
                    marginBottom: '10px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '5px'
                  }}
                >
                  <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#4ADE80' }} />
                  MOBILE VIDEO OVERLAY
                </div>

                <div style={{ fontSize: '13px', fontWeight: 800, color: '#FFFFFF', marginBottom: '4px' }}>
                  Overlay Recorded Mobile Clip
                </div>
                <div style={{ fontSize: '10.5px', color: '#94A3B8', lineHeight: 1.4, marginBottom: '14px' }}>
                  Target Resolution: 9:16 Vertical<br />
                  Registration &amp; Location Trigger
                </div>

                <div
                  style={{
                    background: '#0A1B13',
                    border: '1px solid #1B4332',
                    borderRadius: '8px',
                    padding: '8px 10px',
                    fontSize: '9.5px',
                    fontFamily: 'monospace',
                    color: '#86EFAC',
                    width: '100%',
                    boxSizing: 'border-box'
                  }}
                >
                  http://192.168.1.102:8000/mobile
                </div>
              </div>
            </div>

            {/* Bottom Home Indicator Bar */}
            <div
              style={{
                position: 'absolute',
                bottom: '8px',
                left: '50%',
                transform: 'translateX(-50%)',
                width: '84px',
                height: '4px',
                background: '#475569',
                borderRadius: '4px',
                zIndex: 10
              }}
            />
          </div>

          <button
            onClick={onOpenQRModal}
            className="air-btn-secondary"
            style={{
              marginTop: '14px',
              width: '100%',
              justifyContent: 'center',
              padding: '9px',
              fontSize: '12px',
              background: '#FFFFFF',
              color: '#1B4332'
            }}
          >
            <QrCode size={14} />
            <span>OPEN FULL CAMERA QR CODE</span>
          </button>
        </div>
      </div>
    </div>
  );
};
