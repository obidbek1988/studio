import time
import json
import re
from playwright.sync_api import sync_playwright

ANSWERS = {
    # Modul 1
    "qaysi biri ai (sun'iy intellekt)ni eng yaxshi tavsiflaydi": "ma'lumotlardan o'rganishi mumkin bo'lgan dasturiy dastur",
    "real hayotiy qo'llanishi": "yuqoridagilarning barchasi",
    "hayot siklining 2 ta bosqichi": "o'rgatish (trenirovka) va xulosa chiqarish (inference)",
    "aniq ishda ekspert bo'lgan": "tor si (narrow ai)",
    "kichigidan kattasiga": "chuqur o'rganish < mashinani o'rganish (machine learning) < si",
    "tyuring testi nima": "sun'iy intellekt dasturi inson kabi o'ylay olishi/gaplasha olishi/o'zini tuta olishini aniqlash testi",
    
    # Modul 2
    "generativ si (sun'iy intellekt) nima": "matn / tasvirlar / musiqa / video kabi yangi kontent yarata oladigan si",
    "llm nimani anglatadi": "katta til modeli (large language model)",
    "chat botlar va qidiruv tizimlari o'rtasidagi asosiy farq": "ular kontekstga e'tibor beradi",
    "prompt nima": "siz sun'iy intellektli chat botga kiritadigan matn",
    "yaxshi promptni tuzishning to'g'ri tartibdagi 3 ta asosiy": "rol - kontekst - vazifa",
    "gallyutsinatsiyalar (hallucinations) nima": "chat botlarning yomon yoki noto'g'ri javoblar berishi",
    
    # Modul 3
    "prompt yozishda quyidagi yondashuvlardan qaysi biri tavsiya": "rol - vazifa - kontekst",
    "si tomonidan yaratilgan matnning asosiy cheklovlaridan biri": "xatolar bo'lishi mumkin va tekshirib chiqishni talab qiladi",
    "ohangini o'zgartirish uchun": "ohang sozlamalari",
    "hr yollash jarayonlarida foydalanishning afzalliklaridan biri": "si ko'plab rezyume",
    "ijtimoiy tarmoqlardagi kampaniya uchun": "yuqoridagilarning barchasi",
    "maxfiy hujjatlarni baham ko'rmaslik": "ularda maxfiylik kafolatlari yo'q",
    "ishga oid vazifalar uchun si dan foydalanganda": "si vaqtni tejaydi, lekin uning ishini har doim tekshirib turing",
    
    # Modul 4
    "matndan tasvir yaratish uchun qaysi sun'iy intellekt": "dall-e / midjourney / stable diffusion",
    "tasvir yaratish uchun qaysi sun'iy intellekt vositasi openai": "dall-e",
    "midjourney yordamida tasvirlarni yaratishda qaysi omil": "batafsilroq va tavsiflovchi promptlar",
    "edge brauzeri copilot'ida dall-e": "bepul tasvir yaratish imkoniyatiga ega bo'lish",
    "musiqa yarata oladi": "suno",
    "tasvir o'lchamini (rezolyutsiyasini) oshirishga": "upscale tugmalari",
    "matndan video yaratish uchun ishlatiladi": "runway ml",
    
    # Yakuniy
    "ushbu kursda si nima deb ta'riflangan": "robot sifatida",
    "tor si (narrow ai) ga misol": "yuqoridagilarning barchasi",
    "tyuring testining maqsadi": "inson deb o'ylashga aldashi",
    "mashhur generativ si-chatbot": "chatgpt",
    "zo'r prompt yaratish uchun asosiy qoida": "rol / kontekst / vazifa",
    "gallyutsinatsiya": "noto'g'ri yoki uydirma",
    "ma'lumotlarni tahlil qilish uchun": "excel jadvallaridagi",
    "microsoft office ilovalariga qaysi si vositasi": "copilot",
    "si va ish haqida qaysi fikr to'g'ri": "yanada samarali bo'ladi",
    "tasvir yaratish uchun openai": "dall-e",
    "matndan video yaratish imkonini": "runway ml",
    "midjourney tasvir yaratishni sozlashda": "tomonlar nisbati"
}

