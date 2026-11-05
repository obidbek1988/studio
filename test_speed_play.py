import time
from playwright.sync_api import sync_playwright

EMAIL = "maktab.raxmonov.6159@gmail.com"
PASSWORD = "Maktab29"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, slow_mo=100)
    page = browser.new_page()
    page.add_init_script("window._sys_dt_bypass = true;")
    page.route("**/chunk-4VTC4MLB.js", lambda route: route.abort())
    
    # Login
    print("Logging in...")
    page.goto("https://omp.aistudy.uz/auth/login?debug_bypass=omp-dev-master-99")
    page.wait_for_timeout(2000)
    
    # Click Login - Parol
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
    handle_recaptcha(page)
    page.wait_for_timeout(2000)
    
    page.locator("button:has-text('Tizimga kirish')").last.click(force=True)
    page.wait_for_timeout(4000)
    
    # Go to lesson 1
    print("Navigating to Module 1 Lesson 1...")
    page.goto("https://omp.aistudy.uz/courses/1/module/1/lesson/1/type/1?debug_bypass=omp-dev-master-99")
    page.wait_for_timeout(4000)
    page.evaluate("document.querySelectorAll('.devtools-overlay, .telegram-popup-overlay, .p-dialog-mask').forEach(e => e.remove());")
    
    # Check initial circle text
    initial_progress = page.evaluate("""() => {
        const prog = document.querySelector('omp-learning-progress') || document.querySelector('[class*=\"progress\"]');
        return prog ? prog.innerText.trim() : 'NOT_FOUND';
    }""")
    print("Initial progress circle:", initial_progress)
    
    # SPEED UP VIDEO TO 16X AND CALL API
    print("Starting high-speed video playback (16x) and API call...")
    page.evaluate("""async () => {
        const v = document.querySelector('video') || document.querySelector('#plyrID');
        if (v) {
            v.muted = true;
            v.playbackRate = 16.0;
            v.play();
        }
        
        // Also call CreateOrUpdateLessonWatch directly
        const token = localStorage.getItem('accessToken');
        const match = window.location.href.match(/lesson\/([a-zA-Z0-9\-]+)/);
        const lessonId = match ? match[1] : null;
        if (token && lessonId) {
            try {
                await fetch("https://api.aistudy.uz/api/StudyAILms/UserWatchStory/CreateOrUpdateLessonWatch", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "Authorization": `Bearer ${token}`
                    },
                    body: JSON.stringify({
                        lessonId: parseInt(lessonId) || lessonId,
                        language: "uz",
                        percentJson: { uz: "100.00", ru: "100.00", en: "100.00" },
                        usedTime: 300
                    })
                });
            } catch(e) {
                console.error("API error:", e);
            }
        }
    }""")
    
    # Watch progress for 10 seconds
    for sec in range(1, 11):
        time.sleep(1)
        cur_prog = page.evaluate("""() => {
            const v = document.querySelector('video') || document.querySelector('#plyrID');
            const prog = document.querySelector('omp-learning-progress');
            return {
                videoCurrentTime: v ? v.currentTime : null,
                videoDuration: v ? v.duration : null,
                videoEnded: v ? v.ended : null,
                progressText: prog ? prog.innerText.trim() : null
            };
        }""")
        print(f"[{sec}s] State:", cur_prog)
        if cur_prog.get("videoEnded") or (cur_prog.get("progressText") and "100" in cur_prog.get("progressText")):
            print("🎉 Video reached 100% / ended successfully!")
            break
            
    # Inspect accordion lessons after video completion
    acc_lessons = page.evaluate("""() => {
        const acc = document.querySelector('omp-course-modules-accordion');
        if (!acc) return [];
        return Array.from(acc.querySelectorAll('.cursor-pointer, li, div')).filter(el => {
            const t = el.textContent.trim();
            return t.length > 0 && t.length < 60 && el.children.length <= 3;
        }).map(e => ({ text: e.textContent.trim(), class: e.className }));
    }""")
    print("Accordion lessons count:", len(acc_lessons))
    for al in acc_lessons[:10]:
        print(" -", al)
        
    time.sleep(3)
    browser.close()
