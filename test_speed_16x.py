import os
import sys
import time
from playwright.sync_api import sync_playwright

if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=False, slow_mo=50)
    page = browser.new_page()
    page.add_init_script("window._sys_dt_bypass = true;")
    page.route("**/chunk-4VTC4MLB.js", lambda route: route.abort())

    print("1. Kurs 2 Dars 23 sahifasiga to'g'ridan-to'g'ri kirilmoqda...")
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

    page.locator("input#username, input[formcontrolname='username']").first.fill("maktab.raxmonov.6159@gmail.com")
    page.locator("input#password, input[formcontrolname='password']").first.fill("Maktab29")
    
    from run_visual_test import handle_recaptcha
    handle_recaptcha(page)
    time.sleep(1)

    page.locator("button:has-text('Tizimga kirish')").last.click(force=True)
    page.wait_for_timeout(4000)

    print("2. Kurs 2, Dars 23 sahifasi ochilmoqda...")
    page.goto("https://omp.aistudy.uz/courses/2/module/4/lesson/23/type/2?debug_bypass=omp-dev-master-99")
    page.wait_for_timeout(4000)
    page.evaluate("document.querySelectorAll('.devtools-overlay, .telegram-popup-overlay, .p-dialog-mask').forEach(e => e.remove());")

    # Video tezligini 16x qilish va ovozni o'chirish
    print("3. Video 16x tezlikda (ovozsiz) o'ynatilmoqda...")
    page.evaluate("""() => {
        const v = document.querySelector('video');
        if (v) {
            v.muted = true;
            v.volume = 0;
            v.playbackRate = 16.0;
            v.play();
        }
    }""")

    # Video tugashini kutamiz (2:58 / 16 = ~11 soniya!)
    for sec in range(1, 20):
        time.sleep(1)
        info = page.evaluate("""() => {
            const v = document.querySelector('video');
            return {
                currentTime: v ? v.currentTime : 0,
                duration: v ? v.duration : 0,
                ended: v ? v.ended : false,
                paused: v ? v.paused : false
            };
        }""")
        print(f"[{sec}s] Vaqt: {info['currentTime']:.1f} / {info['duration']:.1f}s | Tugadimi: {info['ended']}")
        if info['ended'] or (info['duration'] > 0 and info['currentTime'] >= info['duration'] - 1):
            print("Video yakunlandi!")
            break

    time.sleep(3)
    
    # Serverdagi dars statusini tekshirish
    st = page.evaluate("""async () => {
        const token = localStorage.getItem('accessToken');
        const r = await fetch('https://api.aistudy.uz/api/StudyAILms/Lesson/GetLessonById?id=23', {
            headers: { 'Authorization': 'Bearer ' + token }
        });
        return await r.json();
    }""")
    print("Dars 23 serverdagi yangi holati:", st.get("result", {}).get("progressStatus"))

    tree = page.evaluate("""async () => {
        const token = localStorage.getItem('accessToken');
        const r = await fetch('https://api.aistudy.uz/api/StudyAILms/Progress/GetPrivateCourseContentTree?courseId=2', {
            headers: { 'Authorization': 'Bearer ' + token }
        });
        return await r.json();
    }""").get("result", {})
    print(f"Kurs 2 yangi progressi: {tree.get('finishLessonCount')} / {tree.get('lessonCount')}")
    browser.close()
