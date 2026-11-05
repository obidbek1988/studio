import time
from playwright.sync_api import sync_playwright

EMAIL = "maktab.raxmonov.6159@gmail.com"
PASSWORD = "Maktab29"

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=False, slow_mo=100)
    page = browser.new_page()
    page.set_viewport_size({"width": 1280, "height": 800})
    page.add_init_script("window._sys_dt_bypass = true;")
    page.route("**/chunk-4VTC4MLB.js", lambda route: route.abort())
    
    # Login
    print("1. Tizimga kirish...")
    page.goto("https://omp.aistudy.uz/auth/login?debug_bypass=omp-dev-master-99")
    page.wait_for_timeout(2000)
    page.evaluate("document.querySelectorAll('.devtools-overlay, .telegram-popup-overlay, .p-dialog-mask').forEach(e => e.remove());")
    
    # Switch tab to Login - Parol
    page.evaluate("""() => {
        const tabs = Array.from(document.querySelectorAll("p-tab, [role='tab'], button"));
        const loginTab = tabs.find(el => el.textContent && el.textContent.includes('Login'));
        if (loginTab) {
            loginTab.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));
            loginTab.click();
        }
    }""")
    page.wait_for_timeout(1500)
    
    page.locator("input#username, input[formcontrolname='username']").first.fill(EMAIL)
    page.locator("input#password, input[formcontrolname='password']").first.fill(PASSWORD)
    
    from run_visual_test import handle_recaptcha
    handle_recaptcha(page)
    page.wait_for_timeout(2000)
    
    page.locator("button:has-text('Tizimga kirish')").last.click(force=True)
    page.wait_for_timeout(4000)
    page.evaluate("document.querySelectorAll('.devtools-overlay, .telegram-popup-overlay, .p-dialog-mask').forEach(e => e.remove());")
    print("Logged in, URL:", page.url)
    
    # Open courses page
    print("2. Modullar ro'yxatiga o'tish...")
    page.goto("https://omp.aistudy.uz/courses?debug_bypass=omp-dev-master-99")
    page.wait_for_timeout(3000)
    page.evaluate("document.querySelectorAll('.devtools-overlay, .telegram-popup-overlay, .p-dialog-mask').forEach(e => e.remove());")
    
    # Extract courses / modules
    courses = page.evaluate("""() => {
        return Array.from(document.querySelectorAll('a')).filter(a => a.href.includes('/courses/')).map(a => ({
            text: a.textContent.trim(),
            href: a.href
        }));
    }""")
    print("Found course links:", courses)
    
    # Go to courses/1
    print("3. 1-kursga o'tish...")
    page.goto("https://omp.aistudy.uz/courses/1?debug_bypass=omp-dev-master-99")
    page.wait_for_timeout(3000)
    page.evaluate("document.querySelectorAll('.devtools-overlay, .telegram-popup-overlay, .p-dialog-mask').forEach(e => e.remove());")
    
    # Click Hozir boshlang
    btn = page.locator("a:has-text('Hozir boshlang'), button:has-text('Hozir boshlang')").first
    print("Hozir boshlang visible:", btn.is_visible())
    if btn.is_visible():
        btn.click(force=True)
        page.wait_for_timeout(4000)
        page.evaluate("document.querySelectorAll('.devtools-overlay, .telegram-popup-overlay, .p-dialog-mask').forEach(e => e.remove());")
        
    print("URL after Hozir boshlang:", page.url)
    page.screenshot(path="d:/uzbekcodersbot/5millionsertifikat/after_hozir_boshlang.png")
    
    # Let's inspect lessons in the DOM
    info = page.evaluate("""() => {
        return {
            url: window.location.href,
            video: document.querySelector('video') !== null,
            videoSrc: document.querySelector('video')?.src,
            lessons: Array.from(document.querySelectorAll('*')).filter(e => {
                return e.className && typeof e.className === 'string' && (e.className.includes('lesson') || e.className.includes('accordion') || e.className.includes('item'));
            }).slice(0, 10).map(x => ({ tag: x.tagName, text: x.textContent.trim().slice(0, 40), class: x.className }))
        };
    }""")
    print("Page details:")
    import json
    print(json.dumps(info, indent=2))
    time.sleep(3)
    browser.close()
