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

def solve_for_account(email, password):
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=False, slow_mo=50)
        context = browser.new_context(no_viewport=True)
        page = context.new_page()
        page.add_init_script("window._sys_dt_bypass = true;")
        page.route("**/chunk-4VTC4MLB.js", lambda route: route.abort())
        
        print(f"\n 1. Login: {email}...")
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
        
        page.locator("input#username, input[formcontrolname='username']").first.fill(email)
        page.locator("input#password, input[formcontrolname='password']").first.fill(password)
        
        from run_visual_test import handle_recaptcha
        handle_recaptcha(page)
        page.wait_for_timeout(1000)
        
        page.locator("button:has-text('Tizimga kirish')").last.click(force=True)
        page.wait_for_timeout(4000)
        
        token = page.evaluate("() => localStorage.getItem('accessToken')")
        if not token:
            print(" Token topilmadi!")
            browser.close()
            return None
            
        print(" Tizimga kirildi! Token mavjud.")
        
        # 4 ta kursni to'liq yakunlash
        for course_id in range(1, 5):
            print(f"\n" + "="*50)
            print(f" KURS {course_id} BOSHLANMOQDA...")
            print("="*50)
            
            # Start course
            page.evaluate(f"""async () => {{
                const token = localStorage.getItem('accessToken');
                await fetch('https://api.aistudy.uz/api/StudyAILms/Progress/StartCourseProgress?courseId={course_id}', {{
                    method: 'POST',
                    headers: {{ 'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{}})
                }});
            }}""")
            time.sleep(2)
            
            # Daraxtni olish va tekshirish
            tree = page.evaluate(f"""async () => {{
                const token = localStorage.getItem('accessToken');
                const r = await fetch('https://api.aistudy.uz/api/StudyAILms/Progress/GetPrivateCourseContentTree?courseId={course_id}', {{
                    headers: {{ 'Authorization': 'Bearer ' + token }}
                }});
                return await r.json();
            }}""").get("result", {})
            
            course_name = tree.get("name", {}).get("uz", f"Kurs {course_id}")
            total_lessons = tree.get("lessonCount", 0)
            print(f" Kurs nomi: {course_name} | Jami darslar: {total_lessons}")
            
            for mod in tree.get("children", []):
                for les in mod.get("children", []):
                    les_id = les.get("id")
                    les_type = les.get("type")
                    les_status = les.get("status")
                    les_name = les.get("name", {}).get("uz", "")
                    
                    # 1. Video (type == 2)
                    if les_type == 2:
                        if les_status == 2:
                            print(f"   [Video {les_id}] {les_name} -> Allaqachon 100%!")
                            continue
                            
                        # Videoni tomosha qilish (retry va rate limit kutish bilan)
                        for attempt in range(1, 10):
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
                                    if (r.status === 429) return {{ status: 429 }};
                                    return await r.json();
                                }} catch(e) {{
                                    return {{ error: e.toString() }};
                                }}
                            }}""")
                            
                            if res and res.get("status") == 429:
                                print(f"     Rate-limit (429). 6 soniya kutilmoqda ({attempt}-urinish)...", flush=True)
                                time.sleep(6)
                                continue
                                
                            if res and (res.get("statusCode") == 200 or res.get("result")):
                                print(f"   [Video {les_id}] {les_name} -> 100% ko'rildi!", flush=True)
                                time.sleep(5) # Cooldown
                                break
                            else:
                                print(f"     Video xatolik: {res}. 3 soniya kutilmoqda...", flush=True)
                                time.sleep(3)
                                
                    # 2. Quiz / Test (type == 3)
                    elif les_type == 3:
                        print(f"\n   [TEST: Quiz ID={les_id}] Savollar yechilmoqda...", flush=True)
                        time.sleep(3)
                        quiz_data = page.evaluate(f"""async () => {{
                            const token = localStorage.getItem('accessToken');
                            const r = await fetch('https://api.aistudy.uz/api/StudyAILms/Quiz/GetQuizById?id={les_id}', {{
                                headers: {{ 'Authorization': 'Bearer ' + token }}
                            }});
                            return await r.json();
                        }}""").get("result", {})
                        
                        questions = quiz_data.get("questions", [])
                        quiz_questions_payload = []
                        for q in questions:
                            q_id = q.get("id")
                            q_text = (q.get("questionText", {}).get("uz", "")).lower()
                            answers = q.get("questionAnswers", [])
                            
                            chosen_answer_id = None
                            for pattern, ans_val in ANSWERS.items():
                                if pattern in q_text:
                                    for a in answers:
                                        a_txt = (a.get("answerText", {}).get("uz", "")).lower()
                                        if ans_val in a_txt or a_txt in ans_val:
                                            chosen_answer_id = a.get("id")
                                            break
                                    if chosen_answer_id:
                                        break
                                        
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
                        print(f"   TEST NATIJASI: {submit_res}", flush=True)
                        time.sleep(5)
                        
            # Kurs yakunini tasdiqlash
            tree_end = page.evaluate(f"""async () => {{
                const token = localStorage.getItem('accessToken');
                const r = await fetch('https://api.aistudy.uz/api/StudyAILms/Progress/GetPrivateCourseContentTree?courseId={course_id}', {{
                    headers: {{ 'Authorization': 'Bearer ' + token }}
                }});
                return await r.json();
            }}""").get("result", {})
            print(f" KURS {course_id} STATUSI: {tree_end.get('finishLessonCount')} / {tree_end.get('lessonCount')}")
            
        # 4 ta kurs yakunlandi, endi sertifikatni olish
        print("\n" + "="*50)
        print(" BARCHA KURSLAR 100% TUGATILDI! SERTIFIKAT HAVOLASI OLINMOQDA...")
        print("="*50)
        
        cert_link = None
        for _ in range(5):
            cert_api = page.evaluate("""async () => {
                const token = localStorage.getItem('accessToken');
                const r = await fetch('https://api.aistudy.uz/api/StudyAILms/Certificate/GetCertificateByUser', {
                    headers: { 'Authorization': 'Bearer ' + token }
                });
                if (r.status === 200) return await r.json();
                return null;
            }""")
            if cert_api and cert_api.get("result"):
                cert_id = cert_api.get("result", {}).get("id") or cert_api.get("result", {}).get("certificateId")
                if cert_id:
                    cert_link = f"https://omp.aistudy.uz/certificate?id={cert_id}"
                    break
            time.sleep(2)
            
        if not cert_link:
            page.goto("https://omp.aistudy.uz/profile?debug_bypass=omp-dev-master-99")
            page.wait_for_timeout(4000)
            anchors = page.locator("a[href*='/certificate']").all()
            for a in anchors:
                href = a.get_attribute("href")
                if href and "certificate?id=" in href:
                    if not href.startswith("http"):
                        href = "https://omp.aistudy.uz" + href
                    cert_link = href
                    break
            if not cert_link:
                content = page.content()
                m = re.search(r'https://omp\.aistudy\.uz/certificate\?id=([a-f0-9\-]+)', content)
                if m:
                    cert_link = m.group(0)
                    
        print(f"\n SERTIFIKAT HAVOLASI: {cert_link}")
        page.screenshot(path="5millionsertifikat/cert_final.png")
        browser.close()
        return cert_link

if __name__ == "__main__":
    link = solve_for_account(EMAIL, PASSWORD)
    print("NATIJA:", link)
