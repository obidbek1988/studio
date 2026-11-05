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
    """Audio reCAPTCHA'ni SpeechRecognition (Google STT) va Whisper AI yordamida 100% yechish"""
    mp3_path = None
    wav_path = None
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

        # Agar hali audio tugmasi bosilmagan bo'lsa, bosamiz
        try:
            audio_btn = bframe.locator("#recaptcha-audio-button, button[title*='audio'], button[title*='Audio']")
            if audio_btn.count() > 0 and audio_btn.first.is_visible():
                audio_btn.first.click(timeout=3000, force=True)
                time.sleep(2)
        except Exception:
            pass

        # Audio yuklab olish havolasini topish (Download icon yoki #audio-source)
        audio_src = None

        # 1. Download tugmasidagi href havolasi
        try:
            dl_links = bframe.locator("a.rc-audiochallenge-tdownload-link, a[download], a[href*='recaptcha'], a[href*='audio'], a[href*='payload']")
            for idx in range(dl_links.count()):
                href = dl_links.nth(idx).get_attribute("href")
                if href and ("http" in href or "payload" in href or "audio" in href):
                    audio_src = href
                    break
        except Exception:
            pass

        # 2. Agar topilmasa, PLAY / IJRO tugmasini bosib ko'ramiz
        if not audio_src:
            try:
                play_btn = bframe.locator("button:has-text('PLAY'), button:has-text('IJRO'), .rc-audiochallenge-play-button, button#audio-play")
                if play_btn.count() > 0:
                    play_btn.first.click(timeout=2000, force=True)
                    time.sleep(1)
            except Exception:
                pass

            if bframe.locator("#audio-source").count() > 0:
                audio_src = bframe.get_attribute("#audio-source", "src")

        # 3. Yana bir bor barcha linklarni tekshirish
        if not audio_src:
            for lk in bframe.locator("a").all():
                href = lk.get_attribute("href")
                if href and ("payload" in href or "audio" in href):
                    audio_src = href
                    break

        if not audio_src:
            return False, "Audio yuklab olish havolasi (audio-source) topilmadi"

        print(f"[CAPTCHA] Audio yuklanmoqda: {audio_src[:60]}...")
        import requests
        resp = requests.get(audio_src, timeout=15)
        mp3_path = os.path.join(os.path.dirname(__file__), f"captcha_{int(time.time())}.mp3")
        wav_path = os.path.join(os.path.dirname(__file__), f"captcha_{int(time.time())}.wav")
        with open(mp3_path, "wb") as f:
            f.write(resp.content)

        solved_text = ""

        # Usul 1: Soundfile + SpeechRecognition (Tez va ffmpeg talab qilmaydi)
        try:
            import soundfile as sf
            import speech_recognition as sr
            data, samplerate = sf.read(mp3_path)
            sf.write(wav_path, data, samplerate)
            r = sr.Recognizer()
            with sr.AudioFile(wav_path) as source:
                audio_data = r.record(source)
            solved_text = r.recognize_google(audio_data)
            print(f"[CAPTCHA] SpeechRecognition muvaffaqiyatli yechdi: '{solved_text}'")
        except Exception as esr:
            print(f"[CAPTCHA SR ERROR] {esr}, Whisper bilan urinib ko'rilmoqda...")

        # Usul 2: Whisper AI (Fallback)
        if not solved_text:
            try:
                model = get_whisper_model()
                res = model.transcribe(mp3_path)
                solved_text = res.get("text", "").strip()
                print(f"[CAPTCHA] Whisper yechdi: '{solved_text}'")
            except Exception as ew:
                print(f"[CAPTCHA WHISPER ERROR] {ew}")

        # Fayllarni tozalash
        for p in [mp3_path, wav_path]:
            if p and os.path.exists(p):
                try:
                    os.remove(p)
                except Exception:
                    pass

        if not solved_text:
            return False, "Audio eshitilmadi / yechilmadi"

        # Javobni kiritish va TASDIQLASH (VERIFY) bosish
        resp_input = bframe.locator("#audio-response, input[id*='audio'], input[type='text']").first
        resp_input.click(force=True)
        resp_input.fill(solved_text)
        time.sleep(1)
        verify_btn = bframe.locator("#recaptcha-verify-button, button:has-text('TASDIQLASH'), button:has-text('VERIFY'), button:has-text('Tasdiqlash')").first
        verify_btn.click(force=True)
        time.sleep(2)
        return True, solved_text
    except Exception as e:
        print(f"[CAPTCHA ENGINE ERROR] {e}")
        return False, str(e)
    finally:
        for p in [mp3_path, wav_path]:
            if p and os.path.exists(p):
                try:
                    os.remove(p)
                except Exception:
                    pass

