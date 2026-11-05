from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.add_init_script("window._sys_dt_bypass = true;")
    page.route("**/chunk-4VTC4MLB.js", lambda route: route.abort())
    
    def log_request(request):
        if "api" in request.url or "GetPersonDataFromGcp" in request.url:
            print(f">> REQ: {request.method} {request.url}")
            print("   PAYLOAD:", request.post_data)
            
    page.on("request", log_request)
    page.goto('https://omp.aistudy.uz/auth/register')
    page.wait_for_timeout(2000)
    
    # Method 1 click Metrika
    page.evaluate("""() => {
        const btns = Array.from(document.querySelectorAll('button'));
        const metr = btns.find(b => b.textContent.includes('Metrika'));
        if (metr) {
            metr.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));
            metr.click();
        }
    }""")
    page.wait_for_timeout(1000)
    
    page.locator("input#seria, input[formcontrolname='seria']").fill("I-FR")
    page.locator("input#number, input[formcontrolname='number']").fill("806159")
    
    birth_input = page.locator("input[formcontrolname='birthdate'], input.p-inputtext").first
    birth_input.click()
    birth_input.fill("")
    birth_input.press_sequentially("09092014", delay=50)
    birth_input.press("Enter")
    page.wait_for_timeout(1000)
    
    page.evaluate("""() => {
        const btn = document.querySelector('button[type="submit"]');
        if (btn) btn.click();
    }""")
    page.wait_for_timeout(3000)
