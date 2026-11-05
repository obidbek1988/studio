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
    
    # Listen to all API requests
    def on_req(req):
        if "api.aistudy.uz" in req.url:
            print(f">> [REQ] {req.method} {req.url}")
            if req.post_data:
                print(f"   Payload: {req.post_data[:200]}")
                
    def on_res(res):
        if "api.aistudy.uz" in res.url:
            print(f"<< [RES] {res.status} {res.url}")
            try:
                txt = res.text()
                print(f"   Resp: {txt[:200]}")
            except Exception:
                pass
                
    page.on("request", on_req)
    page.on("response", on_res)
    
    print("1. Login sahifasiga kirish...")
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
    page.wait_for_timeout(5000)
    
    print("\n2. Kurs 1 darsiga o'tish...")
    page.goto("https://omp.aistudy.uz/courses/1/module/2/lesson/1/type/2?debug_bypass=omp-dev-master-99")
    page.wait_for_timeout(5000)
    page.evaluate("document.querySelectorAll('.devtools-overlay, .telegram-popup-overlay, .p-dialog-mask').forEach(e => e.remove());")
    
    print("\n3. Videoni 16x tezlikda qo'yish...")
    page.evaluate("""() => {
        const v = document.querySelector('video') || document.querySelector('#plyrID');
        if (v) {
            v.muted = true;
            v.playbackRate = 16.0;
            v.play();
        }
    }""")
    
    for sec in range(1, 20):
        time.sleep(1)
        res = page.evaluate("""() => {
            const v = document.querySelector('video') || document.querySelector('#plyrID');
            return v ? { cur: v.currentTime, dur: v.duration, rate: v.playbackRate, paused: v.paused } : null;
        }""")
        if res:
            print(f"[{sec}s] Video holati: {res}")
            if res.get("cur") and res.get("dur") and res["cur"] >= res["dur"] - 1:
                print("Video tugadi!")
                break
                
    time.sleep(4)
    browser.close()
