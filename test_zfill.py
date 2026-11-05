from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.add_init_script("window._sys_dt_bypass = true;")
    page.route("**/chunk-4VTC4MLB.js", lambda route: route.abort())
    
    def log_response(response):
        if "api" in response.url:
            print(f"<< RESP {response.status}: {response.url}")
            try:
                print("   BODY:", response.text()[:200])
            except Exception:
                pass
                
    page.on("response", log_response)
    page.goto('https://omp.aistudy.uz/auth/register')
    page.wait_for_timeout(2000)
    
    # Click Metrika
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
    # ZFILL TO 7 DIGITS!
    num_7 = "806159".zfill(7)
    print(f"Testing number: {num_7}")
    page.locator("input#number, input[formcontrolname='number']").fill(num_7)
    
    birth_input = page.locator("input[formcontrolname='birthdate'], input.p-inputtext").first
    birth_input.click()
    birth_input.fill("")
    birth_input.press_sequentially("09092014", delay=50)
    birth_input.press("Enter")
    page.wait_for_timeout(1000)
    
    # Check form values in Angular
    vals = page.evaluate("""() => {
        return {
            seria: document.querySelector("input#seria, input[formcontrolname='seria']")?.value,
            number: document.querySelector("input#number, input[formcontrolname='number']")?.value,
            birthdate: document.querySelector("input[formcontrolname='birthdate']")?.value
        };
    }""")
    print("Form values:", vals)
