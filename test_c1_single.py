import json
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("https://omp.aistudy.uz/courses/1/module/2/lesson/1/type/2?debug_bypass=omp-dev-master-99")
    
    with open("5millionsertifikat/token.txt") as f:
        token = f.read().strip()
        
    res = page.evaluate("""async (token) => {
        const r = await fetch('https://api.aistudy.uz/api/StudyAILms/UserWatchStory/CreateOrUpdateLessonWatch', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + token
            },
            body: JSON.stringify({
                lessonId: 47,
                language: 'uz',
                percentJson: { uz: '100.00', ru: '100.00', en: '100.00' },
                usedTime: 300
            })
        });
        return { status: r.status, text: await r.text() };
    }""", token)
    print("Lesson 47 Watch result:", res)
    browser.close()
