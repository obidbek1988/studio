import os
import sys
import time
from playwright.sync_api import sync_playwright
from run_visual_test import handle_recaptcha

if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=False, slow_mo=50)
    page = browser.new_page()
    page.add_init_script("window._sys_dt_bypass = true;")
    page.route("**/chunk-4VTC4MLB.js", lambda route: route.abort())

    print("1. Loginga kirish...")
    page.goto("https://omp.aistudy.uz/auth/login?debug_bypass=omp-dev-master-99")
    page.wait_for_timeout(3000)
    page.evaluate("document.querySelectorAll('.devtools-overlay, .telegram-popup-overlay, .p-dialog-mask').forEach(e => e.remove());")

    page.evaluate("""() => {
        const tabs = Array.from(document.querySelectorAll("p-tab, [role='tab'], button"));
        const loginTab = tabs.find(el => el.textContent && el.textContent.includes('Login'));
        if (loginTab) {
            loginTab.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));
            loginTab.click();
        }
    }""")
    page.wait_for_timeout(1500)

    page.locator("input#username, input[formcontrolname='username']").first.fill("maktab.raxmonov.6159@gmail.com")
    page.locator("input#password, input[formcontrolname='password']").first.fill("Maktab29")
    time.sleep(1)

    handle_recaptcha(page)
    time.sleep(1)

    page.locator("button:has-text('Tizimga kirish')").last.click(force=True)
    page.wait_for_timeout(5000)

    token = page.evaluate("() => localStorage.getItem('accessToken')")
    print(f"Yangi olingan token: {token[:30]}...")

    with open("5millionsertifikat/token.txt", "w") as f:
        f.write(token)

    # Dars 11 ga tekshiruv yuborish
    print("Dars 11 ga CreateOrUpdateLessonWatch yuborilmoqda...")
    res = page.evaluate("""async () => {
        const token = localStorage.getItem('accessToken');
        const r = await fetch('https://api.aistudy.uz/api/StudyAILms/UserWatchStory/CreateOrUpdateLessonWatch', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + token
            },
            body: JSON.stringify({
                lessonId: 11,
                language: 'uz',
                percentJson: { uz: '100.00', ru: '100.00', en: '100.00' },
                usedTime: 293
            })
        });
        return { status: r.status, text: await r.text() };
    }""")
    print("Dars 11 javobi:", res)

    # Kurs 1 daraxtini tekshirish
    tree = page.evaluate("""async () => {
        const token = localStorage.getItem('accessToken');
        const r = await fetch('https://api.aistudy.uz/api/StudyAILms/Progress/GetPrivateCourseContentTree?courseId=1', {
            headers: { 'Authorization': 'Bearer ' + token }
        });
        return await r.json();
    }""").get("result", {})

    print(f"Kurs 1 Progress: {tree.get('finishLessonCount')} / {tree.get('lessonCount')}")
    time.sleep(3)
    browser.close()
