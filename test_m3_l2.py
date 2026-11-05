import time
from playwright.sync_api import sync_playwright

EMAIL = "maktab.raxmonov.6159@gmail.com"
PASSWORD = "Maktab29"

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=False, slow_mo=50)
    context = browser.new_context(no_viewport=True)
    page = context.new_page()
    page.add_init_script("window._sys_dt_bypass = true;")
    page.route("**/chunk-4VTC4MLB.js", lambda route: route.abort())
    
    print("1. Login...")
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
    
    from run_visual_test import handle_recaptcha
    handle_recaptcha(page)
    page.wait_for_timeout(1000)
    
    page.locator("button:has-text('Tizimga kirish')").last.click(force=True)
    page.wait_for_timeout(4000)
    
    # Endi 2-darsga o'tamiz
    print("2. Modul 3, Dars 2 sahifasiga o'tish...")
    page.goto("https://omp.aistudy.uz/courses/1/module/3/lesson/2/type/2?debug_bypass=omp-dev-master-99")
    page.wait_for_timeout(5000)
    page.evaluate("document.querySelectorAll('.devtools-overlay, .telegram-popup-overlay, .p-dialog-mask').forEach(e => e.remove());")
    
    # Akkordeondagi barcha darslar holatini ko'ramiz
    acc_items = page.evaluate("""() => {
        const acc = document.querySelector('omp-course-modules-accordion');
        if (!acc) return [];
        return Array.from(acc.querySelectorAll('div.cursor-pointer, .accordion-button, div[class*="flex items-center"]')).map(el => el.innerText.trim());
    }""")
    print("Akkordeon elementlari soni:", len(acc_items))
    for it in acc_items[:10]:
        print("  -", it.replace("\n", " | "))
        
    page.screenshot(path="5millionsertifikat/screen_m3_l2.png")
    page.wait_for_timeout(3000)
    browser.close()
