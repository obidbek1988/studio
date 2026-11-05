import time
from playwright.sync_api import sync_playwright

EMAIL = "maktab.raxmonov.6159@gmail.com"
PASSWORD = "Maktab29"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.add_init_script("window._sys_dt_bypass = true;")
    page.route("**/chunk-4VTC4MLB.js", lambda route: route.abort())
    
    print("Logging in...")
    page.goto("https://omp.aistudy.uz/auth/login?debug_bypass=omp-dev-master-99")
    page.wait_for_timeout(2000)
    
    # Switch tab
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
    
    print("Navigating to Module 1 Lesson 1...")
    page.goto("https://omp.aistudy.uz/courses/1/module/1/lesson/1/type/1?debug_bypass=omp-dev-master-99")
    page.wait_for_timeout(4000)
    page.evaluate("document.querySelectorAll('.devtools-overlay, .telegram-popup-overlay, .p-dialog-mask').forEach(e => e.remove());")
    
    res = page.evaluate("""() => {
        return {
            url: window.location.href,
            title: document.title,
            hasVideo: document.querySelector('video') !== null,
            videoSrc: document.querySelector('video')?.src,
            videoDuration: document.querySelector('video')?.duration,
            buttons: Array.from(document.querySelectorAll('button')).map(b => b.textContent.trim()).filter(t => t.length > 0 && t.length < 50),
            sidebarLessons: Array.from(document.querySelectorAll('.lesson-item, [class*=\"lesson\"], [class*=\"module\"]')).slice(0, 15).map(e => ({
                tag: e.tagName,
                text: e.textContent.trim().slice(0, 50),
                class: e.className
            }))
        };
    }""")
    import json
    print(json.dumps(res, indent=2))
