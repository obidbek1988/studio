import time
from playwright.sync_api import sync_playwright

def test_page():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox"
            ]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800}
        )
        page = context.new_page()
        print("Navigating...")
        page.goto("https://omp.aistudy.uz/auth/register", wait_until="domcontentloaded")
        time.sleep(3)
        
        # Remove any overlays or popup dialogs
        page.evaluate("""
            document.querySelectorAll('.devtools-overlay, .telegram-popup-overlay, .p-dialog-mask').forEach(e => e.remove());
        """)
        print("Overlays removed!")
        
        # Click Metrika tab with force=True
        btn = page.locator("button:has-text('Metrika')")
        if btn.count() > 0:
            btn.click(force=True)
            print("Metrika tab clicked with force=True!")
        else:
            print("Metrika button not found!")
            
        time.sleep(2)
        page.screenshot(path="5millionsertifikat/screen_metrika.png")
        print("Screenshot saved to 5millionsertifikat/screen_metrika.png")
        
        # Look for recaptcha
        frames = page.frames
        print(f"Total frames: {len(frames)}")
        anchor_frame = None
        for f in frames:
            if "recaptcha" in f.url and "anchor" in f.url:
                anchor_frame = f
                print("Found anchor frame:", f.url[:80])
                break
                
        if anchor_frame:
            print("Clicking reCAPTCHA checkbox...")
            checkbox = anchor_frame.locator("#recaptcha-anchor")
            checkbox.click(force=True)
            print("Checkbox clicked!")
            time.sleep(5)
            
            aria_checked = checkbox.get_attribute("aria-checked")
            print("Checkbox aria-checked status:", aria_checked)
            
            page.screenshot(path="5millionsertifikat/screen_captcha_clicked.png")
            print("Saved captcha clicked screenshot!")

            # Check if bframe (challenge) appeared
            bframe = None
            for f in page.frames:
                if "recaptcha" in f.url and "bframe" in f.url:
                    bframe = f
                    print("Found bframe (challenge) frame!")
                    break
            
            if bframe:
                audio_btn = bframe.locator("#recaptcha-audio-button")
                print("Audio challenge button count:", audio_btn.count())

        browser.close()

if __name__ == "__main__":
    test_page()
