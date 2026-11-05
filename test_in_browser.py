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
    
    # Endi dars sahifasiga o'tamiz
    page.goto("https://omp.aistudy.uz/courses/1/module/2/lesson/1/type/2?debug_bypass=omp-dev-master-99")
    page.wait_for_timeout(4000)
    page.evaluate("document.querySelectorAll('.devtools-overlay, .telegram-popup-overlay, .p-dialog-mask').forEach(e => e.remove());")
    
    # Brauzer ichidan fetch yuboramiz
    res = page.evaluate("""async () => {
        const token = localStorage.getItem('accessToken');
        const r = await fetch('https://api.aistudy.uz/api/StudyAILms/UserWatchStory/CreateOrUpdateLessonWatch', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + token
            },
            body: JSON.stringify({
                lessonId: 1,
                language: 'uz',
                percentJson: { uz: '100.00', ru: '100.00', en: '100.00' },
                usedTime: 300
            })
        });
        const text = await r.text();
        return { status: r.status, text: text };
    }""")
    print("Fetch result inside browser:", res)
    
    # Progress Content Tree ni tekshirish
    res_tree = page.evaluate("""async () => {
        const token = localStorage.getItem('accessToken');
        const r = await fetch('https://api.aistudy.uz/api/StudyAILms/Progress/GetPrivateCourseContentTree?courseId=1', {
            headers: { 'Authorization': 'Bearer ' + token }
        });
        return await r.json();
    }""")
    tree = res_tree.get("result", {})
    print("Tree finishLessonCount:", tree.get("finishLessonCount"), "/", tree.get("lessonCount"))
    first_mod = tree.get("children", [])[0]
    first_les = first_mod.get("children", [])[0]
    print(f"Lesson {first_les.get('id')} Status:", first_les.get("status"))

    page.wait_for_timeout(2000)
    browser.close()
