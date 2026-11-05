import time
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.add_init_script("window._sys_dt_bypass = true;")
    page.route("**/chunk-4VTC4MLB.js", lambda route: route.abort())
    
    page.goto("https://omp.aistudy.uz/courses/1/module/1/lesson/1/type/1")
    page.wait_for_timeout(3000)
    page.evaluate("document.querySelectorAll('.devtools-overlay, .telegram-popup-overlay, .p-dialog-mask').forEach(e => e.remove());")
    
    # Check page state
    info = page.evaluate("""() => {
        return {
            title: document.title,
            url: window.location.href,
            video: document.querySelector('video') !== null,
            videoSrc: document.querySelector('video')?.src || document.querySelector('source')?.src,
            headings: Array.from(document.querySelectorAll('h1, h2, h3, h4, h5')).map(h => h.textContent.trim()),
            buttons: Array.from(document.querySelectorAll('button')).map(b => b.textContent.trim()).filter(t => t.length > 0 && t.length < 50),
            sidebarLessons: Array.from(document.querySelectorAll('*')).filter(el => {
                return el.className && typeof el.className === 'string' && el.className.includes('lesson') && el.textContent.trim().length > 0 && el.children.length === 0;
            }).slice(0, 15).map(e => ({ tag: e.tagName, text: e.textContent.trim(), class: e.className }))
        };
    }""")
    import json
    print(json.dumps(info, indent=2))