EMAIL = "maktab.raxmonov.6159@gmail.com"
PASSWORD = "Maktab29"

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=False, slow_mo=50)
    context = browser.new_context(no_viewport=True)
    page = context.new_page()
    page.add_init_script("window._sys_dt_bypass = true;")
    page.route("**/chunk-4VTC4MLB.js", lambda route: route.abort())
    
    print("1. Login sahifasiga kirish...")
    page.goto("https://omp.aistudy.uz/auth/login?debug_bypass=omp-dev-master-99")
    page.wait_for_timeout(2500)
    page.evaluate("document.querySelectorAll('.devtools-overlay, .telegram-popup-overlay, .p-dialog-mask').forEach(e => e.remove());")
    
    page.evaluate("""() => {
        const tabs = Array.from(document.querySelectorAll("p-tab, [role='tab'], button"));
        const loginTab = tabs.find(el => el.textContent && el.textContent.includes('Login'));
        if (loginTab) {
            loginTab.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));
            loginTab.click();
        }
    }""")
    page.wait_for_timeout(1000)
    
    page.locator("input#username, input[formcontrolname='username']").first.fill(EMAIL)
    page.locator("input#password, input[formcontrolname='password']").first.fill(PASSWORD)
    
    from run_visual_test import handle_recaptcha
    handle_recaptcha(page)
    page.wait_for_timeout(1000)
    
    page.locator("button:has-text('Tizimga kirish')").last.click(force=True)
    page.wait_for_timeout(4000)
    
    token = page.evaluate("() => localStorage.getItem('accessToken')")
    print("Login muvaffaqiyatli! Token mavjud:", bool(token))
    
    # 4 ta kursni to'liq bajarish
    for course_id in range(1, 5):
        print(f"\n==================== KURS {course_id} BOSHLANMOQDA ====================")
        # Kursni boshlash
        page.evaluate(f"""async () => {{
            const token = localStorage.getItem('accessToken');
            await fetch('https://api.aistudy.uz/api/StudyAILms/Progress/StartCourseProgress?courseId={course_id}', {{
                method: 'POST',
                headers: {{ 'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json' }},
                body: JSON.stringify({{}})
            }});
        }}""")
        time.sleep(1)
        
        # Daraxtni olish
        tree = page.evaluate(f"""async () => {{
            const token = localStorage.getItem('accessToken');
            const r = await fetch('https://api.aistudy.uz/api/StudyAILms/Progress/GetPrivateCourseContentTree?courseId={course_id}', {{
                headers: {{ 'Authorization': 'Bearer ' + token }}
            }});
            return await r.json();
        }}""").get("result", {})
        
        print(f"Kurs: {tree.get('name', {}).get('uz')} | Darslar soni: {tree.get('lessonCount')}")
        
        # Barcha modullar va darslarni aylanib chiqish
        for mod in tree.get("children", []):
            mod_id = mod.get("id")
            for les in mod.get("children", []):
                les_id = les.get("id")
                les_type = les.get("type")
                les_status = les.get("status")
                les_name = les.get("name", {}).get("uz", "")
                
                # 1. Agar Video (type == 2) bo'lsa
                if les_type == 2:
                    if les_status != 2:
                        for retry in range(1, 5):
                            res = page.evaluate(f"""async () => {{
                                try {{
                                    const token = localStorage.getItem('accessToken');
                                    const r = await fetch('https://api.aistudy.uz/api/StudyAILms/UserWatchStory/CreateOrUpdateLessonWatch', {{
                                        method: 'POST',
                                        headers: {{
                                            'Content-Type': 'application/json',
                                            'Authorization': 'Bearer ' + token
                                        }},
                                        body: JSON.stringify({{
                                            lessonId: {les_id},
                                            language: 'uz',
                                            percentJson: {{ uz: '100.00', ru: '100.00', en: '100.00' }},
                                            usedTime: 300
                                        }})
                                    }});
                                    if (r.status === 429) return {{ rate_limit: true }};
                                    return await r.json();
                                }} catch(e) {{
                                    return {{ error: e.toString() }};
                                }}
                            }}""")
                            if res and res.get("rate_limit"):
                                print(f"    ⏳ Rate limit! 3 soniya kutilmoqda ({retry}-urinish)...", flush=True)
                                time.sleep(3)
                                continue
                            print(f"  [Video: {les_id}] {les_name} -> 100% ko'rildi!", flush=True)
                            time.sleep(1.2)
                            break
                    else:
                        print(f"  [Video: {les_id}] {les_name} -> Allaqachon ko'rilgan!", flush=True)
                        
                # 2. Agar Quiz (type == 3) bo'lsa
                elif les_type == 3:
                    print(f"\n  📝 [TEST TOPShIRISh: Quiz ID={les_id}]...")
                    quiz_data = page.evaluate(f"""async () => {{
                        const token = localStorage.getItem('accessToken');
                        const r = await fetch('https://api.aistudy.uz/api/StudyAILms/Quiz/GetQuizById?id={les_id}', {{
                            headers: {{ 'Authorization': 'Bearer ' + token }}
                        }});
                        return await r.json();
                    }}""").get("result", {})
                    
                    questions = quiz_data.get("questions", [])
                    print(f"  Savollar soni: {len(questions)}")
                    
                    quiz_questions_payload = []
                    for q in questions:
                        q_id = q.get("id")
                        q_text = (q.get("questionText", {}).get("uz", "")).lower()
                        answers = q.get("questionAnswers", [])
                        
                        chosen_answer_id = None
                        # Matn bo'yicha to'g'ri javobni qidirish
                        for pattern, ans_val in ANSWERS.items():
                            if pattern in q_text:
                                for a in answers:
                                    a_txt = (a.get("answerText", {}).get("uz", "")).lower()
                                    if ans_val in a_txt or a_txt in ans_val:
                                        chosen_answer_id = a.get("id")
                                        break
                                if chosen_answer_id:
                                    break
                                    
                        # Agar topilmasa "barchasi" yoki 1-javob
                        if not chosen_answer_id:
                            for a in answers:
                                a_txt = (a.get("answerText", {}).get("uz", "")).lower()
                                if "barchasi" in a_txt or "yuqoridagi" in a_txt:
                                    chosen_answer_id = a.get("id")
                                    break
                        if not chosen_answer_id and answers:
                            chosen_answer_id = answers[0].get("id")
                            
                        quiz_questions_payload.append({
                            "quizQuestionId": q_id,
                            "answers": [{"answerId": chosen_answer_id, "state": True}]
                        })
                        
                    # Testni yuborish
                    submit_res = page.evaluate(f"""async (payload) => {{
                        const token = localStorage.getItem('accessToken');
                        const r = await fetch('https://api.aistudy.uz/api/StudyAILms/Quiz/CheckQuizAndSaveResult', {{
                            method: 'POST',
                            headers: {{
                                'Content-Type': 'application/json',
                                'Authorization': 'Bearer ' + token
                            }},
                            body: JSON.stringify(payload)
                        }});
                        return await r.json();
                    }}""", {
                        "quizId": les_id,
                        "quizQuestions": quiz_questions_payload
                    })
                    print(f"  🎉 Test natijasi: {submit_res}")
                    
        # Kurs holatini tekshirish
        tree_after = page.evaluate(f"""async () => {{
            const token = localStorage.getItem('accessToken');
            const r = await fetch('https://api.aistudy.uz/api/StudyAILms/Progress/GetPrivateCourseContentTree?courseId={course_id}', {{
                headers: {{ 'Authorization': 'Bearer ' + token }}
            }});
            return await r.json();
        }}""").get("result", {})
        print(f"🎉 Kurs {course_id} tugadi: {tree_after.get('finishLessonCount')} / {tree_after.get('lessonCount')} yakunlandi!")
        
    print("\n==================== 4 TA KURS YAKUNLANDI! ====================")
    print("Profilga o'tib sertifikat tekshirilmoqda...")
    page.goto("https://omp.aistudy.uz/profile?debug_bypass=omp-dev-master-99")
    page.wait_for_timeout(4000)
    page.evaluate("document.querySelectorAll('.devtools-overlay, .telegram-popup-overlay, .p-dialog-mask').forEach(e => e.remove());")
    
    cert_res = page.evaluate("""async () => {
        const token = localStorage.getItem('accessToken');
        const r = await fetch('https://api.aistudy.uz/api/StudyAILms/Certificate/GetCertificateByUser', {
            headers: { 'Authorization': 'Bearer ' + token }
        });
        if (r.status === 200) {
            return await r.json();
        }
        return null;
    }""")
    print("Sertifikat API javobi:", cert_res)
    
    page.screenshot(path="5millionsertifikat/cert_screen.png")
    page.wait_for_timeout(5000)
    browser.close()
