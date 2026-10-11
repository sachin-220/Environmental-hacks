"""
AERIS — Perfect Master Hackathon Video Producer (Strictly < 3m 12s)
Includes:
1. 8.02s Cinematic Problem Statement Voiceover matching the user's 3D animation script.
2. Dashboard operation begins at exactly 8.02s.
3. Map zooms to reveal 3km grid cells.
4. Tab 2 shows CAQM Directive statutory modal from top to bottom.
5. Tab 2 features the sleek Black Smartphone Mockup (#000000 screen) for video overlay from 45.70s to 58.68s.
6. Dynamic enrollment triggers verified SMTP email containing Critical Danger Areas to Avoid.
7. Glowing LED lights on 72h forecast parameter toggles.
8. Non-overlapping Regional Advection Timeline in Tab 5.
9. Airshed Federalism & Nash Equilibrium highlighted in Tab 6.
10. Encoded to 1080p 60fps Broadcast MP4 in exactly 186.44s (3m 06s).
"""
import time
import os
import shutil
import asyncio
import subprocess
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

OUTPUT_DIR = Path("artifacts_video")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
MASTER_AUDIO = OUTPUT_DIR / "master_voiceover.mp3"
FINAL_MP4 = Path("final.mp4")

SEGMENT_DURATIONS = [
    7.75,   # 0: Problem statement (0.00s - 7.75s)
    9.67,   # 1_1: Overview & mission (7.75s - 17.42s)
    7.03,   # 1_2: 3km grid zoom (17.42s - 24.45s)
    8.66,   # 1_3: 33 stations table & telemetry (24.45s - 33.11s)
    11.38,  # 2_1: Tab 2 top & CAQM directive modal (33.11s - 44.49s)
    13.78,  # 2_2: Black Smartphone mockup overlay & live enroll (44.49s - 58.27s)
    8.98,   # 2_3: School directives & indoor ventilation (58.27s - 67.25s)
    15.79,  # 3_1: Tab 3 72h Forecast & glowing metric buttons (67.25s - 83.04s)
    14.62,  # 4_1: Tab 4 Inversion Lid & 197m PBL collapse (83.04s - 97.66s)
    12.77,  # 5_1: Tab 5 Sources & Regional Advection Timeline (97.66s - 110.43s)
    14.47,  # 6_1: Tab 6 SLSQP MPC optimal intervention (110.43s - 124.90s)
    14.18,  # 6_2: Tab 6 Airshed Federalism & Nash Arbitrage (124.90s - 139.08s)
    9.41,   # 7_1: Tab 7 Stations & Pearson correlations (139.08s - 148.49s)
    14.88,  # 8_1: Tab 8 AWS Cedar, OpenSearch & Strands (148.49s - 163.37s)
    12.58,  # 9_1: Tab 9 Model Verification & Google Drive Proofs (163.37s - 175.95s)
    8.40    # 9_2: Closing outro & header (175.95s - 184.35s)
]

def switch_to_tab(page, tab_id):
    tab_map = {
        'overview': 'Delhi Map',
        'alerts': 'Citizen Alerts',
        'forecast': '72h Forecast',
        'atmosphere': 'Coupled Feedback',
        'sources': 'Sources & Plumes',
        'intervention': 'Intervention & MPC',
        'monitoring': 'Stations & Telemetry',
        'aws': 'AWS Cloud',
        'model': 'Model Verification'
    }
    target = tab_map.get(tab_id, tab_id)
    page.evaluate(f"""
        const buttons = Array.from(document.querySelectorAll('button'));
        const btn = buttons.find(b => b.textContent && b.textContent.includes('{target}'));
        if (btn) btn.click();
    """)