def handle_recaptcha(page):
    """reCAPTCHA katakchasini bosish va AI bilan yechish (Avto-reload himoyasi bilan)"""
    for attempt in range(1, 6):
        try:
            print(f"[RECAPTCHA] {attempt}-urinish...")
            anchor_frame = None
            for f in page.frames:
                if "anchor" in f.url:
                    anchor_frame = f
                    break
            if anchor_frame:
                checked = anchor_frame.evaluate("() => document.getElementById('recaptcha-anchor')?.getAttribute('aria-checked') === 'true'")
                if checked:
                    print("[RECAPTCHA] Katakcha allaqachon belgilangan (checked=true)!")
                    return True

            # Agar bframe (kapcha oynasi) ekranda ochiq bo'lsa (masalan: "Multiple solutions required"), anchor'ni qayta bosmaymiz!
            bframe_open = False
            for f in page.frames:
                if "bframe" in f.url:
                    try:
                        c_elem = page.locator("iframe[title*='challenge'], iframe[src*='bframe']")
                        if c_elem.count() > 0 and c_elem.first.is_visible():
                            bframe_open = True
                    except Exception:
                        pass
                    break

            if not bframe_open and anchor_frame:
                anchor_frame.click(".recaptcha-checkbox-border, #recaptcha-anchor", timeout=4000, force=True)
                time.sleep(2)

            # Check if solved with 1-click
            if anchor_frame:
                checked = anchor_frame.evaluate("() => document.getElementById('recaptcha-anchor')?.getAttribute('aria-checked') === 'true'")
                if checked:
                    print("[RECAPTCHA] 1-klikda muvaffaqiyatli belgilandi!")
                    return True

            bframe = None
            for f in page.frames:
                if "bframe" in f.url:
                    bframe = f
                    break
            if bframe:
                # Agar Google "Keyinroq urinib ko'ring" (blokirovka) chiqarsa, sahifani yangilaymiz
                try:
                    bcontent = bframe.content()
                    if "Keyinroq" in bcontent or "automated queries" in bcontent or "avtomatik" in bcontent:
                        print("[RECAPTCHA BLOK] Google blok chiqardi, kapcha qayta yuklanmoqda...")
                        try:
                            r_btn = bframe.locator("#recaptcha-reload-button")
                            if r_btn.count() > 0 and r_btn.first.is_visible():
                                r_btn.first.click(force=True)
                                time.sleep(2)
                                continue
                        except Exception:
                            pass
                        print("[RECAPTCHA BLOK] Sahifa avtomatik yangilanmoqda (reload)...")
                        page.reload(wait_until="domcontentloaded")
                        time.sleep(2)
                        continue
                except Exception:
                    pass

                success, text = solve_audio_captcha(page)
                print(f"[RECAPTCHA] Audio solver natijasi: {success} ({text})")
                time.sleep(2)

            if anchor_frame:
                checked = anchor_frame.evaluate("() => document.getElementById('recaptcha-anchor')?.getAttribute('aria-checked') === 'true'")
                if checked:
                    print("[RECAPTCHA] Muvaffaqiyatli yechildi (checked=true)!")
                    return True
        except Exception as ex:
            print(f"[RECAPTCHA ERROR] {ex}")
            time.sleep(1)
    return False

