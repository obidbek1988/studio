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
    
    # Log all requests
    page.on("request", lambda r: print(f">> [REQ] {r.method} {r.url}") if "api.aistudy.uz" in r.url else None)
    page.on("response", lambda r: print(f"<< [RES] {r.status} {r.url}") if "api.aistudy.uz" in r.url else None)
    
    page.goto("https://omp.aistudy.uz/auth/login?debug_bypass=omp-dev-master-99")
    page.wait_for_timeout(2000)
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
    
    # 2-darsga o'tish
    page.goto("https://omp.aistudy.uz/courses/1/module/3/lesson/2/type/2?debug_bypass=omp-dev-master-99")
    page.wait_for_timeout(4000)
    page.evaluate("document.querySelectorAll('.devtools-overlay, .telegram-popup-overlay, .p-dialog-mask').forEach(e => e.remove());")
    
    print("\n--- TEST: Dars 2 ni sun'iy ravishda timeupdate qilish ---")
    res = page.evaluate("""() => {
        // Plyr komponentini topish
        const v = document.querySelector('video') || document.querySelector('#plyrID');
        if (!v) return 'No video';
        
        // plyr instances
        // Angular komponenti yoki plyr instance
        return {
            cur: v.currentTime,
            dur: v.duration
        };
    }""")
    print("Video info:", res)
    
    # Video o'ynatamiz va 2x tezlikda qo'yamiz (2x plyr da ruxsat berilgan tezlik!)
    page.evaluate("""() => {
        const v = document.querySelector('video') || document.querySelector('#plyrID');
        if (v) {
            v.muted = true;
            v.playbackRate = 2.0;
            v.play();
        }
    }""")
    
    print("Video 2x tezlikda qo'yildi. 40 soniya kuzatiladi (1 daqiqalik video 33 soniyada tugaydi)...")
    for sec in range(1, 45):
        time.sleep(1)
        st = page.evaluate("""() => {
            const v = document.querySelector('video') || document.querySelector('#plyrID');
            const prog = document.querySelector('omp-learning-progress');
            return {
                cur: v ? v.currentTime : null,
                dur: v ? v.duration : null,
                ended: v ? v.ended : null,
                prog: prog ? prog.innerText.trim() : null
            };
        }""")
        if sec % 5 == 0 or (st.get("ended")):
            print(f"[{sec}s] {st}")
        if st.get("ended"):
            print("Video yakunlandi!")
            break
            
    time.sleep(3)
    page.screenshot(path="5millionsertifikat/screen_after_watch.png")
    browser.close()
