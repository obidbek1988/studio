import time
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.add_init_script("window._sys_dt_bypass = true;")
    page.route("**/chunk-4VTC4MLB.js", lambda route: route.abort())
    
    page.goto("https://omp.aistudy.uz/courses/1")
    page.wait_for_timeout(2000)
    
    details = page.evaluate("""() => {
        const btn = Array.from(document.querySelectorAll('a, button')).find(x => x.textContent.includes('Hozir boshlang'));
        const allButtons = Array.from(document.querySelectorAll('a, button')).map(el => ({
            tag: el.tagName,
            text: el.textContent.trim(),
            href: el.getAttribute('href'),
            class: el.className
        }));
        return {
            btnHTML: btn ? btn.outerHTML : null,
            allButtons: allButtons.filter(b => b.text.length > 0 && b.text.length < 50)
        };
    }""")
    import json
    print(json.dumps(details, indent=2))
