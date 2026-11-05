import time
import os
from playwright.sync_api import sync_playwright

student = {
    "name": "RAXMONOVA ZULAYHO ILHOMJON QIZI",
    "birthdate": "09092014",
    "seria": "I-FR",
    "number": "806159",
    "sinf": "5-A"
}

from run_visual_test import handle_recaptcha

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=False, slow_mo=100)
    page = browser.new_page()
    page.set_viewport_size({"width": 1280, "height": 800})
    
    # Anti-debug bypass
    page.add_init_script("window._sys_dt_bypass = true;")
    page.route("**/chunk-4VTC4MLB.js", lambda route: route.abort())
    
    print("Navigating to register...")
    page.goto("https://omp.aistudy.uz/auth/register?debug_bypass=omp-dev-master-99", wait_until="domcontentloaded")
    time.sleep(3)
    page.evaluate("document.querySelectorAll('.devtools-overlay, .telegram-popup-overlay, .p-dialog-mask').forEach(e => e.remove());")
    
    # Metrika tanlash
    print("Selecting Metrika...")
    for _ in range(5):
        metrika_btn = page.locator("button:has-text('Metrika')")
        if metrika_btn.count() > 0:
            metrika_btn.click(force=True)
            time.sleep(1)
            if page.locator("input#seria, input[formcontrolname='seria']").count() > 0:
                print("Metrika selected!")
                break
        time.sleep(1)
        
    page.locator("input#seria, input[formcontrolname='seria']").fill(student["seria"])
    page.locator("input#number, input[formcontrolname='number']").fill(student["number"])
    
    birth_input = page.locator("input[formcontrolname='birthdate'], input.p-inputtext").first
    birth_input.click()
    birth_input.fill("")
    birth_input.press_sequentially(student["birthdate"], delay=100)
    birth_input.press("Enter")
    birth_input.press("Tab")
    time.sleep(1)
    
    print("Solving reCAPTCHA...")
    handle_recaptcha(page)
    time.sleep(2)
    
    print("Clicking Yuborish...")
    page.evaluate("""() => {
        const btn = document.querySelector('button[type="submit"]') || Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Yuborish'));
        if (btn) {
            btn.removeAttribute('disabled');
            btn.click();
        }
    }""")
    
    print("Waiting to see result for 10 seconds...")
    for sec in range(1, 11):
        time.sleep(1)
        content = page.content()
        u_count = page.locator("input[formcontrolname='username'], input#username").count()
        if "allaqachon" in content.lower():
            print(f"[{sec}s] RESULT: Allaqachon ro'yxatdan o'tgan!")
            break
        elif u_count > 0:
            print(f"[{sec}s] RESULT: Yangi o'quvchi! Step 2 ochildi (username field visible)!")
            break
        else:
            print(f"[{sec}s] Kutilmoqda... (content length: {len(content)})")
            
    # Screenshot olib qo'yamiz tekshirish uchun
    page.screenshot(path="d:/uzbekcodersbot/5millionsertifikat/reg_check.png")
    print("Screenshot saved to reg_check.png")
    time.sleep(5)
    browser.close()
