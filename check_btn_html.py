from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto('https://omp.aistudy.uz/auth/register')
    page.wait_for_timeout(2000)
    
    info = page.evaluate("""() => {
        const btns = Array.from(document.querySelectorAll('button'));
        const pasp = btns.find(b => b.textContent.includes('Pasport'));
        const metr = btns.find(b => b.textContent.includes('Metrika'));
        return {
            metrHTML: metr ? metr.outerHTML : null,
            paspHTML: pasp ? pasp.outerHTML : null
        };
    }""")
    print("HTML:", info)
