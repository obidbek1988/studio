import time
import re
from playwright.sync_api import sync_playwright
from run_course_engine import complete_course
from run_visual_test import handle_recaptcha, save_cert_to_excel

EMAIL = "maktab.raxmonov.6159@gmail.com"
PASSWORD = "Maktab29"
NAME = "RAXMONOVA ZULAYHO ILHOMJON QIZI"

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=False, slow_mo=40)
    context = browser.new_context(no_viewport=True)
    page = context.new_page()
    page.add_init_script("window._sys_dt_bypass = true;")
    page.route("**/chunk-4VTC4MLB.js", lambda route: route.abort())
    
    print("\n1. Tizimga kirish...")
    page.goto("https://omp.aistudy.uz/auth/login?debug_bypass=omp-dev-master-99")
    page.wait_for_timeout(2500)
    page.evaluate("document.querySelectorAll('.devtools-overlay, .telegram-popup-overlay, .p-dialog-mask').forEach(e => e.remove());")
    
    page.evaluate("""() => {
        const tabs = Array.from(document.querySelectorAll("p-tab, [role='tab'], button"));
        const loginTab = tabs.find(el => el.textContent && el.textContent.includes('Login'));
        if (loginTab) {
            loginTab.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));
            loginTab.click();
        }
    }""")
    page.wait_for_timeout(1000)
    
    page.locator("input#username, input[formcontrolname='username']").first.fill(EMAIL)
    page.locator("input#password, input[formcontrolname='password']").first.fill(PASSWORD)
    
    handle_recaptcha(page)
    page.wait_for_timeout(1000)
    
    page.locator("button:has-text('Tizimga kirish')").last.click(force=True)
    page.wait_for_timeout(4000)
    
    token = page.evaluate("() => localStorage.getItem('accessToken')")
    print("Token mavjud:", bool(token))
    
    # 4 ta kursni to'liq yakunlash
    for c_id in range(1, 5):
        complete_course(page, c_id)
        
    print("\n🎓 Profilga o'tib sertifikat olinmoqda...")
    page.goto("https://omp.aistudy.uz/profile?debug_bypass=omp-dev-master-99")
    page.wait_for_timeout(4000)
    page.evaluate("document.querySelectorAll('.devtools-overlay, .telegram-popup-overlay, .p-dialog-mask').forEach(e => e.remove());")
    
    cert_link = ""
    for _ in range(5):
        cert_api = page.evaluate("""async () => {
            const token = localStorage.getItem('accessToken');
            const r = await fetch('https://api.aistudy.uz/api/StudyAILms/Certificate/GetCertificateByUser', {
                headers: { 'Authorization': 'Bearer ' + token }
            });
            if (r.status === 200) return await r.json();
            return null;
        }""")
        if cert_api and cert_api.get("result"):
            cert_id = cert_api.get("result", {}).get("id") or cert_api.get("result", {}).get("certificateId")
            if cert_id:
                cert_link = f"https://omp.aistudy.uz/certificate?id={cert_id}"
                break
        time.sleep(2)
        
    if not cert_link:
        anchors = page.locator("a[href*='/certificate']").all()
        for a in anchors:
            href = a.get_attribute("href")
            if href and "certificate?id=" in href:
                if not href.startswith("http"):
                    href = "https://omp.aistudy.uz" + href
                cert_link = href
                break
                
    if not cert_link:
        content = page.content()
        m = re.search(r'https://omp\.aistudy\.uz/certificate\?id=([a-f0-9\-]+)', content)
        if m:
            cert_link = m.group(0)
            
    print(f"\n🎉 ZULAYHO UCHUN SERTIFIKAT HAVOLASI: {cert_link}")
    if cert_link:
        save_cert_to_excel(NAME, cert_link)
        print("✅ Excelga saqlandi!")
        
    page.screenshot(path="5millionsertifikat/cert_success.png")
    page.wait_for_timeout(3000)
    browser.close()
