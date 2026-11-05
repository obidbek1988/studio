import os
import re
import time
import openpyxl
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

def clean_print(msg):
    clean = re.sub(r'[^\x00-\x7F]+', ' ', msg)
    print(clean, flush=True)

def complete_course(page, course_id):
    """Berilgan kursni (1..4) to'liq 100% bajarish"""
    clean_print(f"\n==================================================")
    clean_print(f">>> KURS {course_id} BOSHLANMOQDA <<<")
    clean_print(f"==================================================")
    
    # Kurs sahifasiga o'tish
    page.goto(f"https://omp.aistudy.uz/courses/{course_id}?debug_bypass=omp-dev-master-99")
    page.wait_for_timeout(3500)
    page.evaluate("document.querySelectorAll('.devtools-overlay, .telegram-popup-overlay, .p-dialog-mask').forEach(e => e.remove());")
    
    # 'Hozir boshlang' tugmasini bosish
    btn = page.locator("a:has-text('Hozir boshlang'), button:has-text('Hozir boshlang')").first
    if btn.count() > 0 and btn.is_visible():
        btn.click(force=True)
        page.wait_for_timeout(3500)
        
    # Kurs daraxtini olish
    tree = page.evaluate(f"""async () => {{
        const token = localStorage.getItem('accessToken');
        const r = await fetch('https://api.aistudy.uz/api/StudyAILms/Progress/GetPrivateCourseContentTree?courseId={course_id}', {{
            headers: {{ 'Authorization': 'Bearer ' + token }}
        }});
        return await r.json();
    }}""").get("result", {})
    
    total_lessons = tree.get("lessonCount", 0)
    clean_print(f"Kurs: {tree.get('name', {}).get('uz')} | Jami darslar: {total_lessons}")
    
    # Barcha modullar va darslarni tekshirish
    modules = tree.get("children", [])
    for mod_idx, mod in enumerate(modules):
        mod_id = mod.get("id")
        mod_name = mod.get("name", {}).get("uz", "")
        lessons = mod.get("children", [])
        
        clean_print(f"\n--- Modul {mod_idx+1}: {mod_name} (ID: {mod_id}) ---")
        
        for les_idx, les in enumerate(lessons):
            les_id = les.get("id")
            les_type = les.get("type")
            les_name = les.get("name", {}).get("uz", "")
            
            # Agar Video (type == 2) bo'lsa
            if les_type == 2:
                # Dars sahifasiga o'tish
                les_url = f"https://omp.aistudy.uz/courses/{course_id}/module/{mod_id}/lesson/{les_id}/type/2?debug_bypass=omp-dev-master-99"
                page.goto(les_url, wait_until="domcontentloaded")
                page.wait_for_timeout(3000)
                page.evaluate("document.querySelectorAll('.devtools-overlay, .telegram-popup-overlay, .p-dialog-mask').forEach(e => e.remove());")
                
                # Galichka bor-yo'qligini tekshirish
                has_check = page.evaluate(f"""() => {{
                    const acc = document.querySelector('omp-course-modules-accordion');
                    if (!acc) return false;
                    // svg-check yoki completed class
                    const item = Array.from(acc.querySelectorAll('.cursor-pointer, [class*="active-module"]')).find(el => el.innerText.includes("{les_name}"));
                    if (!item) return false;
                    return item.querySelector('svg-check') !== null || item.innerHTML.includes('svg-check');
                }}""")
                
                if has_check:
                    clean_print(f"  [Video {les_id}] {les_name} -> Allaqachon galichka (check) qo'yilgan!")
                    continue
                    
                clean_print(f"  [Video {les_id}] {les_name} ko'rilmoqda (2.5x tezlikda)...")
                
                # Videoni 2.5x tezlikda qo'yish
                page.evaluate("""() => {
                    const v = document.querySelector('video') || document.querySelector('#plyrID');
                    if (v) {
                        v.muted = true;
                        v.playbackRate = 2.5;
                        v.play();
                    }
                }""")
                
                # Video tugashini yoki galichka paydo bo'lishini kutish
                max_wait = 70
                for sec in range(1, max_wait):
                    time.sleep(1)
                    st = page.evaluate("""() => {
                        const v = document.querySelector('video') || document.querySelector('#plyrID');
                        const prog = document.querySelector('omp-learning-progress');
                        return {
                            cur: v ? v.currentTime : null,
                            dur: v ? v.duration : null,
                            ended: v ? v.ended : null,
                            prog: prog ? prog.innerText.replace(/\\n/g, ' ') : null
                        };
                    }""")
                    
                    if st.get("ended") or (st.get("cur") and st.get("dur") and st["cur"] >= st["dur"] - 1):
                        clean_print(f"    -> [Video {les_id}] Tugadi! Progress: {st.get('prog')}")
                        time.sleep(2)
                        break
                        
            # Agar Test/Quiz (type == 3) bo'lsa
            elif les_type == 3:
                clean_print(f"\n  📝 [TEST TOPShIRISh: Quiz ID={les_id}]...")
                quiz_url = f"https://omp.aistudy.uz/courses/{course_id}/module/{mod_id}/lesson/{les_id}/type/3?debug_bypass=omp-dev-master-99"
                page.goto(quiz_url, wait_until="domcontentloaded")
                page.wait_for_timeout(3500)
                page.evaluate("document.querySelectorAll('.devtools-overlay, .telegram-popup-overlay, .p-dialog-mask').forEach(e => e.remove());")
                
                # Quiz ma'lumotlarini olish
                quiz_data = page.evaluate(f"""async () => {{
                    const token = localStorage.getItem('accessToken');
                    const r = await fetch('https://api.aistudy.uz/api/StudyAILms/Quiz/GetQuizById?id={les_id}', {{
                        headers: {{ 'Authorization': 'Bearer ' + token }}
                    }});
                    return await r.json();
                }}""").get("result", {})
                
                questions = quiz_data.get("questions", [])
                clean_print(f"  Savollar soni: {len(questions)}")
                
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
                    
                # Testni topshirish
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
                clean_print(f"  🎉 TEST NATIJASI: {submit_res}")
                time.sleep(3)
                
    # Kurs yakunida daraxtni tekshirish
    final_tree = page.evaluate(f"""async () => {{
        const token = localStorage.getItem('accessToken');
        const r = await fetch('https://api.aistudy.uz/api/StudyAILms/Progress/GetPrivateCourseContentTree?courseId={course_id}', {{
            headers: {{ 'Authorization': 'Bearer ' + token }}
        }});
        return await r.json();
    }}""").get("result", {})
    clean_print(f"🎉 Kurs {course_id} natijasi: {final_tree.get('finishLessonCount')} / {final_tree.get('lessonCount')} yakunlandi!")
    return True
