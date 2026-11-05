import time
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto('https://omp.aistudy.uz/auth/login?debug_bypass=omp-dev-master-99', wait_until='networkidle')
    page.wait_for_timeout(2000)
    
    print("Testing tab click...")
    # Try clicking using different methods
    # Method 1: locator click
    tab = page.locator("p-tab[value='login']")
    print("Found p-tab[value='login']:", tab.count())
    tab.click(force=True)
    page.wait_for_timeout(2000)
    
    # Check if username input is visible
    u = page.locator("input#username")
    print("Is #username visible after tab.click()?", u.is_visible() if u.count() > 0 else False)
    
    if not (u.count() > 0 and u.is_visible()):
        print("Trying JS click...")
        page.evaluate("""() => {
            const tab = document.querySelector("p-tab[value='login']");
            if (tab) {
                tab.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));
                tab.click();
            }
        }""")
        page.wait_for_timeout(2000)
        print("Is #username visible after JS click?", u.is_visible() if u.count() > 0 else False)
