import time
import json
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.add_init_script("window._sys_dt_bypass = true;")
    page.route("**/chunk-4VTC4MLB.js", lambda route: route.abort())
    
    responses = []
    def on_response(response):
        if "api" in response.url or "auth" in response.url:
            try:
                responses.append({
                    "url": response.url,
                    "status": response.status,
                    "text": response.text()[:200]
                })
            except Exception:
                pass
                
    page.on("response", on_response)
    page.goto("https://omp.aistudy.uz/auth/register?debug_bypass=omp-dev-master-99", wait_until="networkidle")
    
    # Click Metrika
    page.locator("button:has-text('Metrika')").click(force=True)
    page.wait_for_timeout(1000)
    page.locator("input#seria, input[formcontrolname='seria']").fill("I-FR")
    page.locator("input#number, input[formcontrolname='number']").fill("806159")
    
    # Check birthdate input properties
    b_info = page.evaluate("""() => {
        const inp = document.querySelector("input[formcontrolname='birthdate'], input.p-inputtext");
        return {
            tagName: inp?.tagName,
            type: inp?.type,
            placeholder: inp?.placeholder,
            value: inp?.value,
            outerHTML: inp?.outerHTML
        };
    }""")
    print("Birthdate input info:", b_info)
    
    # Try typing birthdate
    birth_input = page.locator("input[formcontrolname='birthdate'], input.p-inputtext").first
    birth_input.click()
    birth_input.fill("")
    birth_input.press_sequentially("09092014", delay=50)
    birth_input.press("Enter")
    page.wait_for_timeout(1000)
    print("Value after 09092014:", birth_input.input_value())
    
    # Check form validity in Angular
    form_val = page.evaluate("""() => {
        const form = document.querySelector('form');
        const btn = document.querySelector('button[type="submit"]');
        return {
            formValid: form ? form.checkValidity() : null,
            btnDisabled: btn ? btn.disabled : null,
            btnClass: btn ? btn.className : null
        };
    }""")
    print("Form state:", form_val)
