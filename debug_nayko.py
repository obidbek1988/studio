import time
from playwright.sync_api import sync_playwright
import process_5million_excel

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=True)
    context = browser.new_context()
    context.add_init_script("""
        const style = document.createElement('style');
        style.innerHTML = '.telegram-popup-overlay, .devtools-overlay, .p-dialog-mask { display: none !important; pointer-events: none !important; }';
        document.head.appendChild(style);
        window._sys_dt_bypass = true;
    """)
    page = context.new_page()
    page.goto("https://omp.aistudy.uz/auth/register?debug_bypass=omp-dev-master-99")
    page.wait_for_timeout(3000)
    
    page.evaluate("""() => {
        const btns = Array.from(document.querySelectorAll('button, .btn-switch, .switch-item, [role="tab"], span, div'));
        const mBtn = btns.find(b => b.textContent && b.textContent.includes("guvohnoma"));
        if (mBtn) {
            mBtn.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));
            mBtn.click();
        }
    }""")
    time.sleep(1)
    
    page.locator("input#seria, input[formcontrolname='seria']").fill("I-FR")
    page.locator("input#number, input[formcontrolname='number']").fill("0872014")
    
    page.evaluate("document.querySelectorAll('.telegram-popup-overlay, .devtools-overlay, .p-dialog-mask').forEach(e => e.remove());")
    b_input = page.locator("input[formcontrolname='birthdate'], input.p-inputtext").first
    b_input.click(force=True)
    b_input.fill("")
    b_input.press_sequentially("06042015", delay=50)
    b_input.press("Enter")
    b_input.press("Tab")
    time.sleep(1)
    
    print("Solving captcha...")
    process_5million_excel.handle_recaptcha(page)
    time.sleep(2)
    
    page.evaluate("""() => {
        const btn = document.querySelector('button[type="submit"]') || Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Yuborish'));
        if (btn) { btn.removeAttribute('disabled'); btn.click(); }
    }""")
    time.sleep(5)
    page.screenshot(path="nayko_register_result.png")
    print("Screenshot saved to nayko_register_result.png")
    
    content = page.content()
    with open("nayko_page_dump.html", "w", encoding="utf-8") as f:
        f.write(content)
        
    for text in page.locator("body").all_inner_texts():
        print("PAGE TEXT:\n", text)
        
    browser.close()
