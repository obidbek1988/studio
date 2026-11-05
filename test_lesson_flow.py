import time
from playwright.sync_api import sync_playwright

EMAIL = "maktab.raxmonov.6159@gmail.com"
PASSWORD = "Maktab29"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.add_init_script("window._sys_dt_bypass = true;")
    page.route("**/chunk-4VTC4MLB.js", lambda route: route.abort())
    
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
    page.wait_for_timeout(2000)
    
    page.locator("input#username, input[formcontrolname='username']").first.fill(EMAIL)
    page.locator("input#password, input[formcontrolname='password']").first.fill(PASSWORD)
    
    from run_visual_test import handle_recaptcha
    handle_recaptcha(page)
    page.wait_for_timeout(2000)
    page.locator("button:has-text('Tizimga kirish')").last.click(force=True)
    page.wait_for_timeout(5000)
    
    page.goto("https://omp.aistudy.uz/courses/1?debug_bypass=omp-dev-master-99")
    page.wait_for_timeout(3000)
    
    btn = page.locator("button:has-text('Hozir boshlang'), a:has-text('Hozir boshlang')").first
    print("Is Hozir boshlang visible?", btn.is_visible())
    btn.click(force=True)
    page.wait_for_timeout(4000)
    print("Current URL after Hozir boshlang:", page.url)
    
    # Check lesson page
    lessons_list = page.evaluate("""() => {
        const items = Array.from(document.querySelectorAll('*')).filter(el => {
            return el.className && typeof el.className === 'string' && el.className.includes('lesson') && el.textContent.trim().length > 0;
        });
        return {
            url: window.location.href,
            video: document.querySelector('video') !== null,
            itemsCount: items.length,
            sampleItems: items.slice(0, 10).map(i => ({ tag: i.tagName, text: i.textContent.trim().slice(0, 50), class: i.className }))
        };
    }""")
    import json
    print(json.dumps(lessons_list, indent=2))
