from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto('https://omp.aistudy.uz/auth/register')
    page.wait_for_timeout(2000)
    
    # Check default documentType
    def check_state(name):
        res = page.evaluate("""() => {
            const btns = Array.from(document.querySelectorAll('button'));
            const pasp = btns.find(b => b.textContent.includes('Pasport'));
            const metr = btns.find(b => b.textContent.includes('Metrika'));
            return {
                pasportClass: pasp ? pasp.className : null,
                metrikaClass: metr ? metr.className : null
            };
        }""")
        print(f"[{name}] Buttons:", res)
        
    check_state("INITIAL")
    page.locator("button:has-text('Metrika')").click(force=True)
    page.wait_for_timeout(1000)
    check_state("AFTER CLICK METRIKA")
