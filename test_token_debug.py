import time
from playwright.sync_api import sync_playwright
import process_5million_excel as pe

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.add_init_script("window._sys_dt_bypass = true;")
    page.route("**/chunk-4VTC4MLB.js", lambda route: route.abort())
    page.goto("https://omp.aistudy.uz/auth/login?debug_bypass=omp-dev-master-99")
    page.wait_for_timeout(2500)
    
    pe.switch_to_login_tab(page)
    page.locator("input#username, input[formcontrolname='username']").first.fill("maktab.ismanov.7204@gmail.com")
    page.locator("input#password, input[formcontrolname='password']").first.fill("Axlidin2015")
    time.sleep(1)
    pe.handle_recaptcha(page)
    time.sleep(1)
    page.locator("button:has-text('Tizimga kirish')").last.click(force=True)
    time.sleep(4)
    
    token = page.evaluate("() => localStorage.getItem('accessToken')")
    print("Token found:", bool(token), token[:20] if token else "NONE")
    
    # Ekranda qanday xabar chiqdi?
    toast = page.locator(".p-toast-message, .p-message, .alert, .text-danger, .error")
    if toast.count() > 0:
        print("Toast error:", toast.all_inner_texts())
    else:
        print("Body text sample:", page.inner_text("body")[:300].replace("\n", " "))
        
    page.screenshot(path="login_debug_ismanov.png")
