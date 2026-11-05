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
    
    # Listen to watch requests
    page.on("request", lambda req: print(">> REQ:", req.method, req.url) if "Watch" in req.url or "Progress" in req.url else None)
    page.on("response", lambda res: print("<< RES:", res.status, res.url) if "Watch" in res.url or "Progress" in res.url else None)
    
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
    
    print("2. Kurslar sahifasiga o'tish...")
    page.goto("https://omp.aistudy.uz/courses/1?debug_bypass=omp-dev-master-99")
    page.wait_for_timeout(4000)
    page.evaluate("document.querySelectorAll('.devtools-overlay, .telegram-popup-overlay, .p-dialog-mask').forEach(e => e.remove());")
    
    # 'Hozir boshlang' tugmasini bosish
    btn = page.locator("a:has-text('Hozir boshlang'), button:has-text('Hozir boshlang')").first
    if btn.count() > 0 and btn.is_visible():
        print("'Hozir boshlang' tugmasi bosildi!")
        btn.click(force=True)
        page.wait_for_timeout(4000)
        
    print("Joriy dars URL:", page.url)
    
    # Dars sahifasidagi akkordeon va progress
    prog_before = page.locator("omp-learning-progress").inner_text() if page.locator("omp-learning-progress").count() > 0 else "N/A"
    print("Progress before:", prog_before)
    
    # Videoni boshlash
    print("Videoni play qilish...")
    page.evaluate("""() => {
        const v = document.querySelector('video') || document.querySelector('#plyrID');
        if (v) {
            v.muted = true;
            v.play();
        }
    }""")
    
    # 15 soniya kuzatish
    for s in range(1, 16):
        time.sleep(1)
        res = page.evaluate("""() => {
            const v = document.querySelector('video') || document.querySelector('#plyrID');
            const prog = document.querySelector('omp-learning-progress');
            return {
                cur: v ? v.currentTime : null,
                dur: v ? v.duration : null,
                paused: v ? v.paused : null,
                prog: prog ? prog.innerText.trim() : null
            };
        }""")
        print(f"[{s}s] Holat: {res}")
        
    browser.close()
