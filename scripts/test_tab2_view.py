from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=True)
    page = browser.new_page(viewport={"width": 1920, "height": 1080})
    page.goto("http://127.0.0.1:8000")
    page.wait_for_load_state("networkidle")
    
    # Click alerts tab
    page.evaluate("""
        const buttons = Array.from(document.querySelectorAll('button'));
        const btn = buttons.find(b => b.textContent && b.textContent.includes('Citizen Alerts'));
        if (btn) btn.click();
    """)
    page.wait_for_timeout(1000)
    
    # Scroll to mobile phone container
    el = page.query_selector('#mobile-phone-overlay-container')
    if el:
        el.scroll_into_view_if_needed()
        page.wait_for_timeout(500)
        box = el.bounding_box()
        print('Mockup bounding box:', box)
        
    page.screenshot(path="artifacts_video/test_tab2_mockup.png")
    browser.close()
    print("Screenshot saved to artifacts_video/test_tab2_mockup.png")
