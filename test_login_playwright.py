import time
from playwright.sync_api import sync_playwright

def test_login():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            channel="chrome",
            headless=False,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        context.add_init_script("localStorage.setItem('_sys_dt_bypass', 'true');")
        page = context.new_page()
        page.route("**/chunk-4VTC4MLB.js", lambda route: route.abort())
        
        print("Navigating to login page...")
        page.goto("https://omp.aistudy.uz/auth/login")
        
        print("Waiting for #username field...")
        page.wait_for_selector("#username", timeout=15000)
        time.sleep(1)
        
        page.evaluate("document.querySelectorAll('.devtools-overlay, .telegram-popup-overlay').forEach(e => e.remove());")
        
        print("Entering credentials...")
        page.locator("#username").fill("maktabin.f.orm.ati.k1@gmail.com")
        page.locator("#password").fill("Maktab29")
        time.sleep(1)
        
        print("Clicking Tizimga kirish...")
        page.locator("button[type='submit']").click(force=True)
        time.sleep(5)
        
        print("Current URL after submit:", page.url)
        page.screenshot(path="5millionsertifikat/after_login.png")
        print("Saved screenshot to 5millionsertifikat/after_login.png")
        
        # Check localStorage accessToken
        token = page.evaluate("localStorage.getItem('accessToken') || localStorage.getItem('token') || ''")
        print("Storage AccessToken length:", len(token))
        
        time.sleep(5)
        browser.close()

if __name__ == "__main__":
    test_login()
