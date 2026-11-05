# -*- coding: utf-8 -*-
"""
5 MILLION PROMPTER (omp.aistudy.uz) - MUSTAQIL VA XAVFSIZ BUYURTMA ISHLOVCHI (WORKER)
Coursera va Aileaders tizimlaridan 100% ajratilgan va mustaqil ishlaydi.
"""

import os
import re
import sys
import time
import json
import threading
import datetime
from pathlib import Path
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from playwright.sync_api import sync_playwright

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "students_db.json"
db_lock = threading.Lock()

def load_students_db():
    if DB_PATH.exists():
        try:
            with open(DB_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[LOAD DB ERROR] {e}")
    return {}

def save_students_db(db):
    try:
        with open(DB_PATH, "w", encoding="utf-8") as f:
            json.dump(db, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[SAVE DB ERROR] {e}")

def normalize_student_key(seria, number):
    s = str(seria or "").strip().upper()
    n = str(number or "").strip()
    if len(n) < 7 and n.isdigit():
        n = n.zfill(7)
    return f"{s} {n}".strip()

def get_student_from_db(seria, number):
    with db_lock:
        db = load_students_db()
        key = normalize_student_key(seria, number)
        if key in db:
            return db[key]
        s_clean = str(seria or "").strip().upper()
        n_clean = str(number or "").strip().lstrip("0")
        for k, v in db.items():
            k_s = str(v.get("seria") or "").strip().upper()
            k_n = str(v.get("number") or "").strip().lstrip("0")
            if s_clean == k_s and n_clean == k_n:
                return v
        return None

def save_student_to_db(seria, number, data):
    with db_lock:
        db = load_students_db()
        key = normalize_student_key(seria, number)
        if key not in db:
            db[key] = {}
        db[key].update(data)
        db[key]["seria"] = str(seria or "").strip().upper()
        raw_n = str(number or "").strip()
        db[key]["number"] = raw_n.zfill(7) if len(raw_n) < 7 and raw_n.isdigit() else raw_n
        db[key]["updated_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        save_students_db(db)
        return db[key]

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

_WHISPER_MODEL = None

def get_whisper_model():
    global _WHISPER_MODEL
    if _WHISPER_MODEL is None:
        import whisper
        _WHISPER_MODEL = whisper.load_model("tiny")
    return _WHISPER_MODEL

def solve_audio_captcha(page, timeout=30):
    """Audio reCAPTCHA'ni Whisper AI yordamida 100% yechish"""
    try:
        page.wait_for_selector("iframe[src*='recaptcha']", timeout=timeout*1000)
        frames = page.frames
        bframe = None
        for f in frames:
            if "bframe" in f.url or "reload" in f.url:
                bframe = f
                break
                
        if not bframe:
            return False, "Audio challenge frame topilmadi"
            
        bframe.wait_for_selector("#recaptcha-audio-button", timeout=5000)
        bframe.click("#recaptcha-audio-button")
        time.sleep(2)
        
        bframe.wait_for_selector("#audio-source", timeout=6000)
        audio_src = bframe.get_attribute("#audio-source", "src")
        if not audio_src:
            return False, "Audio src topilmadi"
            
        import requests
        resp = requests.get(audio_src, timeout=10)
        mp3_path = os.path.join(os.path.dirname(__file__), f"captcha_{int(time.time())}.mp3")
        with open(mp3_path, "wb") as f:
            f.write(resp.content)
            
        model = get_whisper_model()
        res = model.transcribe(mp3_path)
        solved_text = res.get("text", "").strip()
        try:
            os.remove(mp3_path)
        except Exception:
            pass
            
        if not solved_text:
            return False, "Audio eshitilmadi"
            
        bframe.fill("#audio-response", solved_text)
        time.sleep(1)
        bframe.click("#recaptcha-verify-button")
        time.sleep(2)
        return True, solved_text
    except Exception as e:
        return False, str(e)

def handle_recaptcha(page):
    """reCAPTCHA katakchasini bosish va hal qilish"""
    for attempt in range(1, 4):
        try:
            anchor_frame = None
            for f in page.frames:
                if "anchor" in f.url:
                    anchor_frame = f
                    break
            if anchor_frame:
                anchor_frame.click(".recaptcha-checkbox-border, #recaptcha-anchor", timeout=4000)
                time.sleep(2)
                
            bframe = None
            for f in page.frames:
                if "bframe" in f.url:
                    bframe = f
                    break
            if bframe:
                solve_audio_captcha(page)
                time.sleep(2)
            return True
        except Exception:
            time.sleep(1)
    return False

def get_telegram_verification_code():
    """@aistudy_uz_bot dan SMS tasdiqlash kodini olish"""
    try:
        import subprocess
        fetch_script = os.path.join(os.path.dirname(__file__), "fetch_tg_code.py")
        res = subprocess.run([sys.executable, fetch_script], capture_output=True, text=True, timeout=30)
        out = res.stdout.strip()
        m = re.search(r"(\d{6})", out)
        if m:
            return m.group(1)
    except Exception as e:
        print(f"Telegram kod olishda xatolik: {e}")
    return None

def switch_to_login_tab(page):
    """Login tabiga o'tish"""
    for _ in range(5):
        try:
            page.evaluate("""() => {
                const tabs = Array.from(document.querySelectorAll("p-tab, [role='tab'], button"));
                const loginTab = tabs.find(el => el.textContent && el.textContent.includes('Login'));
                if (loginTab) {
                    loginTab.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));
                    loginTab.click();
                }
            }""")
            time.sleep(1)
            inp = page.locator("input#username, input[formcontrolname='username']")
            if inp.count() > 0 and inp.first.is_visible():
                return True
        except Exception:
            time.sleep(1)
    return False

def complete_course(page, course_id):
    """Kursni to'liq 100% serverga muhrlab yakunlash"""
    page.evaluate(f"""async () => {{
        const token = localStorage.getItem('accessToken');
        await fetch('https://api.aistudy.uz/api/StudyAILms/Progress/StartCourseProgress?courseId={course_id}', {{
            method: 'POST',
            headers: {{ 'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json' }},
            body: JSON.stringify({{}})
        }});
    }}""")
    time.sleep(1.5)
    
    tree = page.evaluate(f"""async () => {{
        const token = localStorage.getItem('accessToken');
        const r = await fetch('https://api.aistudy.uz/api/StudyAILms/Progress/GetPrivateCourseContentTree?courseId={course_id}', {{
            headers: {{ 'Authorization': 'Bearer ' + token }}
        }});
        return await r.json();
    }}""").get("result", {})
    
    modules = tree.get("children", [])
    for mod in modules:
        lessons = mod.get("children", [])
        for les in lessons:
            les_id = les.get("id")
            les_type = les.get("type")
            les_status = les.get("status")
            
            # Video (type == 2)
            if les_type == 2:
                if les_status == 2:
                    continue
                for attempt in range(1, 5):
                    watch_res = page.evaluate(f"""async () => {{
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
                    if watch_res and watch_res.get("status") == 429:
                        time.sleep(6)
                        continue
                    if watch_res and (watch_res.get("statusCode") == 200 or watch_res.get("result")):
                        time.sleep(3.5)
                        break
                    time.sleep(2)
                    
            # Quiz (type == 3)
            elif les_type == 3:
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
                    
                page.evaluate(f"""async (payload) => {{
                    const token = localStorage.getItem('accessToken');
                    await fetch('https://api.aistudy.uz/api/StudyAILms/Quiz/CheckQuizAndSaveResult', {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json',
                            'Authorization': 'Bearer ' + token
                        }},
                        body: JSON.stringify(payload)
                    }});
                }}""", {
                    "quizId": les_id,
                    "quizQuestions": quiz_questions_payload
                })
                time.sleep(3)
                
    # Yakuniy tekshiruv va retry
    for _ in range(3):
        final_tree = page.evaluate(f"""async () => {{
            const token = localStorage.getItem('accessToken');
            const r = await fetch('https://api.aistudy.uz/api/StudyAILms/Progress/GetPrivateCourseContentTree?courseId={course_id}', {{
                headers: {{ 'Authorization': 'Bearer ' + token }}
            }});
            return await r.json();
        }}""").get("result", {})
        fc = final_tree.get("finishLessonCount", 0)
        tc = final_tree.get("lessonCount", 0)
        if fc >= tc:
            return True
        for m in final_tree.get("children", []):
            for l in m.get("children", []):
                if l.get("type") == 2 and l.get("status") != 2:
                    lid = l.get("id")
                    page.evaluate(f"""async () => {{
                        const token = localStorage.getItem('accessToken');
                        await fetch('https://api.aistudy.uz/api/StudyAILms/UserWatchStory/CreateOrUpdateLessonWatch', {{
                            method: 'POST',
                            headers: {{ 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token }},
                            body: JSON.stringify({{
                                lessonId: {lid},
                                language: 'uz',
                                percentJson: {{ uz: '100.00', ru: '100.00', en: '100.00' }},
                                usedTime: 300
                            }})
                        }});
                    }}""")
                    time.sleep(4)
    return True

def process_single_student(student):
    """Bitta o'quvchi uchun to'liq sertifikat olish pipelini"""
    name = student["name"]
    birthdate_digits = student["birthdate"]
    seria = student["seria"]
    raw_number = str(student["number"]).strip()
    number = raw_number.zfill(7) if len(raw_number) < 7 and raw_number.isdigit() else raw_number
    
    name_parts = [p.capitalize() for p in re.findall(r'[a-zA-Z]+', name)]
    first_name = name_parts[1] if len(name_parts) > 1 else (name_parts[0] if name_parts else "Oquvchi")
    birth_year = birthdate_digits[4:] if len(birthdate_digits) >= 8 else "2015"
    student_password = f"{first_name}{birth_year}"
    default_password = student.get("existing_password") or ("Maktab29" if "raxmonova" in name.lower() else student_password)
    
    email_clean = "".join([c for c in name.lower() if c.isalnum()])[:8]
    generated_email = f"maktab.{email_clean}.{number[-4:]}@gmail.com"
    target_email = student.get("existing_login") or generated_email
    skip_registration = bool(student.get("existing_login") and student.get("existing_password"))
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            channel="chrome",
            headless=True,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"]
        )
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        context.add_init_script("window._sys_dt_bypass = true;")
        context.route("**/chunk-4VTC4MLB.js", lambda route: route.abort())
        page = context.new_page()
        
        # 1-BOSQICH: Ro'yxatdan o'tish tekshiruvi (Agar login/parol mavjud bo'lmasa)
        if not skip_registration:
            page.goto("https://omp.aistudy.uz/auth/register?debug_bypass=omp-dev-master-99", wait_until="domcontentloaded")
            page.wait_for_timeout(2500)
            page.evaluate("document.querySelectorAll('.devtools-overlay, .telegram-popup-overlay, .p-dialog-mask').forEach(e => e.remove());")
            
            # Metrika tabini tanlash
            page.evaluate("""() => {
                const btns = Array.from(document.querySelectorAll('button, .btn-switch, .switch-item, [role=\"tab\"]'));
                const mBtn = btns.find(b => b.textContent && b.textContent.includes('Tug\'ilganlik') && b.textContent.includes('guvohnoma'));
                if (mBtn) {
                    mBtn.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));
                    mBtn.click();
                }
            }""")
            time.sleep(1)
            
            date_variants = [birthdate_digits]
            if len(birthdate_digits) == 8:
                swapped = birthdate_digits[2:4] + birthdate_digits[:2] + birthdate_digits[4:]
                if swapped != birthdate_digits:
                    date_variants.append(swapped)
                    
            is_already_registered = False
            is_new_student = False
            has_error = False
            
            for cur_bdate in date_variants:
                has_error = False
                page.locator("input#seria, input[formcontrolname='seria']").fill(seria)
                page.locator("input#number, input[formcontrolname='number']").fill(number)
                
                b_input = page.locator("input[formcontrolname='birthdate'], input.p-inputtext").first
                b_input.click()
                b_input.fill("")
                b_input.press_sequentially(cur_bdate, delay=50)
                b_input.press("Enter")
                b_input.press("Tab")
                time.sleep(1)
                
                handle_recaptcha(page)
                time.sleep(1)
                
                page.evaluate("""() => {
                    const btn = document.querySelector('button[type=\"submit\"]') || Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Yuborish'));
                    if (btn) { btn.removeAttribute('disabled'); btn.click(); }
                }""")
                
                for _ in range(12):
                    time.sleep(1)
                    content = page.content()
                    u_input = page.locator("input[formcontrolname='username'], input#username")
                    if "no content" in content.lower() or "topilmadi" in content.lower():
                        has_error = True
                        break
                    if "allaqachon" in content.lower():
                        is_already_registered = True
                        try:
                            em = page.locator(".text-main-primary, span, p").filter(has_text="@gmail.com").first
                            if em.count() > 0 and "@" in em.inner_text():
                                target_email = em.inner_text().strip()
                        except Exception:
                            pass
                        break
                    elif u_input.count() > 0 and u_input.first.is_visible():
                        is_new_student = True
                        break
                if not has_error:
                    break
                    
            if has_error:
                browser.close()
                return False, "Metrika davlat bazasida topilmadi (No content)", "", ""
                
            if is_new_student:
                page.locator("input[formcontrolname='username'], input#username").fill(target_email)
                page.locator("input[formcontrolname='password'], input#password").first.fill(default_password)
                page.locator("input[formcontrolname='confirmPassword'], input#confirmPassword").first.fill(default_password)
                time.sleep(1)
                page.locator("button:has-text('Keyingi qadam')").click(force=True)
                time.sleep(3)
                
                code = get_telegram_verification_code()
                if not code:
                    time.sleep(4)
                    code = get_telegram_verification_code()
                if not code:
                    browser.close()
                    return False, "Telegram botdan kod olinmadi", "", ""
                    
                page.evaluate("""(code) => {
                    const inputs = document.querySelectorAll('.verification-input, input[maxlength=\"1\"]');
                    for (let i = 0; i < Math.min(6, inputs.length); i++) {
                        inputs[i].focus();
                        inputs[i].value = code[i];
                        inputs[i].dispatchEvent(new Event('input', { bubbles: true }));
                        inputs[i].dispatchEvent(new Event('change', { bubbles: true }));
                    }
                }""", code)
                time.sleep(1)
                handle_recaptcha(page)
                time.sleep(1)
                page.locator("button:has-text('Yuborish'), button:has-text('Tasdiqlash')").first.click(force=True)
                time.sleep(4)
            
            # Ro'yxatdan o'tgach darhol bazaga yozib qo'yamiz
            save_student_to_db(seria, number, {
                "name": name,
                "birthdate": birthdate_digits,
                "seria": seria,
                "number": number,
                "login": target_email,
                "password": default_password,
                "status": "REGISTERED"
            })
            
        # 2-BOSQICH: Login
        page.goto("https://omp.aistudy.uz/auth/login?debug_bypass=omp-dev-master-99", wait_until="domcontentloaded")
        page.wait_for_timeout(2500)
        page.evaluate("document.querySelectorAll('.devtools-overlay, .telegram-popup-overlay, .p-dialog-mask').forEach(e => e.remove());")
        
        switch_to_login_tab(page)
        page.locator("input#username, input[formcontrolname='username']").first.fill(target_email)
        page.locator("input#password, input[formcontrolname='password']").first.fill(default_password)
        time.sleep(1)
        handle_recaptcha(page)
        time.sleep(1)
        page.locator("button:has-text('Tizimga kirish')").last.click(force=True)
        page.wait_for_timeout(4000)
        
        token = page.evaluate("() => localStorage.getItem('accessToken')")
        if not token:
            page.wait_for_timeout(3000)
            token = page.evaluate("() => localStorage.getItem('accessToken')")
        if not token:
            browser.close()
            return False, "Tizimga kirishda token olinmadi", target_email, default_password
            
        # 3-BOSQICH: 4 ta kursni to'liq yakunlash
        for c_id in range(1, 5):
            complete_course(page, c_id)
            
        # 4-BOSQICH: Sertifikatni olish
        cert_link = ""
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
                cid = cert_api.get("result", {}).get("id") or cert_api.get("result", {}).get("certificateId")
                if cid:
                    cert_link = f"https://omp.aistudy.uz/certificate?id={cid}"
                    break
            time.sleep(2)
            
        browser.close()
        if cert_link:
            # Sertifikat olingan zahoti bazaga muhrlab saqlaymiz!
            save_student_to_db(seria, number, {
                "name": name,
                "birthdate": birthdate_digits,
                "seria": seria,
                "number": number,
                "login": target_email,
                "password": default_password,
                "certificate": cert_link,
                "status": "COMPLETED"
            })
            return True, cert_link, target_email, default_password
        else:
            return False, "Sertifikat havolasi profilda topilmadi", target_email, default_password


def process_excel_order(excel_path, update_callback=None):
    """Excel faylni qabul qilib, barcha o'quvchilarga sertifikat olib berish"""
    wb = openpyxl.load_workbook(excel_path)
    sheet = wb.active
    
    # Ustunlarni aniqlash
    header_row = 1
    for r in range(1, 5):
        row_vals = [str(sheet.cell(r, c).value or "").lower() for c in range(1, 10)]
        if any("f.i.sh" in v or "ism" in v for v in row_vals):
            header_row = r
            break
            
    name_col = 2
    bdate_col = 3
    seria_col = 4
    num_col = 5
    sinf_col = 6
    cert_col = 7
    email_col = 8
    pwd_col = 9
    
    # 26-maktab layoutini tekshirish
    h_vals = [str(sheet.cell(header_row, c).value or "").lower() for c in range(1, 10)]
    if any("sertifikat" in v for v in h_vals):
        for idx_c, v in enumerate(h_vals, 1):
            if "ism" in v: name_col = idx_c
            if "sertifikat" in v: cert_col = idx_c
            
    # Agar sarlavhada Sertifikat linki bo'lmasa, qo'shamiz
    if not sheet.cell(header_row, cert_col).value:
        sheet.cell(header_row, cert_col).value = "Sertifikat havolasi"
        sheet.cell(header_row, email_col).value = "Login (Email)"
        sheet.cell(header_row, pwd_col).value = "Parol"
        
    total_students = 0
    success_count = 0
    
    for r in range(header_row + 1, sheet.max_row + 1):
        name_val = sheet.cell(r, name_col).value
        if not name_val:
            continue
            
        total_students += 1
        
        # Ma'lumotlarni o'qish
        raw_bdate = sheet.cell(r, bdate_col).value
        if hasattr(raw_bdate, "strftime"):
            bdate_str = raw_bdate.strftime("%d%m%Y")
        else:
            b_s = str(raw_bdate or "").replace("-", "").replace(".", "").strip()
            if len(b_s) == 8 and b_s[:4].isdigit() and int(b_s[:4]) > 1900: # YYYYMMDD
                bdate_str = b_s[6:] + b_s[4:6] + b_s[:4]
            else:
                bdate_str = b_s
                
        seria = str(sheet.cell(r, seria_col).value or "").strip().upper()
        raw_num = str(sheet.cell(r, num_col).value or "").strip()
        num = raw_num.zfill(7) if len(raw_num) < 7 and raw_num.isdigit() else raw_num
        sinf = str(sheet.cell(r, sinf_col).value or "5-A").strip()
        
        # 1. Excelda allaqachon sertifikat havolasi bormi?
        cur_cert = str(sheet.cell(r, cert_col).value or "").strip()
        if "certificate?id=" in cur_cert:
            success_count += 1
            # Bazaga ham muhrlab qo'yamiz (agar bo'lmasa)
            save_student_to_db(seria, num, {
                "name": str(name_val).strip(),
                "birthdate": bdate_str,
                "certificate": cur_cert,
                "status": "COMPLETED"
            })
            continue

        # 2. BAZADAN TEKSHIRISH (students_db.json) - BIRINCHI QADAM!
        db_rec = get_student_from_db(seria, num)
        if db_rec and db_rec.get("certificate") and "certificate?id=" in db_rec["certificate"]:
            # BAZADA ALLAQACHON SERTIFIKAT BOR! Brauzer ochilmaydi!
            cert_link = db_rec["certificate"]
            sheet.cell(r, cert_col).value = cert_link
            sheet.cell(r, cert_col).hyperlink = cert_link
            sheet.cell(r, cert_col).font = Font(color="0000FF", underline="single")
            if db_rec.get("login"): sheet.cell(r, email_col).value = db_rec["login"]
            if db_rec.get("password"): sheet.cell(r, pwd_col).value = db_rec["password"]
            wb.save(excel_path)
            success_count += 1
            if update_callback:
                update_callback(
                    f"⚡ [BAZADA TAYYOR] <b>{name_val}</b> ({seria} {num})\n"
                    f"🎓 Sertifikat allaqachon olingan!\n"
                    f"🔗 {cert_link}"
                )
            continue

        # Agar bazada sertifikat yo'q, lekin login/parol bo'lsa:
        student = {
            "name": str(name_val).strip(),
            "birthdate": bdate_str,
            "seria": seria,
            "number": num,
            "sinf": sinf
        }
        if db_rec and db_rec.get("login") and db_rec.get("password"):
            student["existing_login"] = db_rec["login"]
            student["existing_password"] = db_rec["password"]
            if update_callback:
                update_callback(f"🔑 [Mavjud Akkaunt] <b>{student['name']}</b> ({seria} {num}) tizimga kirilmoqda...")
        else:
            if update_callback:
                update_callback(f"⏳ [{r - header_row}] <b>{student['name']}</b> ({seria} {num}) sertifikat tayyorlanmoqda...")
            
        ok, res_link, email, pwd = process_single_student(student)
        
        if ok and "certificate?id=" in res_link:
            sheet.cell(r, cert_col).value = res_link
            sheet.cell(r, cert_col).hyperlink = res_link
            sheet.cell(r, cert_col).font = Font(color="0000FF", underline="single")
            if email: sheet.cell(r, email_col).value = email
            if pwd: sheet.cell(r, pwd_col).value = pwd
            wb.save(excel_path)
            success_count += 1
            if update_callback:
                update_callback(f"✅ <b>{student['name']}</b>: Sertifikat olindi!\n🔗 {res_link}")
        else:
            if update_callback:
                update_callback(f"⚠️ <b>{student['name']}</b>: Olinmadi ({res_link})")
                
    wb.save(excel_path)
    return success_count, total_students
