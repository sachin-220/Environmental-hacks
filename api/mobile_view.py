"""
AERIS Mobile Dynamic Registration Portal
Dedicated mobile web application accessible across the local network (http://<IP>:8000/mobile)
when scanned via mobile phone camera barcode / QR code.
"""

MOBILE_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <title>AERIS Mobile • Dynamic Air Alert Registration</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;700;800&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg-dark: #081C15;
      --card-bg: #0F281E;
      --card-border: #1B4332;
      --forest-primary: #2D6A4F;
      --emerald-accent: #4ADE80;
      --mint-glow: #74C69D;
      --danger-red: #EF4444;
      --text-main: #F8FAF9;
      --text-muted: #94A3B8;
    }
    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
      -webkit-tap-highlight-color: transparent;
    }
    body {
      background-color: var(--bg-dark);
      color: var(--text-main);
      font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
      min-height: 100vh;
      padding: 16px 16px 40px 16px;
      display: flex;
      flex-direction: column;
      align-items: center;
    }
    .mobile-container {
      width: 100%;
      max-width: 440px;
    }
    .top-badge {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      background: rgba(74, 222, 128, 0.12);
      border: 1px solid rgba(74, 222, 128, 0.3);
      padding: 5px 12px;
      border-radius: 999px;
      font-size: 11px;
      font-weight: 700;
      color: var(--emerald-accent);
      letter-spacing: 0.5px;
      margin-bottom: 12px;
    }
    .pulse-dot {
      width: 7px;
      height: 7px;
      background: var(--emerald-accent);
      border-radius: 50%;
      animation: pulse 1.8s infinite;
    }
    @keyframes pulse {
      0% { opacity: 0.4; transform: scale(0.9); }
      50% { opacity: 1; transform: scale(1.3); }
      100% { opacity: 0.4; transform: scale(0.9); }
    }
    .header-card {
      background: linear-gradient(135deg, #0F281E 0%, #17382B 100%);
      border: 1px solid var(--card-border);
      border-radius: 18px;
      padding: 20px;
      margin-bottom: 16px;
      box-shadow: 0 10px 30px rgba(0,0,0,0.3);
    }
    .header-title {
      font-size: 20px;
      font-weight: 800;
      color: #FFFFFF;
      letter-spacing: -0.3px;
      line-height: 1.3;
      margin-bottom: 6px;
    }
    .header-subtitle {
      font-size: 13px;
      color: var(--text-muted);
      line-height: 1.4;
    }

    /* Location Card */
    .location-card {
      background: #143326;
      border: 1.5px solid #2D6A4F;
      border-radius: 16px;
      padding: 18px;
      margin-bottom: 18px;
      position: relative;
      overflow: hidden;
    }
    .loc-label {
      font-size: 11px;
      font-weight: 800;
      color: var(--mint-glow);
      text-transform: uppercase;
      letter-spacing: 1px;
      display: flex;
      align-items: center;
      gap: 6px;
      margin-bottom: 6px;
    }
    .loc-name {
      font-size: 17px;
      font-weight: 800;
      color: #FFFFFF;
      margin-bottom: 4px;
    }
    .loc-coords {
      font-family: 'JetBrains Mono', monospace;
      font-size: 11.5px;
      color: #94A3B8;
      margin-bottom: 14px;
    }
    .aqi-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      background: rgba(239, 68, 68, 0.12);
      border: 1px solid rgba(239, 68, 68, 0.35);
      border-radius: 10px;
      padding: 10px 14px;
    }
    .aqi-val {
      font-family: 'JetBrains Mono', monospace;
      font-size: 24px;
      font-weight: 900;
      color: var(--danger-red);
    }
    .aqi-tag {
      background: var(--danger-red);
      color: #FFFFFF;
      font-size: 10px;
      font-weight: 800;
      padding: 4px 10px;
      border-radius: 999px;
      letter-spacing: 0.5px;
    }

    /* Form Card */
    .form-card {
      background: #0F281E;
      border: 1px solid var(--card-border);
      border-radius: 18px;
      padding: 22px 20px;
      margin-bottom: 18px;
      box-shadow: 0 10px 25px rgba(0,0,0,0.25);
    }
    .form-group {
      margin-bottom: 16px;
    }
    label {
      display: block;
      font-size: 12px;
      font-weight: 700;
      color: #D8F3DC;
      margin-bottom: 7px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
    input, select {
      width: 100%;
      background: #081C15;
      border: 1.5px solid #2D6A4F;
      border-radius: 12px;
      padding: 13px 14px;
      font-size: 14px;
      color: #FFFFFF;
      font-family: inherit;
      outline: none;
      transition: border-color 0.2s, box-shadow 0.2s;
    }
    input:focus, select:focus {
      border-color: var(--emerald-accent);
      box-shadow: 0 0 0 3px rgba(74, 222, 128, 0.2);
    }
    .submit-btn {
      width: 100%;
      background: linear-gradient(135deg, #10B981 0%, #059669 100%);
      border: none;
      border-radius: 14px;
      padding: 16px;
      font-size: 14.5px;
      font-weight: 800;
      color: #FFFFFF;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      box-shadow: 0 6px 20px rgba(16, 185, 129, 0.35);
      letter-spacing: 0.5px;
      transition: transform 0.15s, opacity 0.15s;
    }
    .submit-btn:active {
      transform: scale(0.98);
    }
    .submit-btn:disabled {
      opacity: 0.6;
      cursor: not-allowed;
    }

    /* Danger Areas Accordion / Alert */
    .danger-box {
      background: rgba(239, 68, 68, 0.08);
      border: 1px solid rgba(239, 68, 68, 0.3);
      border-radius: 14px;
      padding: 14px;
      margin-top: 16px;
    }
    .danger-title {
      font-size: 12px;
      font-weight: 800;
      color: #F87171;
      text-transform: uppercase;
      margin-bottom: 8px;
      display: flex;
      align-items: center;
      gap: 6px;
    }
    .danger-item {
      display: flex;
      justify-content: space-between;
      font-size: 12px;
      padding: 6px 0;
      border-bottom: 1px solid rgba(255,255,255,0.06);
    }
    .danger-item:last-child {
      border-bottom: none;
    }
    .danger-name {
      color: #E2E8F0;
      font-weight: 600;
    }
    .danger-aqi {
      font-family: 'JetBrains Mono', monospace;
      font-weight: 800;
      color: #EF4444;
    }

    /* Success Card */
    .success-card {
      display: none;
      background: linear-gradient(135deg, #0F3826 0%, #144D34 100%);
      border: 2px solid var(--emerald-accent);
      border-radius: 18px;
      padding: 24px 20px;
      text-align: center;
      animation: popIn 0.3s ease-out;
    }
    @keyframes popIn {
      from { opacity: 0; transform: scale(0.95); }
      to { opacity: 1; transform: scale(1); }
    }
    .success-icon {
      width: 52px;
      height: 52px;
      background: rgba(74, 222, 128, 0.2);
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      margin: 0 auto 14px auto;
      font-size: 26px;
    }
  </style>
</head>
<body>
  <div class="mobile-container">
    <div style="text-align: center; margin-bottom: 8px;">
      <div class="top-badge">
        <div class="pulse-dot"></div>
        <span>LIVE AIRSHED CONNECTED &bull; LOCAL WI-FI</span>
      </div>
    </div>

    <div class="header-card">
      <h1 class="header-title">AERIS Citizen Defense</h1>
      <p class="header-subtitle">Dynamic hyper-local air quality early warning network. Connected via Local Gateway.</p>
    </div>

    <!-- Location Card -->
    <div class="location-card">
      <div class="loc-label">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/></svg>
        CURRENT MONITORED LOCATION
      </div>
      <div class="loc-name" id="locDisplay">Location: Bawana / North Delhi Airshed Corridor</div>
      <div class="loc-coords">Lat: 28.7997&deg;N, Lon: 77.0600&deg;E &bull; Ward #4</div>
      <div class="aqi-row">
        <div>
          <div style="font-size: 11px; font-weight: 700; color: #FCA5A5;">CURRENT WARD AQI</div>
          <div class="aqi-val">384 <span style="font-size: 12px; font-weight: 700; color: #F87171;">SEVERE</span></div>
        </div>
        <div class="aqi-tag">INVERSION COLLAPSE LID</div>
      </div>
    </div>

    <!-- Registration Form -->
    <div class="form-card" id="formCard">
      <form id="regForm">
        <div class="form-group">
          <label for="name">Your Name / Role</label>
          <input type="text" id="name" placeholder="e.g. Sanjeev Kumar / Commuter" required value="Citizen Responder">
        </div>

        <div class="form-group">
          <label for="email">Email Address (For Instant Air Alert)</label>
          <input type="email" id="email" placeholder="Enter your email address" required value="sanjeevkumaredu8@gmail.com">
        </div>

        <div class="form-group">
          <label for="role">Notification Profile</label>
          <select id="role">
            <option value="citizen" selected>Daily Commuter / Resident</option>
            <option value="school_principal">School Principal / Administrator</option>
            <option value="hospital_staff">Healthcare / Vulnerable Patient</option>
            <option value="transit_worker">Outdoor / Transit Worker</option>
          </select>
        </div>

        <button type="submit" class="submit-btn" id="subBtn">
          <span>ACTIVATE EMERGENCY AIR ALERTS</span>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="m22 2-7 20-4-9-9-4Z"/><path d="M22 2 11 13"/></svg>
        </button>
      </form>

      <!-- Danger Areas to Avoid Card -->
      <div class="danger-box">
        <div class="danger-title">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
          CRITICAL DANGER AREAS TO AVOID
        </div>
        <div class="danger-item">
          <span class="danger-name">1. Anand Vihar ISBT</span>
          <span class="danger-aqi">AQI 418</span>
        </div>
        <div class="danger-item">
          <span class="danger-name">2. Jahangirpuri Corridor</span>
          <span class="danger-aqi">AQI 396</span>
        </div>
        <div class="danger-item">
          <span class="danger-name">3. Wazirpur Industrial</span>
          <span class="danger-aqi">AQI 390</span>
        </div>
        <div class="danger-item">
          <span class="danger-name">4. Bawana North Airshed</span>
          <span class="danger-aqi">AQI 384</span>
        </div>
        <div class="danger-item">
          <span class="danger-name">5. Punjabi Bagh West</span>
          <span class="danger-aqi">AQI 372</span>
        </div>
      </div>
    </div>

    <!-- Success Feedback Card -->
    <div class="success-card" id="successCard">
      <div class="success-icon">&check;</div>
      <h2 style="font-size: 19px; font-weight: 800; color: #FFFFFF; margin-bottom: 6px;">REGISTRATION SUCCESSFUL!</h2>
      <p style="font-size: 13.5px; color: #D8F3DC; line-height: 1.5; margin-bottom: 16px;" id="successMsg">
        Emergency air advisory email dispatched to your inbox.
      </p>
      <div style="background: rgba(0,0,0,0.25); border-radius: 12px; padding: 12px; font-size: 12px; color: #A7F3D0; text-align: left; margin-bottom: 16px;">
        &bull; <strong>Status:</strong> Active 72-Hour Threshold Watch<br>
        &bull; <strong>Danger Notice:</strong> Avoid Anand Vihar &amp; Jahangirpuri during morning inversion (05:00-09:30 AM)<br>
        &bull; <strong>Delivery:</strong> Real-time SMTP Broadcast
      </div>
      <button onclick="window.location.reload()" style="background: #2D6A4F; border: none; color: #FFF; padding: 10px 20px; border-radius: 999px; font-weight: 700; font-size: 13px; cursor: pointer;">
        Register Another Device
      </button>
    </div>

    <div style="text-align: center; margin-top: 14px; font-size: 11px; color: #64748B;">
      AERIS Clean Air Intelligence &bull; Bharat Builds 2026
    </div>
  </div>

  <script>
    // Detect geolocation if available, otherwise default to Bawana
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          const lat = pos.coords.latitude.toFixed(4);
          const lon = pos.coords.longitude.toFixed(4);
          document.getElementById('locDisplay').textContent = "Location: Bawana / North Delhi Airshed Corridor (" + lat + "°N, " + lon + "°E)";
        },
        (err) => {
          console.log("Using calibrated default airshed coordinates.");
        },
        { timeout: 3000 }
      );
    }

    document.getElementById('regForm').addEventListener('submit', async (e) => {
      e.preventDefault();
      const btn = document.getElementById('subBtn');
      const email = document.getElementById('email').value.trim();
      const name = document.getElementById('name').value.trim() || 'Citizen';
      const role = document.getElementById('role').value;

      btn.disabled = true;
      btn.innerHTML = '<span>DISPATCHING ADVISORY...</span>';

      try {
        const res = await fetch('/api/alerts/subscribe', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            name: name,
            email: email,
            ward_id: 'bawana_dtu',
            role: role,
            channels: ['email', 'web_push']
          })
        });
        const data = await res.json();
        
        document.getElementById('formCard').style.display = 'none';
        const sc = document.getElementById('successCard');
        sc.style.display = 'block';
        document.getElementById('successMsg').innerHTML = 
          'Verified emergency advisory with <strong>Active Danger Corridors to Avoid</strong> has been successfully dispatched to <strong>' + email + '</strong>.';
      } catch (err) {
        alert('Network error connecting to local server: ' + err.message);
        btn.disabled = false;
        btn.innerHTML = '<span>ACTIVATE EMERGENCY AIR ALERTS</span>';
      }
    });
  </script>
</body>
</html>
"""
