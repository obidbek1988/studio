import time
import requests
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
    
    token = page.evaluate("() => localStorage.getItem('accessToken')")
    print("Token found:", bool(token))
    
    if token:
        headers = {"Authorization": f"Bearer {token}"}
        # Get course structure
        r = requests.get("https://api.aistudy.uz/api/StudyAILms/Course/GetCourseById?id=1", headers=headers)
        print("Course 1 API status:", r.status_code)
        if r.status_code == 200:
            data = r.json()
            modules = data.get("result", {}).get("courseModules", [])
            print(f"Total modules: {len(modules)}")
            for m in modules:
                print(f"Modul {m.get('order')}: {m.get('name')} (ID: {m.get('id')})")
                for l in m.get('lessons', []):
                    print(f"   Lesson {l.get('order')}: ID={l.get('id')}, Type={l.get('type')}, Name={l.get('name')}")
