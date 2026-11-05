import time
import json
import requests
from playwright.sync_api import sync_playwright

EMAIL = "maktab.raxmonov.6159@gmail.com"
PASSWORD = "Maktab29"

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=False, slow_mo=50)
    context = browser.new_context(no_viewport=True)
    page = context.new_page()
    page.add_init_script("window._sys_dt_bypass = true;")
    page.route("**/chunk-4VTC4MLB.js", lambda route: route.abort())
    
    print("1. Login sahifasiga o'tilmoqda...")
    page.goto("https://omp.aistudy.uz/auth/login?debug_bypass=omp-dev-master-99")
    page.wait_for_timeout(3000)
    page.evaluate("document.querySelectorAll('.devtools-overlay, .telegram-popup-overlay, .p-dialog-mask').forEach(e => e.remove());")
    
    # Switch to login tab
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
    print("2. reCAPTCHA yechilmoqda...")
    handle_recaptcha(page)
    page.wait_for_timeout(1500)
    
    print("3. Tizimga kirish bosilmoqda...")
    page.locator("button:has-text('Tizimga kirish')").last.click(force=True)
    page.wait_for_timeout(5000)
    
    print("Joriy URL:", page.url)
    token = page.evaluate("() => localStorage.getItem('accessToken')")
    print("Token mavjudmi:", bool(token))
    if token:
        with open("5millionsertifikat/token.txt", "w") as f:
            f.write(token)
        print("Token saqlandi!")
    
    if token:
        headers = {"Authorization": f"Bearer {token}"}
        # Check user profile
        r_prof = requests.get("https://api.aistudy.uz/api/StudyAILms/User/GetProfile", headers=headers)
        print("Profile status:", r_prof.status_code, r_prof.text[:200])
        
        # Check all courses
        r_courses = requests.get("https://api.aistudy.uz/api/StudyAILms/Course/GetAllCourses", headers=headers)
        print("Courses status:", r_courses.status_code)
        if r_courses.status_code == 200:
            print("Courses:", json.dumps(r_courses.json(), indent=2, ensure_ascii=False)[:1000])
            
        # Check user course progress
        r_prog = requests.get("https://api.aistudy.uz/api/StudyAILms/Course/GetUserCourseProgress", headers=headers)
        print("Course progress status:", r_prog.status_code, r_prog.text[:500])
        
        # Check Certificate
        r_cert = requests.get("https://api.aistudy.uz/api/StudyAILms/Certificate/GetMyCertificate", headers=headers)
        print("Certificate status:", r_cert.status_code, r_cert.text[:500])

    page.wait_for_timeout(5000)
    browser.close()