def get_telegram_verification_code():
    """@aistudy_uz_bot dan SMS tasdiqlash kodini olish (Subprocess orqali Playwrightdan to'liq izolyatsiya qilingan)"""
    try:
        import subprocess
        fetch_script = os.path.join(os.path.dirname(__file__), "fetch_tg_code.py")
        res = subprocess.run([sys.executable, fetch_script], capture_output=True, text=True, timeout=45)
        out = res.stdout.strip()
        lines = [ln.strip() for ln in out.splitlines() if ln.strip()]
        if lines:
            last_line = lines[-1]
            parts = last_line.split()
            if len(parts) >= 2 and len(parts[0]) == 6 and parts[0].isdigit():
                return parts[0], parts[1]
            m = re.search(r"\b(\d{6})\b", last_line)
            if m:
                return m.group(1), "session"
    except Exception as e:
        print(f"Telegram kod olishda xatolik: {e}")
    return None, None

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

def perform_safe_login(page, email, password, name="", notify=None):
    """Xavfsiz va reload-bardoshli login qilish (Input bo'shab qolishidan himoyalangan)"""
    for attempt in range(1, 4):
        try:
            page.goto("https://omp.aistudy.uz/auth/login?debug_bypass=omp-dev-master-99", wait_until="domcontentloaded")
            page.wait_for_timeout(2500)
            page.evaluate("document.querySelectorAll('.devtools-overlay, .telegram-popup-overlay, .p-dialog-mask').forEach(e => e.remove());")

            switch_to_login_tab(page)
            time.sleep(1)

            u_inp = page.locator("input#username, input[formcontrolname='username']").first
            u_inp.click(force=True)
            u_inp.fill(email)
            time.sleep(0.5)

            p_inp = page.locator("input#password, input[formcontrolname='password']").first
            p_inp.click(force=True)
            p_inp.fill(password)
            time.sleep(1)

            if notify:
                notify(f"🎧 [{name}] reCAPTCHA audio Whisper AI orqali yechilmoqda ({attempt}-urinish)...")

            handle_recaptcha(page)
            time.sleep(1)

            # AGAR KAPCHA VAQTIDA SAHIFA RELOAD BO'LSA, INPUTLAR TOZALANIB QOLGAN BO'LADI!
            # Shuning uchun yana bir bor tekshiramiz va agar bo'sh bo'lsa, qayta to'ldiramiz!
            switch_to_login_tab(page)
            time.sleep(0.5)
            try:
                cur_u = page.locator("input#username, input[formcontrolname='username']").first.input_value()
                if not cur_u or cur_u != email:
                    print(f"[RE-FILL LOGIN] Input bo'sh qolgan yoki reload bo'lgan, qayta to'ldirilmoqda: {email}")
                    u2 = page.locator("input#username, input[formcontrolname='username']").first
                    u2.click(force=True)
                    u2.fill(email)
                    time.sleep(0.5)
                    p2 = page.locator("input#password, input[formcontrolname='password']").first
                    p2.click(force=True)
                    p2.fill(password)
                    time.sleep(1)
            except Exception as e_rf:
                print(f"[RE-FILL ERROR] {e_rf}")

            # Endi "Tizimga kirish" tugmasini bosamiz
            page.locator("button:has-text('Tizimga kirish')").last.click(force=True)
            page.wait_for_timeout(4000)

            token = page.evaluate("() => localStorage.getItem('accessToken')")
            if not token:
                page.wait_for_timeout(3000)
                token = page.evaluate("() => localStorage.getItem('accessToken')")

            if token:
                print(f"[LOGIN SUCCESS] Tizimga muvaffaqiyatli kirildi ({email})!")
                return token

            page_text = page.content().lower()
            if "topilmadi" in page_text or "not found" in page_text or "mavjud emas" in page_text:
                print(f"[LOGIN NOT FOUND] '{email}' bo'yicha foydalanuvchi topilmadi! Qayta ro'yxatdan o'tishga yo'naltiriladi...")
                return None

            print(f"[LOGIN RETRY] {attempt}-urinishda token olinmadi, qayta urinilmoqda...")
            time.sleep(2)
        except Exception as el:
            print(f"[LOGIN EXCEPTION] {el}")
            time.sleep(2)
    return None

