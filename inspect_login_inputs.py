import time
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto('https://omp.aistudy.uz/auth/login?debug_bypass=omp-dev-master-99', wait_until='networkidle')
    page.wait_for_timeout(2000)
    
    # Click tab
    page.evaluate("""() => {
        const tabs = Array.from(document.querySelectorAll("p-tab, [role='tab'], button"));
        const loginTab = tabs.find(el => el.textContent && el.textContent.includes('Login'));
        if (loginTab) {
            loginTab.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));
            loginTab.click();
        }
    }""")
    page.wait_for_timeout(2000)
    
    inputs = page.evaluate("""() => {
        return Array.from(document.querySelectorAll('input')).map(i => ({
            id: i.id,
            name: i.name,
            type: i.type,
            formcontrolname: i.getAttribute('formcontrolname'),
            placeholder: i.placeholder,
            visible: i.offsetParent !== null
        }));
    }""")
    print("Inputs on Login tab:")
    for inp in inputs:
        print(inp)
        
    buttons = page.evaluate("""() => {
        return Array.from(document.querySelectorAll('button')).map(b => ({
            text: b.textContent.trim(),
            type: b.type,
            disabled: b.disabled,
            visible: b.offsetParent !== null
        }));
    }""")
    print("Buttons:")
    for btn in buttons:
        print(btn)
