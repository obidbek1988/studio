# Test how video completion works
import time
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.add_init_script("window._sys_dt_bypass = true;")
    page.route("**/chunk-4VTC4MLB.js", lambda route: route.abort())
    
    # We can inspect the lesson HTML structure
    page.goto("https://omp.aistudy.uz/courses/1")
    page.wait_for_timeout(2000)
    
    # Let's see how lessons are listed in HTML
    html = page.content()
    print("HTML length:", len(html))
    
    # Find all elements related to progress or lessons
    res = page.evaluate("""() => {
        return {
            hasNg: typeof ng !== 'undefined',
            localStorageKeys: Object.keys(localStorage)
        };
    }""")
    print("Page env:", res)
