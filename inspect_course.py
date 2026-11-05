from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.add_init_script("window._sys_dt_bypass = true;")
    page.route("**/chunk-4VTC4MLB.js", lambda route: route.abort())
    
    page.goto("https://omp.aistudy.uz/courses/1?debug_bypass=omp-dev-master-99")
    page.wait_for_timeout(3000)
    
    # Check elements on course 1
    info = page.evaluate("""() => {
        return {
            title: document.title,
            headings: Array.from(document.querySelectorAll('h1, h2, h3, h4, h5')).map(h => h.textContent.trim()),
            links: Array.from(document.querySelectorAll('a')).map(a => ({ text: a.textContent.trim(), href: a.href })).filter(a => a.href.includes('course') || a.href.includes('module') || a.href.includes('lesson')),
            buttons: Array.from(document.querySelectorAll('button')).map(b => b.textContent.trim()).filter(t => t.length > 0 && t.length < 50)
        };
    }""")
    print("Course 1 Info:")
    import json
    print(json.dumps(info, indent=2))
