from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=True)
    page = browser.new_page()
    page.goto("https://omp.aistudy.uz/auth/register")
    page.wait_for_timeout(4000)
    page.screenshot(path="register_page_look.png")
    
    with open("register_page_text.txt", "w", encoding="utf-8") as f:
        f.write("URL: " + page.url + "\n")
        for b in page.locator("button, [role='tab'], a, span, p").all():
            try:
                txt = b.inner_text().strip()
                if txt and len(txt) < 100:
                    f.write(f"{b.evaluate('el => el.tagName')}: {txt}\n")
            except Exception:
                pass
    browser.close()
print("DONE DUMPING")