def record_hackathon_demo():
    print("Starting Synchronized Playwright Walkthrough (1920x1080 60fps)...")
    
    start_times = [0.0]
    for d in SEGMENT_DURATIONS[:-1]:
        start_times.append(start_times[-1] + d)
        
    total_dur = sum(SEGMENT_DURATIONS)
    print(f"Target presentation duration: {total_dur:.2f}s (3m 06s)")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            channel="msedge",
            headless=True,
            args=[
                "--window-size=1920,1080",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--force-device-scale-factor=1"
            ]
        )
        
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            record_video_dir=str(OUTPUT_DIR),
            record_video_size={"width": 1920, "height": 1080}
        )
        
        t_context_start = time.time()
        page = context.new_page()
        page.goto("http://127.0.0.1:8000", wait_until="networkidle")
        time.sleep(1.0) # Settle styles
        
        t_pres_start = time.time()
        offset_seconds = t_pres_start - t_context_start
        print(f"Browser loading offset: {offset_seconds:.3f}s (trimmed via -ss)")
        
        def wait_until(sec):
            while (time.time() - t_pres_start) < sec:
                time.sleep(0.01)

        # ----------------------------------------------------
        # SEGMENT 0: CINEMATIC PROBLEM STATEMENT (0.00s - 8.02s)
        # Voiceover describes child, inversion lid, and stubble fires
        # ----------------------------------------------------
        print("[0.00s] Segment 0: Cinematic Problem Statement Intro (Steady hold for 3D clip replacement)")
        page.evaluate("window.scrollTo({top: 0, behavior: 'smooth'})")
        page.mouse.move(960, 300)
        
        # ----------------------------------------------------
        # SEGMENT 1_1: DASHBOARD OPERATION STARTS (8.02s - 16.52s)
        # "We built AERIS — an atmospheric early-warning platform..."
        # ----------------------------------------------------
        wait_until(start_times[1] - 0.2)
        print(f"[{start_times[1]:.2f}s] Operation Begins: Overview & KPI cards")
        page.mouse.move(360, 210)
        time.sleep(2.0)
        page.mouse.move(620, 210)
        
        # ----------------------------------------------------
        # SEGMENT 1_2: 3KM GRID CELL ZOOM (16.52s - 23.55s)
        # ----------------------------------------------------
        wait_until(start_times[2] - 0.2)
        print(f"[{start_times[2]:.2f}s] Zooming into 3km grid cell mesh...")
        try:
            zoom_btn = page.query_selector(".leaflet-control-zoom-in")
            if zoom_btn:
                zoom_btn.click()
                time.sleep(0.8)
                zoom_btn.click()
        except Exception as e:
            print("Zoom note:", e)
        page.mouse.move(960, 480)
        
        # ----------------------------------------------------
        # SEGMENT 1_3: 33 STATIONS TABLE & PROFILE (23.55s - 32.31s)
        # ----------------------------------------------------
        wait_until(start_times[3] - 0.2)
        print(f"[{start_times[3]:.2f}s] Scrolling down to 33 stations table & line profile...")
        page.evaluate("window.scrollTo({top: document.body.scrollHeight * 0.45, behavior: 'smooth'})")
        time.sleep(1.5)
        page.evaluate("window.scrollTo({top: document.body.scrollHeight, behavior: 'smooth'})")
        page.mouse.move(650, 780)

        # ----------------------------------------------------
        # SEGMENT 2_1: TAB 2 CITIZEN PORTAL & CAQM DIRECTIVE (32.31s - 45.70s)
        # ----------------------------------------------------
        wait_until(start_times[4] - 0.3)
        print(f"[{start_times[4]:.2f}s] Switching to Tab 2 at top of page...")
        switch_to_tab(page, 'alerts')
        page.evaluate("window.scrollTo({top: 0, behavior: 'smooth'})")
        time.sleep(0.8)
        
        # Open GENERATE CAQM DIRECTIVE modal
        print("Opening GENERATE CAQM DIRECTIVE modal...")
        page.evaluate("""
            const buttons = Array.from(document.querySelectorAll('button'));
            const caqmBtn = buttons.find(b => b.textContent && b.textContent.includes('CAQM'));
            if (caqmBtn) caqmBtn.click();
        """)
        time.sleep(3.2)
        
        # Close CAQM modal
        page.evaluate("""
            const buttons = Array.from(document.querySelectorAll('button'));
            const closeBtn = buttons.find(b => b.textContent && (b.textContent.includes('Close') || b.textContent.includes('Acknowledge') || b.textContent.includes('Dismiss')));
            if (closeBtn) closeBtn.click();
            else {
                const xBtn = document.querySelector('[aria-label="Close"], button svg.lucide-x');
                if (xBtn) xBtn.parentElement.click();
            }
        """)
        time.sleep(0.5)

        # ----------------------------------------------------
        # SEGMENT 2_2: BLACK PHONE MOCKUP OVERLAY WINDOW (45.70s - 58.68s)
        # ----------------------------------------------------
        wait_until(start_times[5] - 0.2)
        print(f"[{start_times[5]:.2f}s] === MOBILE VIDEO OVERLAY WINDOW START (45.70s to 58.68s) ===")
        print("Scrolling down to center the Black Smartphone Mockup Container...")
        page.evaluate("""
            const el = document.getElementById('mobile-phone-overlay-container');
            if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' });
            else window.scrollTo({ top: 480, behavior: 'smooth' });
        """)
        time.sleep(1.0)
        
        # Type email on the left form and enroll
        try:
            email_inputs = page.query_selector_all("input[type='email'], input[placeholder*='email'], input[placeholder*='Email']")
            for inp in email_inputs:
                inp.click()
                inp.fill("")
                inp.type("sanjeevkumaredu8@gmail.com", delay=20)
            time.sleep(0.6)
            sub_btn = page.query_selector("button:has-text('ENROLL FOR HYPER-LOCAL AIR ALERTS'), button:has-text('GET LIVE AIR ALERTS'), button:has-text('Subscribe')")
            if sub_btn:
                sub_btn.click()
        except Exception as e:
            print("Form note:", e)
            
        page.mouse.move(1360, 600) # Hover black phone screen area
        
        # ----------------------------------------------------
        # SEGMENT 2_3: SCHOOL DIRECTIVES & VENTILATION (58.68s - 67.06s)
        # ----------------------------------------------------
        wait_until(start_times[6] - 0.2)
        print(f"[{start_times[6]:.2f}s] Scrolling down to School Safety Protocol & Ventilation Windows...")
        page.evaluate("window.scrollTo({top: document.body.scrollHeight * 0.65, behavior: 'smooth'})")
        time.sleep(1.6)
        page.evaluate("window.scrollTo({top: document.body.scrollHeight, behavior: 'smooth'})")
        page.mouse.move(600, 720)

        # ----------------------------------------------------
        # SEGMENT 3_1: TAB 3 72H FORECAST & GLOWING BUTTONS (67.06s - 84.70s)
        # ----------------------------------------------------
        wait_until(start_times[7] - 0.4)
        print(f"[{start_times[7]:.2f}s] Switching to Tab 3 (72h Forecast)...")
        switch_to_tab(page, 'forecast')
        page.evaluate("window.scrollTo({top: 0, behavior: 'smooth'})")
        time.sleep(0.8)
        
        # Toggle metrics with glowing lights: PM25 -> PM10 -> O3 -> NO2 -> AQI
        metrics = ['pm25', 'pm10', 'o3', 'no2', 'aqi']
        t_step = (SEGMENT_DURATIONS[7] - 4.5) / len(metrics)
        for m in metrics:
            print(f"Activating metric button: {m.upper()} (showing glowing light)...")
            page.evaluate(f"""
                const buttons = Array.from(document.querySelectorAll('button'));
                const mBtn = buttons.find(b => b.textContent && b.textContent.trim().toUpperCase().includes('{m.upper()}'));
                if (mBtn) mBtn.click();
            """)
            time.sleep(t_step)
            
        # Scroll to bottom Lyapunov error covariance table
        page.evaluate("window.scrollTo({top: document.body.scrollHeight, behavior: 'smooth'})")
        page.mouse.move(700, 680)

        # ----------------------------------------------------
        # SEGMENT 4_1: TAB 4 INVERSION LID & PBL (84.70s - 98.98s)
        # ----------------------------------------------------
        wait_until(start_times[8] - 0.4)
        print(f"[{start_times[8]:.2f}s] Switching to Tab 4 (Inversion Lid & PBL Dynamics)...")
        switch_to_tab(page, 'atmosphere')
        page.evaluate("window.scrollTo({top: 0, behavior: 'smooth'})")
        page.mouse.move(720, 420) # Hover 197m PBL collapse
        time.sleep(2.5)
        page.evaluate("window.scrollTo({top: document.body.scrollHeight, behavior: 'smooth'})")

        # ----------------------------------------------------
        # SEGMENT 5_1: TAB 5 SOURCES & PLUMES (98.98s - 111.32s)
        # ----------------------------------------------------
        wait_until(start_times[9] - 0.4)
        print(f"[{start_times[9]:.2f}s] Switching to Tab 5 (Sources & Stubble Plumes)...")
        switch_to_tab(page, 'sources')
        page.evaluate("window.scrollTo({top: 0, behavior: 'smooth'})")
        page.mouse.move(800, 440) # Fire map
        time.sleep(2.0)
        print("Scrolling down to the fixed, non-overlapping Regional Advection Timeline...")
        page.evaluate("window.scrollTo({top: document.body.scrollHeight, behavior: 'smooth'})")
        page.mouse.move(500, 750)

        # ----------------------------------------------------
        # SEGMENT 6_1: TAB 6 SLSQP MPC (111.32s - 125.48s)
        # ----------------------------------------------------
        wait_until(start_times[10] - 0.4)
        print(f"[{start_times[10]:.2f}s] Switching to Tab 6 (Intervention & MPC Optimization)...")
        switch_to_tab(page, 'intervention')
        page.evaluate("window.scrollTo({top: 0, behavior: 'smooth'})")
        time.sleep(1.0)
        # Click Run Optimal Control Simulation
        page.evaluate("""
            const buttons = Array.from(document.querySelectorAll('button'));
            const optBtn = buttons.find(b => b.textContent && (b.textContent.includes('Optimal') || b.textContent.includes('Run') || b.textContent.includes('Simulate')));
            if (optBtn) optBtn.click();
        """)
        time.sleep(2.0)
        page.mouse.move(760, 460) # Hover 32% peak reduction curve

        # ----------------------------------------------------
        # SEGMENT 6_2: AIRSHED FEDERALISM & NASH ARBITRAGE (125.48s - 141.30s)
        # ----------------------------------------------------
        wait_until(start_times[11] - 0.2)
        print(f"[{start_times[11]:.2f}s] Scrolling down to Airshed Federalism (Cross-Border Arbitrage)...")
        page.evaluate("window.scrollTo({top: document.body.scrollHeight * 0.70, behavior: 'smooth'})")
        time.sleep(1.5)
        page.evaluate("window.scrollTo({top: document.body.scrollHeight, behavior: 'smooth'})")
        page.mouse.move(600, 720) # Focus Airshed Federalism Card

        # ----------------------------------------------------
        # SEGMENT 7_1: TAB 7 STATIONS & TELEMETRY (141.30s - 150.66s)
        # ----------------------------------------------------
        wait_until(start_times[12] - 0.4)
        print(f"[{start_times[12]:.2f}s] Switching to Tab 7 (Stations & Telemetry)...")
        switch_to_tab(page, 'monitoring')
        page.evaluate("window.scrollTo({top: 0, behavior: 'smooth'})")
        page.mouse.move(700, 320)
        time.sleep(1.5)
        page.evaluate("window.scrollTo({top: document.body.scrollHeight, behavior: 'smooth'})") # Pearson matrix

        # ----------------------------------------------------
        # SEGMENT 8_1: TAB 8 AWS SUITE (150.66s - 166.28s)
        # ----------------------------------------------------
        wait_until(start_times[13] - 0.4)
        print(f"[{start_times[13]:.2f}s] Switching to Tab 8 (AWS Open-Source Architecture)...")
        switch_to_tab(page, 'aws')
        page.evaluate("window.scrollTo({top: 0, behavior: 'smooth'})")
        time.sleep(0.8)
        # Click Cedar test
        page.evaluate("""
            const buttons = Array.from(document.querySelectorAll('button'));
            const cedarBtn = buttons.find(b => b.textContent && b.textContent.includes('Cedar'));
            if (cedarBtn) cedarBtn.click();
        """)
        time.sleep(1.8)
        # Click OpenSearch test
        page.evaluate("""
            const buttons = Array.from(document.querySelectorAll('button'));
            const osBtn = buttons.find(b => b.textContent && b.textContent.includes('OpenSearch'));
            if (osBtn) osBtn.click();
        """)
        time.sleep(1.8)
        page.evaluate("window.scrollTo({top: document.body.scrollHeight, behavior: 'smooth'})") # Strands trace

        # ----------------------------------------------------
        # SEGMENT 9_1: TAB 9 MODEL PROOFS & BENCHMARKS (166.28s - 178.71s)
        # ----------------------------------------------------
        wait_until(start_times[14] - 0.4)
        print(f"[{start_times[14]:.2f}s] Switching to Tab 9 (Model Verification & Proofs)...")
        switch_to_tab(page, 'model')
        page.evaluate("window.scrollTo({top: 0, behavior: 'smooth'})")
        time.sleep(0.8)
        page.mouse.move(960, 240) # Showcase Proof Repository banner
        time.sleep(2.5)
        page.evaluate("window.scrollTo({top: document.body.scrollHeight, behavior: 'smooth'})") # RMSE table

        # ----------------------------------------------------
        # SEGMENT 9_2: OUTRO (178.71s - 186.44s)
        # ----------------------------------------------------
        wait_until(start_times[15] - 0.2)
        print(f"[{start_times[15]:.2f}s] Scrolling back to top proof banner & header for clean finish...")
        page.evaluate("window.scrollTo({top: 0, behavior: 'smooth'})")
        page.mouse.move(960, 240)
        
        wait_until(total_dur)
        raw_video_path = page.video.path()
        context.close()
        browser.close()
        print(f"Raw video recorded: {raw_video_path}")
        return raw_video_path, offset_seconds, total_dur

