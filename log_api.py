import time
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.add_init_script("window._sys_dt_bypass = true;")
    page.route("**/chunk-4VTC4MLB.js", lambda route: route.abort())
    
    def log_request(request):
        if "api" in request.url or "register" in request.url:
            print(f">> REQ: {request.method} {request.url}")
            try:
                print("   PAYLOAD:", request.post_data)
            except Exception:
                pass
                
    def log_response(response):
        if "api" in response.url or "register" in response.url:
            print(f"<< RESP: {response.status} {response.url}")
            try:
                print("   BODY:", response.text()[:300])
            except Exception:
                pass

    page.on("request", log_request)
    page.on("response", log_response)
    
    page.goto("https://omp.aistudy.uz/auth/register?debug_bypass=omp-dev-master-99", wait_until="networkidle")
    page.locator("button:has-text('Metrika')").click(force=True)
    page.wait_for_timeout(1000)
    page.locator("input#seria, input[formcontrolname='seria']").fill("I-FR")
    page.locator("input#number, input[formcontrolname='number']").fill("806159")
    
    birth_input = page.locator("input[formcontrolname='birthdate'], input.p-inputtext").first
    birth_input.click()
    birth_input.fill("")
    birth_input.press_sequentially("09092014", delay=50)
    birth_input.press("Enter")
    page.wait_for_timeout(1000)
    
    # Click Yuborish directly
    print("Clicking submit...")
    page.evaluate("""() => {
        const btn = document.querySelector('button[type="submit"]');
        if (btn) btn.click();
    }""")
    page.wait_for_timeout(5000)
