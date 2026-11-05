import time
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.add_init_script("window._sys_dt_bypass = true;")
    page.route("**/chunk-4VTC4MLB.js", lambda route: route.abort())
    
    page.goto("https://omp.aistudy.uz/courses/1")
    page.wait_for_timeout(2000)
    
    # Click Kirish so`zi
    btn = page.locator("button:has-text('Kirish so`zi')").first
    if btn.is_visible():
        btn.click()
        page.wait_for_timeout(1500)
        
    items = page.evaluate("""() => {
        return Array.from(document.querySelectorAll('a, button, li')).map(el => ({
            tag: el.tagName,
            text: el.textContent.trim(),
            href: el.getAttribute('href'),
            class: el.className
        })).filter(x => x.href && (x.href.includes('lesson') || x.href.includes('module')));
    }""")
    import json
    print(json.dumps(items, indent=2))