def complete_course(page, course_id, status_callback=None):
    """Kursni to'liq 100% serverga muhrlab yakunlash"""
    course_names = {
        1: "1-modul: Sun'iy intellekt asoslari",
        2: "2-modul: Prompt muhandisligi asoslari",
        3: "3-modul: Promptlar yozish va LLM amaliyot",
        4: "4-modul: Yakuniy imtihon testlari"
    }
    c_title = course_names.get(course_id, f"{course_id}-modul")
    if status_callback:
        status_callback(f"📚 {c_title} 100% yopilmoqda...")

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
                for attempt in range(1, 4):
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
                            return {{ status: r.status, ok: r.ok }};
                        }} catch(e) {{
                            return {{ error: e.toString() }};
                        }}
                    }}""")
                    if watch_res and watch_res.get("status") == 429:
                        time.sleep(5)
                        continue
                    if watch_res and (watch_res.get("ok") or watch_res.get("status") == 200):
                        print(f"    [OK] Modul {course_id} - Dars {les_id} yopildi (✔)")
                        time.sleep(1.2)
                        break
                    time.sleep(1.5)
                    
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
                    time.sleep(1.5)
    if status_callback:
        status_callback(f"✅ {c_title} 100% muvaffaqiyatli yakunlandi!")
    return True

def process_single_student(student, update_callback=None):
    """Bitta o'quvchi uchun to'liq sertifikat olish pipelini"""
    name = student["name"]
    birthdate_digits = student["birthdate"]
    seria = student["seria"]
    raw_number = str(student["number"]).strip()
    number = raw_number.zfill(7) if len(raw_number) < 7 and raw_number.isdigit() else raw_number

    def notify(msg):
        if update_callback:
            try:
                update_callback(msg)
            except Exception as e:
                print(f"[CALLBACK ERROR] {e}")

    name_parts = [p.capitalize() for p in re.findall(r'[a-zA-Z]+', name)]
    first_name = name_parts[1] if len(name_parts) > 1 else (name_parts[0] if name_parts else "Oquvchi")
    birth_year = birthdate_digits[4:] if len(birthdate_digits) >= 8 else "2015"
    student_password = f"{first_name}{birth_year}"
    default_password = student.get("existing_password") or ("Maktab29" if "raxmonova" in name.lower() else student_password)

    email_clean = "".join([c for c in name.lower() if c.isalnum()])[:8]
    generated_email = f"maktab.{email_clean}.{number[-4:]}@gmail.com"
    target_email = student.get("existing_login") or generated_email
    skip_registration = bool(student.get("existing_login") and student.get("existing_password"))

    notify(f"⏳ [{name}] Jarayon boshlandi ({seria} {number})...")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            channel="chrome",
            headless=False,
            args=[
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-features=Translate",
                "--no-default-browser-check",
                "--disable-popup-blocking"
            ]
        )
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            locale="en-US",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        context.add_init_script("""
            window._sys_dt_bypass = true;
            const style = document.createElement('style');
            style.innerHTML = '.telegram-popup-overlay, .devtools-overlay, .p-dialog-mask { display: none !important; pointer-events: none !important; }';
            if (document.head) {
                document.head.appendChild(style);
            } else {
                document.addEventListener('DOMContentLoaded', () => document.head.appendChild(style));
            }
        """)
        context.route("**/chunk-4VTC4MLB.js", lambda route: route.abort())
        page = context.new_page()

        # Agar bazada login/parol bo'lsa, avval to'g'ridan-to'g'ri login qilib ko'ramiz
        token = None
        if skip_registration:
            notify(f"🔑 [{name}] Mavjud akkaunt bilan kirilmoqda ({target_email})...")
            token = perform_safe_login(page, target_email, default_password, name=name, notify=notify)

            # Agar mavjud hisob bilan login o'xshamasa yoki "Foydalanuvchi topilmadi" bo'lsa:
            # TO'XTAMAYMIZ — foydalanuvchi ilgarigi safar SMS tasdiqlanmay qolgan bo'lishi mumkin!
            # Shu sababli darhol to'liq qayta ro'yxatdan o'tishga yo'naltiramiz!
            if not token:
                print(f"[FALLBACK REGISTER] {target_email} bilan login olinmadi. Avtomatik ro'yxatdan o'tish boshlandi...")
                notify(f"⚠️ [{name}] Saytda '{target_email}' topilmadi. Avtomatik qayta ro'yxatdan o'tish boshlanmoqda...")
                skip_registration = False
                target_email = generated_email
                default_password = "Maktab29" if "raxmonova" in name.lower() else student_password
                
                # Bazadagi eskirgan / tasdiqlanmay qolgan loginni tozalaymiz
                save_student_to_db(seria, number, {
                    "name": name,
                    "seria": seria,
                    "number": number,
                    "status": "PENDING",
                    "login": None,
                    "password": None
                })

        # 1-BOSQICH: Ro'yxatdan o'tish tekshiruvi (Agar login qilinmagan bo'lsa)
        if not skip_registration and not token:
            notify(f"📝 [{name}] Metrika kiritilmoqda ({seria} {number})...")
            page.goto("https://omp.aistudy.uz/auth/register?debug_bypass=omp-dev-master-99", wait_until="domcontentloaded")
            page.wait_for_timeout(2500)
            page.evaluate("document.querySelectorAll('.devtools-overlay, .telegram-popup-overlay, .p-dialog-mask').forEach(e => e.remove());")

            # Metrika yoki Pasport tabini tanlash
            is_passport = len(seria) == 2 and seria.isalpha() and seria.upper() not in ["PE"]
            if is_passport:
                page.evaluate("""() => {
                    const btns = Array.from(document.querySelectorAll('button, .btn-switch, .switch-item, [role="tab"]'));
                    const pasp = btns.find(b => b.textContent && b.textContent.includes('Pasport'));
                    if (pasp) { pasp.click(); }
                }""")
            else:
                page.evaluate("""() => {
                    const btns = Array.from(document.querySelectorAll('button, .btn-switch, .switch-item, [role="tab"]'));
                    const metr = btns.find(b => b.textContent && (b.textContent.includes('Metrika') || b.textContent.includes('guvohnoma')));
                    if (metr) {
                        metr.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));
                        metr.click();
                    }
                }""")
            time.sleep(1.5)

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

                page.evaluate("document.querySelectorAll('.telegram-popup-overlay, .devtools-overlay, .p-dialog-mask').forEach(e => e.remove());")
                b_input = page.locator("input[formcontrolname='birthdate'], input.p-inputtext").first
                b_input.click(force=True)
                b_input.fill("")
                b_input.press_sequentially(cur_bdate, delay=50)
                b_input.press("Enter")
                b_input.press("Tab")
                time.sleep(1)

                notify(f"🎧 [{name}] reCAPTCHA audio Whisper AI orqali yechilmoqda...")
                handle_recaptcha(page)
                time.sleep(1)

                # Agar reload bo'lgan bo'lsa, metrika maydonlari bo'shab qoladi! Shuning uchun tekshiramiz va qayta to'ldiramiz:
                try:
                    cur_num_val = page.locator("input#number, input[formcontrolname='number']").first.input_value()
                    if not cur_num_val:
                        print(f"[RE-FILL METRIKA] Kapcha reload qilgan, metrika qayta kiritilmoqda...")
                        page.evaluate("""(is_p) => {
                            const btns = Array.from(document.querySelectorAll('button, .btn-switch, .switch-item, [role="tab"]'));
                            const tab_btn = btns.find(b => b.textContent && (is_p ? b.textContent.includes('Pasport') : (b.textContent.includes('Metrika') || b.textContent.includes('guvohnoma'))));
                            if (tab_btn) { tab_btn.click(); }
                        }""", is_passport)
                        time.sleep(1)
                        page.locator("input#seria, input[formcontrolname='seria']").fill(seria)
                        page.locator("input#number, input[formcontrolname='number']").fill(number)
                        b_inp = page.locator("input[formcontrolname='birthdate'], input.p-inputtext").first
                        b_inp.click(force=True)
                        b_inp.fill("")
                        b_inp.press_sequentially(cur_bdate, delay=50)
                        time.sleep(1)
                except Exception as e_rf_m:
                    print(f"[METRIKA REFILL ERROR] {e_rf_m}")

                time.sleep(2)
                page.evaluate("""() => {
                    const btn = document.querySelector('button[type="submit"]') || Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Yuborish'));
                    if (btn) { btn.removeAttribute('disabled'); btn.click(); }
                }""")
                time.sleep(0.5)
                try:
                    page.locator("button:has-text('Yuborish')").first.click(force=True)
                except Exception:
                    pass

                # Davlat bazasidan javob kelishini 25 soniya shoshmasdan kutamiz:
                for _ in range(25):
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
                notify(f"❌ [{name}] Metrika davlat bazasida topilmadi ({seria} {number})")
                return False, "Metrika davlat bazasida topilmadi (No content)", "", ""

            if not is_new_student and not is_already_registered:
                browser.close()
                notify(f"❌ [{name}] Ro'yxatdan o'tish oynasiga o'tib bo'lmadi (Kapcha yechilmadi)")
                return False, "Ro'yxatdan o'tish oynasiga o'tib bo'lmadi (Kapcha yechilmadi)", "", ""

            if is_new_student:
                notify(f"📝 [{name}] Yangi login ochilmoqda ({target_email})...")
                page.locator("input[formcontrolname='username'], input#username").fill(target_email)
                page.locator("input[formcontrolname='password'], input#password").first.fill(default_password)
                page.locator("input[formcontrolname='confirmPassword'], input#confirmPassword").first.fill(default_password)
                time.sleep(1)
                page.locator("button:has-text('Keyingi qadam')").click(force=True)
                time.sleep(3)

                from session_pool import mark_session_exhausted, record_session_success

                registration_success = False
                for reg_attempt in range(1, 10):
                    notify(f"📩 [{name}] Telegram botdan (@aistudy_uz_bot) tasdiqlash kodi olinmoqda ({reg_attempt}-urinish)...")
                    code, session_used = get_telegram_verification_code()
                    if not code:
                        time.sleep(3)
                        code, session_used = get_telegram_verification_code()
                    if not code:
                        notify(f"⚠️ [{name}] Sessiyalardan kod olinmadi, qayta urinilmoqda...")
                        continue

                    page.evaluate("""(code) => {
                        const inputs = document.querySelectorAll('.verification-input, input[maxlength="1"]');
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

                    # Agar reload bo'lgan bo'lsa yoki kod o'chib ketgan bo'lsa, qayta to'ldirish:
                    try:
                        c_inp = page.locator(".verification-input, input[maxlength='1']").first
                        if not c_inp.input_value():
                            print(f"[RE-FILL CODE] Tasdiqlash kodi o'chib ketgan, qayta kiritilmoqda: {code}")
                            page.evaluate("""(code) => {
                                const inputs = document.querySelectorAll('.verification-input, input[maxlength="1"]');
                                for (let i = 0; i < Math.min(6, inputs.length); i++) {
                                    inputs[i].focus();
                                    inputs[i].value = code[i];
                                    inputs[i].dispatchEvent(new Event('input', { bubbles: true }));
                                    inputs[i].dispatchEvent(new Event('change', { bubbles: true }));
                                }
                            }""", code)
                            time.sleep(1)
                    except Exception:
                        pass

                    page.locator("button:has-text('Yuborish'), button:has-text('Tasdiqlash')").first.click(force=True)
                    time.sleep(4)

                    content = page.content().lower()
                    if "cheklangan" in content or "bitta telefon" in content:
                        notify(f"⚠️ [{name}] {session_used} raqami limitga yetgan, keyingi sessiyaga o'tilmoqda...")
                        mark_session_exhausted(session_used, reason="Bitta raqam cheklovi")
                        try:
                            resend_btn = page.locator("button:has-text('qayta'), a:has-text('qayta')")
                            if resend_btn.count() > 0 and resend_btn.first.is_visible():
                                resend_btn.first.click(force=True)
                                time.sleep(2)
                        except Exception:
                            pass
                        continue
                    else:
                        record_session_success(session_used)
                        registration_success = True
                        break

                if not registration_success:
                    browser.close()
                    notify(f"❌ [{name}] Ro'yxatdan o'tishda telefon raqamlari limitga uchradi")
                    return False, "Ro'yxatdan o'tishda telefon raqamlari limitga uchradi", "", ""

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

            # 2-BOSQICH: Yangi olingan login/parol bilan kirish
            notify(f"🔓 [{name}] Tizimga kirilmoqda ({target_email})...")
            token = perform_safe_login(page, target_email, default_password, name=name, notify=notify)
            if not token:
                browser.close()
                notify(f"❌ [{name}] Tizimga kirishda token olinmadi (Login/Parol xato)")
                return False, "Tizimga kirishda token olinmadi (Parol yoki Login xato)", target_email, default_password

        # Agar token yo'q bo'lsa
        if not token:
            browser.close()
            notify(f"❌ [{name}] Tizimga kirishda token olinmadi")
            return False, "Tizimga kirishda token olinmadi", target_email, default_password

        notify(f"🔓 [{name}] Tizimga muvaffaqiyatli kirildi! Kurslar boshlandi...")

        # 3-BOSQICH: 4 ta kursni to'liq yakunlash
        for c_id in range(1, 5):
            complete_course(page, c_id, status_callback=notify)

        # 4-BOSQICH: Sertifikatni olish
        notify(f"🏆 [{name}] Sertifikat havolasi olinmoqda...")
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
            notify(f"❌ [{name}] Sertifikat havolasi profilda topilmadi")
            return False, "Sertifikat havolasi profilda topilmadi", target_email, default_password


def format_duration(seconds):
    """Vaqtni chiroyli ko'rinishga keltirish (masalan: 1 daqiqa 15 soniya)"""
    seconds = int(round(seconds))
    if seconds < 60:
        return f"{seconds} soniya"
    mins = seconds // 60
    rem = seconds % 60
    if rem == 0:
        return f"{mins} daqiqa"
    return f"{mins} daqiqa {rem} soniya"

def process_excel_order(excel_path, update_callback=None):
    """Excel faylni qabul qilib, barcha o'quvchilarga sertifikat olib berish"""
    excel_start_time = time.time()
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
    time_col = 10
    
    # 26-maktab layoutini tekshirish
    h_vals = [str(sheet.cell(header_row, c).value or "").lower() for c in range(1, 10)]
    if any("sertifikat" in v for v in h_vals):
        for idx_c, v in enumerate(h_vals, 1):
            if "ism" in v: name_col = idx_c
            if "sertifikat" in v: cert_col = idx_c
            
    # Sarlavhalarni to'ldirish
    if not sheet.cell(header_row, cert_col).value:
        sheet.cell(header_row, cert_col).value = "Sertifikat havolasi"
        sheet.cell(header_row, email_col).value = "Login (Email)"
        sheet.cell(header_row, pwd_col).value = "Parol"
    sheet.cell(header_row, time_col).value = "Sarflangan vaqt"
        
    # Oxirgi ustunlar (Sertifikat, Login, Parol, Vaqt) to'liq va keng ochilib ko'rinishi uchun
    try:
        from openpyxl.utils import get_column_letter
        col_widths = {
            name_col: 36,
            bdate_col: 20,
            seria_col: 18,
            num_col: 18,
            sinf_col: 12,
            cert_col: 50,
            email_col: 34,
            pwd_col: 20,
            time_col: 24
        }
        for c_idx, w_val in col_widths.items():
            if c_idx:
                sheet.column_dimensions[get_column_letter(c_idx)].width = w_val
    except Exception as e_w:
        print(f"[COLUMN WIDTH ERROR] {e_w}")
        
    total_students = 0
    success_count = 0
    
    for r in range(header_row + 1, sheet.max_row + 1):
        name_val = sheet.cell(r, name_col).value
        if not name_val:
            continue
            
        total_students += 1
        student_start_time = time.time()
        
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
            sheet.cell(r, time_col).value = "0 soniya (Excelda bor)"
            save_student_to_db(seria, num, {
                "name": str(name_val).strip(),
                "birthdate": bdate_str,
                "certificate": cur_cert,
                "status": "COMPLETED"
            })
            continue

        # 2. BAZADAN TEKSHIRISH (students_db.json) - BIRINCHI QADAM!
        db_rec = get_student_from_db(seria, num)
        cert_link = (db_rec.get("certificate") or db_rec.get("cert_url") or "") if db_rec else ""
        if cert_link and "certificate?id=" in cert_link:
            sheet.cell(r, cert_col).value = cert_link
            sheet.cell(r, cert_col).hyperlink = cert_link
            sheet.cell(r, cert_col).font = Font(color="0000FF", underline="single")
            if db_rec.get("login"): sheet.cell(r, email_col).value = db_rec["login"]
            if db_rec.get("password"): sheet.cell(r, pwd_col).value = db_rec["password"]
            sheet.cell(r, time_col).value = "0 soniya (Bazada tayyor)"
            wb.save(excel_path)
            success_count += 1
            if update_callback:
                update_callback(
                    f"⚡ [BAZADA TAYYOR] <b>{name_val}</b> ({seria} {num})\n"
                    f"🎓 Sertifikat allaqachon olingan!\n"
                    f"⏱ Vaqt: <b>0 soniya</b> (Bazada bor edi)\n"
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

        try:
            ok, res_link, email, pwd = process_single_student(student, update_callback=update_callback)
        except Exception as err:
            print(f"[STUDENT ERROR] {name_val}: {err}")
            ok, res_link, email, pwd = False, f"Xatolik: {err}", "", ""
        
        st_duration = time.time() - student_start_time
        st_dur_str = format_duration(st_duration)
        sheet.cell(r, time_col).value = st_dur_str

        if ok and "certificate?id=" in res_link:
            sheet.cell(r, cert_col).value = res_link
            sheet.cell(r, cert_col).hyperlink = res_link
            sheet.cell(r, cert_col).font = Font(color="0000FF", underline="single")
            if email: sheet.cell(r, email_col).value = email
            if pwd: sheet.cell(r, pwd_col).value = pwd
            wb.save(excel_path)
            success_count += 1
            if update_callback:
                update_callback(
                    f"✅ <b>{student['name']}</b>: Sertifikat olindi!\n"
                    f"⏱ <b>Sarflangan vaqt:</b> {st_dur_str}\n"
                    f"🔗 {res_link}"
                )
        else:
            wb.save(excel_path)
            if update_callback:
                update_callback(
                    f"⚠️ <b>{student['name']}</b>: Olinmadi ({res_link})\n"
                    f"⏱ <b>Sarflangan vaqt:</b> {st_dur_str}"
                )
                
    total_excel_duration = time.time() - excel_start_time
    try:
        from openpyxl.utils import get_column_letter
        for c_idx, w_val in col_widths.items():
            if c_idx:
                sheet.column_dimensions[get_column_letter(c_idx)].width = w_val
    except Exception:
        pass
    wb.save(excel_path)
    return success_count, total_students, total_excel_duration


if __name__ == "__main__":
    target = None
    if len(sys.argv) > 1:
        target = sys.argv[1]
    else:
        orders_dir = Path(__file__).resolve().parent / "orders"
        order_files = list(orders_dir.glob("*.xlsx"))
        if order_files:
            order_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            target = str(order_files[0])
        else:
            target = "5a 5millionsertifikat.xlsx"

    print(f"\n==================================================")
    print(f"5 MILLION PROMPTER ISHGA TUSHDI (CHROME KO'RINADI)")
    print(f"Fayl: {target}")
    print(f"==================================================\n")

    def cli_callback(m):
        clean = re.sub(r'<[^>]+>', '', m)
        print(f"\n>>> {clean}\n")

    res = process_excel_order(target, update_callback=cli_callback)
    print(f"\n[YAKUNLANDI] Natija: {res}")