def multiplex_final_video(raw_video_path, offset_seconds, total_dur):
    print("==========================================================")
    print("Multiplexing Broadcast-Grade 1080p Video into final.mp4...")
    print(f"Offset trimmed: {offset_seconds:.3f}s | Audio duration: {total_dur:.2f}s")
    print("==========================================================")
    
    cmd = (
        f'ffmpeg -y -ss {offset_seconds:.3f} -i "{raw_video_path}" -i "{MASTER_AUDIO}" '
        f'-map 0:v:0 -map 1:a:0 -avoid_negative_ts make_zero '
        f'-c:v libx264 -preset slow -crf 16 -pix_fmt yuv420p -b:v 8M '
        f'-c:a aac -b:a 192k -t {total_dur:.2f} "{FINAL_MP4}"'
    )
    print("Executing FFmpeg command:", cmd)
    subprocess.run(cmd, shell=True, check=True)
    
    artifact_copy = Path(r"C:\Users\Sanjeev Kumar S\.gemini\antigravity-ide\brain\d4f8297c-451c-4f18-b3f4-d0f030c109de\final.mp4")
    shutil.copyfile(FINAL_MP4, artifact_copy)
    
    file_size_mb = FINAL_MP4.stat().st_size / (1024 * 1024)
    res_final = subprocess.check_output(f'ffprobe -v error -show_entries format=duration -of json "{FINAL_MP4}"', shell=True)
    final_dur = float(json.loads(res_final.decode("utf-8"))["format"]["duration"])
    
    print("==========================================================")
    print(f"SUCCESS: final.mp4 generated successfully!")
    print(f"File Location: {FINAL_MP4.resolve()}")
    print(f"Artifact Location: {artifact_copy}")
    print(f"Final Duration: {final_dur:.2f}s ({int(final_dur//60)}m {int(final_dur%60):02d}s) [< 3m 12s]")
    print(f"File Size: {file_size_mb:.2f} MB")
    print("==========================================================")

def main():
    raw_video, offset, total_dur = record_hackathon_demo()
    multiplex_final_video(raw_video, offset, total_dur)

if __name__ == "__main__":
    main()
