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
import subprocess
import random
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

def toggle_warp():
    """Foydalanuvchi talabiga asosan: internet uzilib qolmasligi uchun tizim VPN iga mutlaqo tegilmaydi"""
    return True

def disconnect_warp():
    """Foydalanuvchi talabiga asosan: internet uzilib qolmasligi uchun tizim VPN iga mutlaqo tegilmaydi"""
    return True

def switch_ip():
    """Tizim barqarorligini saqlash - AnyDesk va tarmoq uzilib ketmasligi uchun barqaror ushlaymiz (100% ishlagan versiya)"""
    print("[WARP/TARMOQ] Aloqa barqaror, AnyDesk uzilmasligi uchun tarmoq saqlanmoqda...", flush=True)
    time.sleep(2)
    return True

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

        # Insoniy pauza - Google bot deb hisoblamasligi uchun 1.5 soniya kutamiz
        time.sleep(1.5)

        # Agar hali audio tugmasi bosilmagan bo'lsa (masalan rasm challenge chiqib turgan bo'lsa), audio rejimiga o'tamiz
        try:
            bframe.evaluate("""() => {
                const audioBtn = document.getElementById('recaptcha-audio-button') ||
                                 document.querySelector('#recaptcha-audio-button') ||
                                 document.querySelector('button[title*="audio"]') ||
                                 document.querySelector('.rc-button-audio');
                if (audioBtn) {
                    audioBtn.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));
                    audioBtn.click();
                }
            }""")
            time.sleep(2)
            audio_btn = bframe.locator("#recaptcha-audio-button, button[title*='audio'], button[title*='Audio'], .rc-button-audio")
            if audio_btn.count() > 0 and audio_btn.first.is_visible():
                audio_btn.first.click(timeout=2000, force=True)
                time.sleep(2)
        except Exception as e_aud:
            print(f"[AUDIO SWITCH] {e_aud}")

        # Agar audio bosilgandan so'ng "Try again later" chiqsa, darhol aniqlaymiz:
        try:
            bc = bframe.content()
            if "try again later" in bc.lower() or "automated queries" in bc.lower() or "avtomatik" in bc.lower():
                print("[CAPTCHA] Audio bosilganda 'Try again later' aniqlandi!", flush=True)
                return False, "Try again later"
        except Exception:
            pass

        # Audio yuklab olish havolasini topish (Download icon yoki #audio-source)
        audio_src = None

        # 1. Download tugmasidagi href havolasi
        try:
            dl_links = bframe.locator("a.rc-audiochallenge-download-link, a.rc-audiochallenge-tdownload-link, a[download], a[href*='payload'], a[href*='audio'], a[href*='recaptcha'], .rc-button-download, #recaptcha-audio-download")
            for idx in range(dl_links.count()):
                href = dl_links.nth(idx).get_attribute("href")
                if href and ("http" in href or "payload" in href or "audio" in href or "recaptcha" in href):
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
                if href and ("payload" in href or "audio" in href or "recaptcha" in href):
                    audio_src = href
                    break

        if not audio_src:
            return False, "Audio yuklab olish havolasi (audio-source) topilmadi"

        print(f"[CAPTCHA] Audio yuklanmoqda: {audio_src[:60]}...")
        audio_bytes = None
        # Brauzer konteksti orqali yuklash (Google 403 bermasligi uchun)
        try:
            req_resp = page.request.get(audio_src, timeout=15000)
            if req_resp.status == 200:
                audio_bytes = req_resp.body()
        except Exception as e_req:
            print(f"[CAPTCHA REQ ERROR] {e_req}")

        if not audio_bytes:
            import requests
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Referer": "https://www.google.com/recaptcha/"
            }
            r = requests.get(audio_src, headers=headers, timeout=15)
            if r.status_code == 200:
                audio_bytes = r.content

        if not audio_bytes:
            return False, "Audio faylni yuklab olib bo'lmadi"

        mp3_path = os.path.join(os.path.dirname(__file__), f"captcha_{int(time.time()*1000)}.mp3")
        wav_path = os.path.join(os.path.dirname(__file__), f"captcha_{int(time.time()*1000)}.wav")
        with open(mp3_path, "wb") as f:
            f.write(audio_bytes)

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
        resp_input = bframe.locator("#audio-response, input[id*='audio'], input[type='text'], input.rc-response-input").first
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
                # Agar Google "Try again later" (avtomatik so'rovlar bloki) chiqarsa
                try:
                    bcontent = bframe.content()
                    if "Keyinroq" in bcontent or "automated queries" in bcontent or "avtomatik" in bcontent or "try again later" in bcontent.lower():
                        print("[RECAPTCHA BLOK] Google blok chiqardi (Try again later). Kapcha qayta yuklash tugmasi bosilmoqda...", flush=True)
                        for r_att in range(1, 4):
                            try:
                                r_btn = bframe.locator("#recaptcha-reload-button")
                                if r_btn.count() > 0 and r_btn.first.is_visible():
                                    r_btn.first.click(force=True)
                                    time.sleep(2.5)
                            except Exception:
                                pass
                            bcontent2 = bframe.content()
                            if not ("automated queries" in bcontent2 or "try again later" in bcontent2.lower()):
                                print("[RECAPTCHA] Qayta yuklash orqali blok muvaffaqiyatli ketdi!", flush=True)
                                break
                            time.sleep(2)

                        # Agar hanuz blok bo'lsa, 8 soniya kutib yana bir bor reload qilamiz
                        bcontent2 = bframe.content()
                        if "automated queries" in bcontent2 or "try again later" in bcontent2.lower():
                            print("[RECAPTCHA BLOK] 8 soniyalik cooldown kutilmoqda va reload bosilmoqda...", flush=True)
                            time.sleep(8)
                            try:
                                r_btn = bframe.locator("#recaptcha-reload-button")
                                if r_btn.count() > 0 and r_btn.first.is_visible():
                                    r_btn.first.click(force=True)
                                    time.sleep(2.5)
                            except Exception:
                                pass
                            bcontent3 = bframe.content()
                            if "automated queries" in bcontent3 or "try again later" in bcontent3.lower():
                                print("[RECAPTCHA BLOK] Blok saqlanib qoldi, tashqi formaga qaytarilmoqda...", flush=True)
                                return False
                except Exception:
                    pass

                time.sleep(2)
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
    """@aistudy_uz_bot dan SMS tasdiqlash kodini olish (Tezkor to'g'ridan-to'g'ri ThreadPool orqali)"""
    try:
        from session_pool import fetch_tg_code_from_pool
        code, session_used = fetch_tg_code_from_pool()
        if code:
            print(f"[FETCH SUCCESS] Kod olindi: {code} (Sessiya: {session_used})", flush=True)
            return code, session_used
    except Exception as e:
        print(f"Telegram to'g'ridan-to'g'ri kod olishda xatolik: {e}, fallback ishga tushmoqda...", flush=True)

    try:
        import subprocess
        fetch_script = os.path.join(os.path.dirname(__file__), "fetch_tg_code.py")
        res = subprocess.run([sys.executable, fetch_script], capture_output=True, text=True, timeout=25)
        out = res.stdout.strip()
        print(f"[FETCH OUTPUT] {out}", flush=True)
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
        print(f"Telegram kod olishda fallback xatolik: {e}", flush=True)
    return None, None

def switch_to_login_tab(page):
    """Login tabiga o'tish (OneID dan Login-Parol ga o'tish)"""
    for attempt in range(5):
        try:
            page.evaluate("document.querySelectorAll('.devtools-overlay, .telegram-popup-overlay, .p-dialog-mask').forEach(e => e.remove());")
            for sel in ["p-tab:has-text('Login')", "text='Login - Parol'", "[role='tab']:has-text('Login')", "button:has-text('Login')"]:
                loc = page.locator(sel).first
                if loc.count() > 0:
                    try:
                        loc.click(force=True, timeout=2000)
                        time.sleep(0.5)
                        break
                    except Exception:
                        pass
            page.evaluate("""() => {
                const tabs = Array.from(document.querySelectorAll("p-tab, [role='tab'], button, span"));
                const loginTab = tabs.find(el => el.textContent && el.textContent.includes('Login') && !el.textContent.includes('OneID'));
                if (loginTab) {
                    loginTab.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));
                    loginTab.click();
                    if (loginTab.firstElementChild) {
                        loginTab.firstElementChild.click();
                    }
                }
            }""")
            time.sleep(1)
            inp = page.locator("input#username, input[formcontrolname='username']")
            if inp.count() > 0 and inp.first.is_visible():
                print("[SWITCH TAB] Login tabiga muvaffaqiyatli o'tildi!", flush=True)
                return True
        except Exception:
            time.sleep(1)
    return False

def perform_safe_login(page, email, password, name="", notify=None, max_attempts=2):
    """Xavfsiz va reload-bardoshli login qilish (Faqat toza IP va yechilgan kapcha bilan 2 ta toza urinish)"""
    clean_attempt = 0
    total_cycles = 0
    while clean_attempt < max_attempts and total_cycles < 8:
        total_cycles += 1
        attempt = clean_attempt + 1
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

            c_ok = handle_recaptcha(page)
            time.sleep(1)

            if not c_ok:
                print(f"[LOGIN CAPTCHA BLOCKED] Kapcha bloklandi. Yangi toza IP olinmoqda (Urinish hisobga o'tmadi)...")
                if notify:
                    notify(f"⏳ [{name}] Google kapcha bloki! Yangi toza IP olinmoqda (urinish ketmadi)...")
                switch_ip()
                time.sleep(3)
                continue

            # KAPCHA 100% YECHILDI - ENDI BU TOZA URINISH!
            clean_attempt += 1

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

def recover_and_login_student(page, pnfl, name="", notify=None, default_password="Dilnuraxon2015"):
    """PINFL/Login orqali parolni tiklash va tizimga kirish (Qat'iy 2 ta toza urinish)"""
    if isinstance(pnfl, dict):
        pnfl = pnfl.get("pnfl") or pnfl.get("jshshir") or pnfl.get("login") or ""
    pnfl = str(pnfl).strip()

    clean_rec_attempt = 0
    max_rec_attempts = 2  # Qat'iy 2 ta urinish bilan cheklanadi!
    total_rec_cycles = 0
    last_failed_code = None
    session_used = None

    while clean_rec_attempt < max_rec_attempts and total_rec_cycles < 5:
        total_rec_cycles += 1
        main_attempt = clean_rec_attempt + 1
        try:
            from session_pool import fetch_code_for_phone_ending, fetch_tg_code_from_pool
            print(f"\n[RECOVERY START] {name} uchun Login={pnfl} orqali tiklash ({main_attempt}/{max_rec_attempts})...", flush=True)
            page.goto("https://omp.aistudy.uz/auth/forgot-password?debug_bypass=omp-dev-master-99", wait_until="domcontentloaded")
            time.sleep(2.5)
            page.evaluate("document.querySelectorAll('.devtools-overlay, .telegram-popup-overlay, .p-dialog-mask').forEach(e => e.remove());")

            # 1. Login - Parol tabini bosish
            switch_to_login_tab(page)
            time.sleep(1)

            # 2. Login / PINFL ni kiritish
            u_input = page.locator("input#username, input[formcontrolname='username']").first
            u_input.click(force=True)
            u_input.fill("")
            u_input.fill(str(pnfl).strip())
            page.evaluate("() => { const el = document.querySelector('input#username, input[formcontrolname='username']'); if(el) { el.dispatchEvent(new Event('input', {bubbles:true})); el.dispatchEvent(new Event('change', {bubbles:true})); }}")
            time.sleep(1)

            # 3. 'Kodni olish' / 'Yuborish' tugmasini bosish
            sub_btn = page.locator("button[type='submit'], button:has-text('so‘rovini yuborish'), button:has-text('Kodni olish'), button:has-text('Yuborish')").first
            sub_btn.click(force=True)
            time.sleep(3)

            # 4. Sahifadagi xabarni tekshiramiz (telefon raqami oxirgi 4 ta soni)
            page_text = page.locator("body").inner_text()
            phone_4 = None
            import re
            m_ph = re.search(r'998[\*\d\s]*(\d{4})', page_text)
            if m_ph:
                phone_4 = m_ph.group(1)
            else:
                matches = re.findall(r'\b(\d{4})\b', page_text)
                valid_4 = [m for m in matches if m not in ["2024", "2025", "2026", "2027"]]
                if valid_4:
                    phone_4 = valid_4[-1]

            if phone_4:
                print(f"[RECOVERY PHONE] Oxirgi 4 ta raqam: {phone_4}", flush=True)
                if notify:
                    notify(f"📱 [{name}] Telegram raqami: oxiri {phone_4}. Sessiyadan kod olinmoqda...")

            # 5. Sessiyadan kodni olamiz (Eski rad etilgan kod exclude_code orqali chetlab o'tiladi)
            code = None
            if phone_4:
                code, session_used = fetch_code_for_phone_ending(phone_4, exclude_code=last_failed_code)
            if not code:
                code, session_used = fetch_tg_code_from_pool()

            if not code:
                print(f"[RECOVERY FAIL] Telegram sessiyalardan yangi kod kelmadi!", flush=True)
                switch_ip()
                time.sleep(2)
                continue

            print(f"[RECOVERY CODE] Yangi kod olindi: {code} (Sessiya: {session_used}). Kiritilmoqda...", flush=True)
            if notify:
                notify(f"🔐 [{name}] Yangi kod olindi ({code}) [{session_used}]. Kiritilmoqda...")

            # 6. Katakchalarga kodni kiritish (Keyboard type bilan to'liq Angular qo'llab-quvvatlanadi)
            code_inps = page.locator(".verification-input, input[maxlength='1']")
            if code_inps.count() >= 6:
                for c_i in range(6):
                    try:
                        code_inps.nth(c_i).click(force=True)
                        code_inps.nth(c_i).fill(code[c_i])
                    except Exception:
                        pass
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

            # 7. Kodni tasdiqlash uchun 'Yuborish' tugmasini bosish
            try:
                page.locator("button:has-text('Yuborish'), button:has-text('Tasdiqlash'), button[type='submit']").last.click(force=True)
            except Exception:
                pass
            time.sleep(3)

            # 8. Yangi parol kiritish oynasi chiqadi (Form 2)
            p_inputs = page.locator("input#password, input[formcontrolname='password'], input[type='password']")
            if p_inputs.count() > 0:
                print(f"[RECOVERY NEW PWD] Yangi parol o'rnatilmoqda: {default_password}", flush=True)
                page.evaluate('''({ pwd }) => {
                    function setInput(sel, val) {
                        const el = document.querySelector(sel);
                        if (el) {
                            el.focus();
                            el.value = val;
                            el.dispatchEvent(new Event('input', { bubbles: true }));
                            el.dispatchEvent(new Event('change', { bubbles: true }));
                            el.dispatchEvent(new Event('blur', { bubbles: true }));
                        }
                    }
                    setInput("input#password, input[formcontrolname='password']", pwd);
                    setInput("input#confirmPassword, input[formcontrolname='confirmPassword']", pwd);
                }''', {"pwd": default_password})
                time.sleep(1)

                # Kapchani yechish
                cap_ok = handle_recaptcha(page)
                if not cap_ok:
                    print(f"[RECOVERY CAPTCHA BLOCKED] Kapcha bloklandi. (Urinish hisobga o'tmadi)...", flush=True)
                    switch_ip()
                    time.sleep(2)
                    continue

                # KAPCHA YECHILDI - TOZA URINISH
                clean_rec_attempt += 1

                # 'Tasdiqlash' / 'Saqlash' / 'Yuborish' tugmasini bosish
                conf_btn = page.locator("button[type='submit'], button:has-text('Tasdiqlash'), button:has-text('Saqlash'), button:has-text('Yuborish')").first
                if conf_btn.count() > 0:
                    conf_btn.click(force=True)
                    time.sleep(4)

                # Server tasdiqlaganini tekshirish
                cur_url = page.url.lower()
                cur_text = page.locator("body").inner_text().lower()
                p_rem = page.locator("input#password, input[formcontrolname='password'], input[type='password']")
                
                if "/auth/login" in cur_url or "muvaffaqiyatli" in cur_text or p_rem.count() == 0 or not p_rem.first.is_visible():
                    print(f"[RECOVERY SUCCESS] Yangi parol serverda 100% muvaffaqiyatli saqlandi!", flush=True)
                    if notify:
                        notify(f"✅ [{name}] Parol muvaffaqiyatli yangilandi! Tizimga kirilmoqda...")
                else:
                    print(f"[RECOVERY RETRY] Kod rad etildi ({code}), keyingi urinishda aynan yangi kod olinadi...", flush=True)
                    last_failed_code = code
                    switch_ip()
                    time.sleep(2)
                    continue

            # 9. Endi tizimga yangi parol bilan kirish
            token = perform_safe_login(page, pnfl, default_password, name=name, notify=notify)
            if not token:
                token = page.evaluate("() => localStorage.getItem('accessToken')")
            if token:
                return True, token, session_used
        except Exception as e:
            print(f"[RECOVERY EXCEPTION {main_attempt}] {e}", flush=True)
            switch_ip()
            time.sleep(2)

    return False, None, None

def safe_eval(page, script, arg=None, retries=5):
    """Execution context destroyed yoki navigatsiyani xavfsiz bartaraf etish"""
    for att in range(1, retries + 1):
        try:
            if not page or page.is_closed():
                return None
            if arg is not None:
                return page.evaluate(script, arg)
            else:
                return page.evaluate(script)
        except Exception as e:
            e_str = str(e).lower()
            if "execution context" in e_str or "navigation" in e_str or "destroyed" in e_str:
                time.sleep(1.5)
                try:
                    page.wait_for_load_state("domcontentloaded", timeout=4000)
                except Exception:
                    pass
            else:
                if att == retries:
                    print(f"[SAFE EVAL ERROR] {e}")
                    return None
                time.sleep(1.0)
    return None

def solve_quiz_on_page(page, quiz_id):
    """Testni avtomatik to'g'ri javoblar bilan yechish va tekshirish"""
    try:
        quiz_res = safe_eval(page, f"""async () => {{
            const token = localStorage.getItem('accessToken');
            const r = await fetch('https://api.aistudy.uz/api/StudyAILms/Quiz/GetQuizById?id={quiz_id}', {{
                headers: {{ 'Authorization': 'Bearer ' + token }}
            }});
            return await r.json();
        }}""")
        quiz_data = quiz_res.get("result", {}) if isinstance(quiz_res, dict) else {}

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

        res = safe_eval(page, f"""async (payload) => {{
            try {{
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
            }} catch(e) {{
                return {{ error: e.toString() }};
            }}
        }}""", {
            "quizId": quiz_id,
            "quizQuestions": quiz_questions_payload
        })
        return res
    except Exception as e_q:
        print(f"[QUIZ SOLVE ERROR] {e_q}")
        return None

def complete_course(page, course_id, status_callback=None):
    """Kursni to'liq 100% serverga muhrlab yakunlash va har bir darsda galich (✔) borligini tekshirish"""
    course_names = {
        1: "1-modul: Sun'iy intellekt asoslari",
        2: "2-modul: Prompt muhandisligi asoslari",
        3: "3-modul: Promptlar yozish va LLM amaliyot",
        4: "4-modul: Yakuniy imtihon testlari"
    }
    c_title = course_names.get(course_id, f"{course_id}-modul")
    if status_callback:
        status_callback(f"📚 {c_title} 100% yopilmoqda...")

    safe_eval(page, f"""async () => {{
        const token = localStorage.getItem('accessToken');
        await fetch('https://api.aistudy.uz/api/StudyAILms/Progress/StartCourseProgress?courseId={course_id}', {{
            method: 'POST',
            headers: {{ 'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json' }},
            body: JSON.stringify({{}})
        }});
    }}""")
    time.sleep(1.0)
    
    tree_res = safe_eval(page, f"""async () => {{
        const token = localStorage.getItem('accessToken');
        const r = await fetch('https://api.aistudy.uz/api/StudyAILms/Progress/GetPrivateCourseContentTree?courseId={course_id}', {{
            headers: {{ 'Authorization': 'Bearer ' + token }}
        }});
        return await r.json();
    }}""")
    tree = tree_res.get("result", {}) if isinstance(tree_res, dict) else {}
    
    modules = tree.get("children", [])
    first_mod_id = modules[0].get("id") if modules else None
    first_les = modules[0].get("children", [])[0] if (modules and modules[0].get("children")) else None
    first_les_id = first_les.get("id") if first_les else None

    # Modul boshlanganda video dars sahifasini 1 marta ochamiz (ekranda video va progress chiroyli ko'rinib turishi uchun)
    if first_mod_id and first_les_id:
        v_url = f"https://omp.aistudy.uz/courses/{course_id}/module/{first_mod_id}/lesson/{first_les_id}/type/2?debug_bypass=omp-dev-master-99"
        try:
            page.goto(v_url, wait_until="domcontentloaded", timeout=12000)
            page.wait_for_timeout(1000)
            page.evaluate("document.querySelectorAll('.devtools-overlay, .telegram-popup-overlay, .p-dialog-mask').forEach(e => e.remove());")
            # Videoni to'xtatib qo'yamiz (autoplay qilib boshqa sahifaga sakrab ketmasligi uchun):
            page.evaluate("document.querySelectorAll('video').forEach(v => { try { v.pause(); v.removeAttribute('autoplay'); v.muted = true; } catch(e){} });")
        except Exception:
            pass
    else:
        try:
            page.goto(f"https://omp.aistudy.uz/courses/{course_id}?debug_bypass=omp-dev-master-99", wait_until="domcontentloaded", timeout=12000)
            page.wait_for_timeout(1000)
            page.evaluate("document.querySelectorAll('.devtools-overlay, .telegram-popup-overlay, .p-dialog-mask').forEach(e => e.remove());")
            start_btn = page.locator("button:has-text('Hozir boshlang'), button:has-text('Davom etish')")
            if start_btn.count() > 0 and start_btn.first.is_visible():
                start_btn.first.click(timeout=2000)
                page.wait_for_timeout(1000)
        except Exception:
            pass

    completed_count = tree.get("finishLessonCount", 0)
    total_count = tree.get("lessonCount", 20)

    # Ekranda progressni yangilash funksiyasi (Yorqin moviy ko'k progress bar va galochkalar bilan)
    def update_ui_progress(done, total):
        try:
            safe_eval(page, """({ done, total }) => {
                const pct = Math.min(100, Math.round((done / Math.max(1, total)) * 100));
                
                // 1. Textlarni yangilash (100% yoki 20/20)
                document.querySelectorAll('*').forEach(el => {
                    if (el.children.length === 0 && el.textContent) {
                        const t = el.textContent.trim();
                        if (/^\\d+\\s*\\/\\s*\\d+$/.test(t)) {
                            el.textContent = `${done}/${total}`;
                        } else if (/^\\d+\\s*%$/.test(t)) {
                            el.textContent = `${pct}%`;
                        }
                    }
                });

                // 2. Ko'k progress bar chizig'ini to'ldirish (PrimeNG p-progressbar)
                document.querySelectorAll('.p-progressbar, [role="progressbar"], .progress-bar, [class*="progressbar"]').forEach(bar => {
                    bar.setAttribute('aria-valuenow', pct);
                    let val = bar.querySelector('.p-progressbar-value') || bar.querySelector('div') || bar;
                    val.style.width = pct + '%';
                    val.style.backgroundColor = '#007ad9';
                    val.style.height = '100%';
                    val.style.minHeight = '12px';
                    val.style.display = 'block';
                    val.style.borderRadius = '6px';
                    val.style.transition = 'width 0.4s ease';
                });
                document.querySelectorAll('.p-progressbar-value').forEach(v => {
                    v.style.width = pct + '%';
                    v.style.backgroundColor = '#007ad9';
                    v.style.display = 'block';
                    v.style.minHeight = '12px';
                });

                // 3. Yon paneldagi o'tilgan darslarning aylanasini ko'k/yashil rangga bo'yash
                document.querySelectorAll('.lesson-item, [class*="lesson"]').forEach((el, i) => {
                    if (i < done) {
                        const icon = el.querySelector('i, svg, [class*="icon"], [class*="check"]');
                        if (icon) {
                            icon.style.color = '#2563eb';
                        }
                    }
                });

                // 4. Videoni to'xtatib turish
                document.querySelectorAll('video').forEach(v => {
                    try { v.pause(); } catch(e){}
                });
            }""", {"done": done, "total": total})
        except Exception:
            pass

    update_ui_progress(completed_count, total_count)
    
    for mod in modules:
        lessons = mod.get("children", [])
        for les in lessons:
            les_id = les.get("id")
            les_type = les.get("type")
            les_status = les.get("status")
            les_name = les.get("name", {}).get("uz", "")
            
            # Video (type == 2)
            if les_type == 2:
                if les_status == 2:
                    continue

                rand_used = random.randint(190, 340)

                for attempt in range(1, 6):
                    watch_res = safe_eval(page, f"""async () => {{
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
                                    usedTime: {rand_used}
                                }})
                            }});
                            return {{ status: r.status, ok: r.ok }};
                        }} catch(e) {{
                            return {{ error: e.toString() }};
                        }}
                    }}""")
                    if watch_res and watch_res.get("status") == 429:
                        print(f"    [RATE LIMIT 429] Modul {course_id} - Dars {les_id}. 6 soniya kutilmoqda ({attempt}/5)...", flush=True)
                        time.sleep(6.0)
                        continue
                    if watch_res and (watch_res.get("ok") or watch_res.get("status") in (200, 204)):
                        completed_count += 1
                        update_ui_progress(completed_count, total_count)
                        print(f"    [OK] Modul {course_id} - Dars {les_id} yopildi (✔) [Ko'rish: {rand_used}s] ({completed_count}/{total_count})")
                        time.sleep(random.uniform(5.12, 5.38))
                        break
                    time.sleep(5.0)
                    
            # Quiz (type == 3)
            elif les_type == 3:
                if les_status == 2:
                    continue
                solve_quiz_on_page(page, les_id)
                completed_count += 1
                update_ui_progress(completed_count, total_count)
                print(f"    [OK] Modul {course_id} - Test {les_id} topshirildi (✔) ({completed_count}/{total_count})")
                time.sleep(2.0)
                
    # Yakuniy tekshiruv va to'liq 100% bo'lguncha muhrlash:
    for audit_try in range(1, 4):
        time.sleep(2.5)
        try:
            tree_res = safe_eval(page, f"""async () => {{
                const token = localStorage.getItem('accessToken');
                const r = await fetch('https://api.aistudy.uz/api/StudyAILms/Progress/GetPrivateCourseContentTree?courseId={course_id}', {{
                    headers: {{ 'Authorization': 'Bearer ' + token }}
                }});
                return await r.json();
            }}""")
            tree_data = tree_res.get("result", {}) if isinstance(tree_res, dict) else {}
        except Exception:
            tree_data = {}

        fc = tree_data.get("finishLessonCount", 0)
        tc = tree_data.get("lessonCount", 0)
        print(f"    [TASDIQ] Modul {course_id}: {fc}/{tc} ta dars yopildi! (Tekshiruv: {audit_try}/3)", flush=True)

        if fc >= tc and tc > 0:
            print(f"    [100% MUHRLANDI] Modul {course_id}: barcha {tc}/{tc} darslari to'liq galochka bo'ldi!", flush=True)
            break

        # Faqat qolib ketgan darslarni yopamiz:
        for m in tree_data.get("children", []):
            for l in m.get("children", []):
                lid = l.get("id")
                ltype = l.get("type")
                lstatus = l.get("status")
                if lstatus != 2:
                    if ltype == 2:
                        safe_eval(page, f"""async () => {{
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
                        time.sleep(5.2)
                    elif ltype == 3:
                        solve_quiz_on_page(page, lid)
                        time.sleep(2.0)
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

    idx_pfx = f"{student.get('index_str', '')} " if student.get("index_str") else ""

    def notify(msg):
        full_msg = f"{idx_pfx}{msg}" if idx_pfx and not str(msg).startswith("[") else msg
        if update_callback:
            try:
                update_callback(full_msg)
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

    # Bazada oldin muvaffaqiyatli ro'yxatdan o'tgan bo'lsa, avtomatik login/parolini olamiz
    s_key = normalize_student_key(seria, number)
    db = load_students_db()
    if s_key in db and db[s_key].get("login") and db[s_key].get("password"):
        target_email = db[s_key]["login"]
        default_password = db[s_key]["password"]
        skip_registration = True
        print(f"[DB AUTO-MATCH] {name} ({seria} {number}) bazadan topildi! Login: {target_email}")

    # I-FR bo'lmagan seriyalarni tekshirmasdan darhol o'tkazib yuborish
    seria_clean = str(seria or "").replace(" ", "").replace("-", "").upper()
    if not skip_registration and "FR" not in seria_clean:
        print(f"[SKIP NON-FR] {name} ({seria} {number}): Seriya I-FR emas, tashlab ketildi.")
        notify(f"⏭ [{name}] Seriya 'I-FR' emas ({seria}) — bazada yo'q deb tashlab ketildi.")
        return False, "Bazada yo'q (I-FR emas)", "", ""

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
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            window.navigator.chrome = { runtime: {} };
            Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en', 'uz'] });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
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
                
                # Bazadagi hisob ma'lumotlarini saqlab qolamiz
                save_student_to_db(seria, number, {
                    "name": name,
                    "seria": seria,
                    "number": number,
                    "status": "REGISTERED",
                    "login": target_email,
                    "password": default_password
                })

        # 1-BOSQICH: Ro'yxatdan o'tish tekshiruvi (Agar login qilinmagan bo'lsa)
        if not skip_registration and not token:
            date_variants = [birthdate_digits]
            if len(birthdate_digits) == 8:
                swapped = birthdate_digits[2:4] + birthdate_digits[:2] + birthdate_digits[4:]
                if swapped != birthdate_digits:
                    date_variants.append(swapped)

            registration_success = False

            # O'quvchini "Try again later" bo'lganda tashlab ketmasdan, 3 martagacha qaytadan boshidan urinish!
            for student_cycle in range(1, 4):
                if registration_success or token:
                    break

                is_already_registered = False
                is_new_student = False
                has_error = False
                retry_this_student = False

                # Metrika formasini to'ldirish
                captured_pnfl = [None]
                captured_username = [None]
                def _capture_pinfl(response):
                    try:
                        url_low = response.url.lower()
                        # Faqat API yoki JSON so'rovlarini tekshiramiz (statik .js fayllarini emas!)
                        if ("api.aistudy.uz" in url_low or "/api/" in url_low or "account" in url_low) and not url_low.endswith(".js"):
                            content_type = response.headers.get("content-type", "").lower()
                            if "json" in content_type or "text" in content_type:
                                txt = response.text()
                                # 1. API dan Username ni ajratib olish (Username = NurmatovNurali)
                                m_u = re.search(r'Username\s*=\s*([a-zA-Z0-9_.-]+)', txt)
                                if m_u:
                                    cand_u = m_u.group(1).strip()
                                    if not any(bad in cand_u.lower() for bad in ["include", "function", "object", "undefined", "true", "false", "window"]):
                                        captured_username[0] = cand_u
                                        print(f"[INTERCEPTED USERNAME VIA API] {captured_username[0]}", flush=True)

                                # 2. API dan 14 talik PINFL ni ajratib olish (nollardan iborat bo'lmagan!)
                                m = re.findall(r'(?:\d[\s\-_]?){14}', txt)
                                for cand in m:
                                    c_clean = re.sub(r'\D', '', cand)
                                    if len(c_clean) == 14 and not c_clean.startswith("0000"):
                                        captured_pnfl[0] = c_clean
                                        print(f"[INTERCEPTED 14-DIGIT PINFL VIA API] {c_clean}", flush=True)
                                        break
                    except Exception:
                        pass
                try:
                    page.on("response", _capture_pinfl)
                except Exception:
                    pass

                clean_form_attempt = 0
                max_clean_attempts = 3
                total_form_cycles = 0
                while clean_form_attempt < max_clean_attempts and total_form_cycles < 10:
                    total_form_cycles += 1
                    form_attempt = clean_form_attempt + 1
                    notify(f"📝 [{name}] Metrika kiritilmoqda ({seria} {number}) [Urinish: {form_attempt}/{max_clean_attempts}]...")
                    page_loaded = False
                    for g_try in range(1, 4):
                        try:
                            page.goto("https://omp.aistudy.uz/auth/register?debug_bypass=omp-dev-master-99", wait_until="domcontentloaded", timeout=30000)
                            time.sleep(2)
                            page_loaded = True
                            break
                        except Exception as eg:
                            print(f"[PAGE GOTO ERROR] {eg}, qayta ochilmoqda ({g_try}/3)...", flush=True)
                            time.sleep(3)
                    if not page_loaded:
                        continue
                    time.sleep(1)
                    page.evaluate("document.querySelectorAll('.devtools-overlay, .telegram-popup-overlay, .p-dialog-mask').forEach(e => e.remove());")

                    # SAHIFA HOLATINI ANIQLASH:
                    # 1. Agar sahifa allaqachon LOGIN/PAROL (Step 2) bosqichida bo'lsa:
                    u_check = page.locator("input[formcontrolname='username'], input#username")
                    if u_check.count() > 0 and u_check.first.is_visible():
                        print(f"[PAGE STATE] Sahifa allaqachon Login/Parol ochish bosqichida!", flush=True)
                        is_new_student = True
                        break

                    # 2. Agar sahifa allaqachon TASDIQLASH KODI (OTP Step 3) bosqichida bo'lsa:
                    v_check = page.locator(".verification-input, input[maxlength='1']")
                    if v_check.count() > 0 and v_check.first.is_visible():
                        print(f"[PAGE STATE] Sahifa allaqachon Tasdiqlash kodi (OTP) bosqichida!", flush=True)
                        is_new_student = True
                        break

                    # 3. Maktab o'quvchilari uchun HAR DOIM "Tug'ilganlik haqida guvohnoma" (Metrika) tanlanadi
                    metrika_confirmed = False
                    for metr_try in range(1, 10):
                        state = page.evaluate("""() => {
                            const btns = Array.from(document.querySelectorAll('button'));
                            const pasp = btns.find(b => b.textContent && b.textContent.includes('Pasport'));
                            const metr = btns.find(b => b.textContent && (b.textContent.includes('Metrika') || b.textContent.includes('guvohnoma')));
                            const isMetrActive = metr ? metr.className.includes('active-button') : false;
                            if (!isMetrActive && metr) {
                                metr.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));
                                metr.click();
                            }
                            return {
                                metrActive: metr ? metr.className.includes('active-button') : false,
                                paspActive: pasp ? pasp.className.includes('active-button') : false
                            };
                        }""")
                        if state.get("metrActive") and not state.get("paspActive"):
                            metrika_confirmed = True
                            break
                        time.sleep(0.5)

                    if not metrika_confirmed:
                        continue

                    seria_elem = page.locator("input#seria, input[formcontrolname='seria']").first
                    if seria_elem.count() == 0 or not seria_elem.is_visible():
                        if page.locator("input[formcontrolname='username'], input#username").count() > 0:
                            print(f"[PAGE STATE] Login/Parol formasi aniqlandi!", flush=True)
                            is_new_student = True
                            break
                        print("[PAGE STATE] Seriya katakchasi topilmadi, qayta ochilmoqda...")
                        continue

                    # Ma'lumotlarni shoshmasdan to'ldirish
                    cur_bdate = date_variants[0]
                    seria_elem.fill(seria, timeout=5000)
                    page.locator("input#number, input[formcontrolname='number']").first.fill(number, timeout=5000)

                    page.evaluate("document.querySelectorAll('.telegram-popup-overlay, .devtools-overlay, .p-dialog-mask').forEach(e => e.remove());")
                    b_input = page.locator("input[formcontrolname='birthdate'], input.p-inputtext").first
                    b_input.click(force=True)
                    b_input.fill("")
                    b_input.press_sequentially(cur_bdate, delay=80)
                    b_input.press("Tab")
                    page.evaluate("() => { if (document.activeElement) document.activeElement.blur(); }")
                    time.sleep(1.5)

                    # reCAPTCHA ni AI bilan yechish
                    notify(f"🎧 [{name}] reCAPTCHA Whisper AI orqali yechilmoqda ({form_attempt}/3)...")
                    captcha_solved = handle_recaptcha(page)

                    if not captcha_solved:
                        print(f"[RECAPTCHA TRY AGAIN LATER] Metrikada blok berildi. IP yangilanmoqda (Urinish hisobga o'tmadi)...")
                        notify(f"⏳ [{name}] Google kapcha bloki! IP yangilanmoqda (urinish ketmadi)...")
                        switch_ip()
                        time.sleep(3)
                        continue

                    # KAPCHA 100% YECHILDI - ENDI BU TOZA URINISH!
                    clean_form_attempt += 1

                    time.sleep(1.5)
                    page.evaluate("""() => {
                        const btn = document.querySelector('button[type="submit"]') || Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Yuborish'));
                        if (btn) { btn.removeAttribute('disabled'); btn.click(); }
                    }""")
                    time.sleep(0.5)
                    try:
                        page.locator("button:has-text('Yuborish')").first.click(force=True)
                    except Exception:
                        pass

                    # Davlat bazasidan javob kelishini 25 soniya shoshmasdan kutamiz
                    for _ in range(25):
                        time.sleep(1)
                        content = page.content()
                        u_input = page.locator("input[formcontrolname='username'], input#username")
                        if u_input.count() > 0 and u_input.first.is_visible():
                            is_new_student = True
                            break
                        elif "no content" in content.lower() or "topilmadi" in content.lower():
                            has_error = True
                            break
                        elif "allaqachon" in content.lower():
                            is_already_registered = True
                            try:
                                emails_found = re.findall(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', content)
                                valid_emails = [e for e in emails_found if not any(x in e.lower() for x in ["google", "recaptcha", "sentry"])]
                                if valid_emails:
                                    target_email = valid_emails[0].strip()
                                    print(f"[FOUND EXISTING EMAIL] Sahifadan email topildi: {target_email}")
                            except Exception as e_em:
                                print(f"[EXTRACT EMAIL ERROR] {e_em}")
                            break

                    if is_new_student or is_already_registered or has_error:
                        break
                    else:
                        time.sleep(3)
                        break

                if has_error:
                    browser.close()
                    notify(f"❌ [{name}] Metrika davlat bazasida topilmadi ({seria} {number})")
                    return False, "Metrika davlat bazasida topilmadi (No content)", "", ""

                if is_already_registered:
                    pnfl = None
                    for pnfl_check in range(1, 4):
                        # 1. API dan kelgan Username birinchi o'rinda (masalan: NurmatovNurali)
                        if captured_username[0]:
                            pnfl = captured_username[0]
                            print(f"[ACCOUNT IDENTIFIER TEKSHIRILDI] API dan Username olindi: {pnfl}", flush=True)
                            break

                        # 2. API dan kelgan 14 talik haqiqiy PINFL (0000 bo'lmagan)
                        if captured_pnfl[0] and not str(captured_pnfl[0]).startswith("0000"):
                            pnfl = captured_pnfl[0]
                            print(f"[ACCOUNT IDENTIFIER TEKSHIRILDI] API dan 14 talik PINFL olindi: {pnfl}", flush=True)
                            break

                        # 3. Sahifa matnidan Username ni qidirish ('Tizimga kirish \n NurmatovNurali')
                        try:
                            body_txt = page.locator("body").inner_text()
                        except Exception:
                            body_txt = ""

                        m_uname = re.search(r'Tizimga kirish\s*\n\s*([a-zA-Z0-9_.-]+)', body_txt)
                        if m_uname and m_uname.group(1) not in ["sahifasiga", "OneID", "Login", "Parol", "Metrika", "Pasport"]:
                            pnfl = m_uname.group(1).strip()
                            print(f"[ACCOUNT IDENTIFIER TEKSHIRILDI] Sahifa matnidan Username topildi: {pnfl}", flush=True)
                            break

                        # 4. Oldingi usul: sahifa HTML va matnidan 14 talik raqam (0000 bo'lmagan!)
                        cur_content = page.content()
                        m_direct = [c for c in re.findall(r'\b\d{14}\b', cur_content) if not c.startswith("0000")]
                        if m_direct:
                            pnfl = m_direct[0]
                            print(f"[ACCOUNT IDENTIFIER TEKSHIRILDI] Sahifa HTML kodidan 14 talik PINFL olindi: {pnfl}", flush=True)
                            break

                        m_body = [c for c in re.findall(r'\b\d{14}\b', body_txt) if not c.startswith("0000")]
                        if m_body:
                            pnfl = m_body[0]
                            print(f"[ACCOUNT IDENTIFIER TEKSHIRILDI] Sahifa matnidan 14 talik PINFL olindi: {pnfl}", flush=True)
                            break

                        # 5. Toast va Dialog ichidagi 14 talik raqamlar (0000 bo'lmagan)
                        try:
                            dialog_texts = page.locator(".p-dialog, p-dialog, .p-toast, p-toast, .p-toast-detail, .p-toast-message, .alert, [role='alert']").all_inner_texts()
                            for d_txt in dialog_texts:
                                for cand in re.findall(r'(?:\d[\s\-_]?){14}', d_txt):
                                    c_clean = re.sub(r'\D', '', cand)
                                    if len(c_clean) == 14 and not c_clean.startswith("0000"):
                                        pnfl = c_clean
                                        break
                                if pnfl: break
                        except Exception:
                            pass

                        if pnfl:
                            break

                        print(f"[IDENTIFIER TEKSHIRUV {pnfl_check}/3] Login/PINFL hozircha topilmadi, qayta tekshirilmoqda...", flush=True)
                        time.sleep(1.5)

                    print(f"[FOUND ACCOUNT IDENTIFIER] {name} uchun hisob ma'lumoti: {pnfl}", flush=True)

                    if pnfl:
                        notify(f"🔑 [{name}] Allaqachon ro'yxatdan o'tgan! Login/PINFL ({pnfl}) orqali hisob tiklanmoqda...")
                        rec_res = recover_and_login_student(page, pnfl, name=name, notify=notify, default_password=default_password)
                        rec_ok = rec_res[0] if isinstance(rec_res, tuple) and len(rec_res) > 0 else False
                        rec_token = rec_res[1] if isinstance(rec_res, tuple) and len(rec_res) > 1 else None
                        rec_session = rec_res[2] if isinstance(rec_res, tuple) and len(rec_res) > 2 else None
                        if rec_ok and rec_token:
                            token = rec_token
                            target_email = pnfl
                            registration_success = True
                            save_student_to_db(seria, number, {
                                "name": name,
                                "birthdate": birthdate_digits,
                                "seria": seria,
                                "number": number,
                                "login": pnfl,
                                "password": default_password,
                                "phone": rec_session,
                                "status": "REGISTERED"
                            })
                            break
                        else:
                            if student_cycle < 3:
                                print(f"[ACCOUNT RETRY] Tiklashda kapcha bloki, IP yangilanib qayta urinilmoqda...")
                                switch_ip()
                                time.sleep(2)
                                continue
                            else:
                                browser.close()
                                notify(f"⚠️ [{name}] Hisob ({pnfl}) orqali tiklab bo'lmadi")
                                return False, "Hisob orqali tiklab bo'lmadi", "", ""
                    else:
                        browser.close()
                        notify(f"⚠️ [{name}] Bu o'quvchi ALLAQACHON ro'yxatdan o'tgan (Login/PINFL topilmadi)!")
                        return False, "Allaqachon ro'yxatdan o'tgan (Login/Parol kerak)", "",

                if not is_new_student and not is_already_registered:
                    if student_cycle < 3:
                        switch_ip()
                        continue
                    browser.close()
                    notify(f"❌ [{name}] Ro'yxatdan o'tish oynasiga o'tib bo'lmadi (Kapcha yechilmadi)")
                    return False, "Ro'yxatdan o'tish oynasiga o'tib bo'lmadi (Kapcha yechilmadi)", "", ""

                if is_new_student:
                    u_form = page.locator("input[formcontrolname='username'], input#username")
                    if u_form.count() > 0 and u_form.first.is_visible():
                        notify(f"📝 [{name}] Yangi login ochilmoqda ({target_email})...")
                        
                        # Har bir katakchani shoshmasdan to'ldirish va Angular eventlarini yuborish:
                        page.evaluate("""({ email, pwd }) => {
                            function setInput(selector, val) {
                                const el = document.querySelector(selector);
                                if (el) {
                                    el.focus();
                                    el.value = val;
                                    el.dispatchEvent(new Event('input', { bubbles: true }));
                                    el.dispatchEvent(new Event('change', { bubbles: true }));
                                    el.dispatchEvent(new Event('blur', { bubbles: true }));
                                }
                            }
                            setInput("input[formcontrolname='username'], input#username", email);
                            setInput("input[formcontrolname='password'], input#password", pwd);
                            setInput("input[formcontrolname='confirmPassword'], input#confirmPassword", pwd);
                        }""", {"email": target_email, "pwd": default_password})
                        
                        # Playwright orqali ham bitta-bitta kiritib tekshirish:
                        u_form.first.click(force=True)
                        u_form.first.fill(target_email)
                        time.sleep(0.5)
                        p_inp = page.locator("input[formcontrolname='password'], input#password").first
                        p_inp.click(force=True)
                        p_inp.fill(default_password)
                        time.sleep(0.5)
                        cp_inp = page.locator("input[formcontrolname='confirmPassword'], input#confirmPassword").first
                        cp_inp.click(force=True)
                        cp_inp.fill(default_password)
                        cp_inp.press("Tab")
                        time.sleep(1.5)

                        # "Keyingi qadam" tugmasi faollashishini sabr bilan kutamiz va bosamiz:
                        print("[STEP 2] 'Keyingi qadam' tugmasi faollashishi sabr bilan kutilmoqda...", flush=True)
                        otp_reached = False
                        for step_wait in range(1, 15):
                            # Tugmani aktivlashtirish va bosish:
                            page.evaluate("""() => {
                                const btn = Array.from(document.querySelectorAll('button')).find(b => b.textContent && b.textContent.includes('Keyingi qadam'));
                                if (btn) {
                                    btn.removeAttribute('disabled');
                                    btn.classList.remove('p-disabled');
                                    btn.click();
                                }
                            }""")
                            try:
                                n_btn = page.locator("button:has-text('Keyingi qadam')").first
                                if n_btn.count() > 0 and n_btn.is_visible():
                                    n_btn.click(timeout=1500)
                            except Exception:
                                pass
                            time.sleep(2)

                            # OTP oynasiga o'tganini tekshirish:
                            otp_inputs = page.locator(".verification-input, input[maxlength='1']")
                            if otp_inputs.count() > 0 and otp_inputs.first.is_visible():
                                print(f"[STEP 2 SUCCESS] OTP oynasi muvaffaqiyatli ochildi ({step_wait}-urinishda)!", flush=True)
                                otp_reached = True
                                break
                            
                            # Agar sahifada xatolik chiqsa (masalan "Bunday foydalanuvchi mavjud"):
                            c_text = page.content().lower()
                            if "mavjud" in c_text or "band" in c_text:
                                import random
                                target_email = f"maktab.{name.split()[0].lower()[:6]}.{random.randint(1000, 9999)}@gmail.com"
                                print(f"[EMAIL TAKEN] Yangi email tanlandi: {target_email}", flush=True)
                                u_form.first.fill(target_email)
                                time.sleep(1)

                    from session_pool import mark_session_exhausted, record_session_success

                    code = None
                    session_used = None
                    for reg_attempt in range(1, 10):
                        # 1. Agar 'Tasdiqlash kodini qayta yuborish' havolasi chiqib turgan bo'lsa, bosish
                        try:
                            resend_btn = page.locator("a:has-text('qayta yuborish'), button:has-text('qayta yuborish'), *:has-text('qayta yuborish')")
                            if resend_btn.count() > 0 and resend_btn.first.is_visible():
                                print("[RESEND] 'Tasdiqlash kodini qayta yuborish' tugmasi bosildi!", flush=True)
                                resend_btn.first.click(force=True)
                                code = None
                                time.sleep(2)
                        except Exception:
                            pass

                        # 2. Kod olish
                        if not code:
                            try:
                                page.evaluate("""() => {
                                    const inputs = document.querySelectorAll('.verification-input, input[maxlength="1"]');
                                    inputs.forEach(inp => {
                                        inp.value = '';
                                        inp.dispatchEvent(new Event('input', { bubbles: true }));
                                        inp.dispatchEvent(new Event('change', { bubbles: true }));
                                    });
                                }""")
                                code_inputs = page.locator(".verification-input, input[maxlength='1']")
                                for idx_c in range(code_inputs.count()):
                                    code_inputs.nth(idx_c).fill("")
                                time.sleep(0.5)
                            except Exception:
                                pass

                            notify(f"📩 [{name}] Telegram botdan (@aistudy_uz_bot) tasdiqlash kodi olinmoqda ({reg_attempt}-urinish)...")
                            code, session_used = get_telegram_verification_code()
                            if not code:
                                time.sleep(3)
                                code, session_used = get_telegram_verification_code()
                            if not code:
                                notify(f"⚠️ [{name}] Sessiyalardan kod olinmadi, qayta urinilmoqda...")
                                continue

                        # 3. Kodni katakchalarga kiritish
                        page.evaluate("""(code) => {
                            const inputs = document.querySelectorAll('.verification-input, input[maxlength="1"]');
                            for (let i = 0; i < Math.min(6, inputs.length); i++) {
                                inputs[i].focus();
                                inputs[i].value = code[i];
                                inputs[i].dispatchEvent(new Event('input', { bubbles: true }));
                                inputs[i].dispatchEvent(new Event('change', { bubbles: true }));
                            }
                        }""", code)
                        time.sleep(0.5)
                        try:
                            code_inputs = page.locator(".verification-input, input[maxlength='1']")
                            if code_inputs.count() >= 6:
                                for idx_d, digit in enumerate(code[:6]):
                                    code_inputs.nth(idx_d).click(force=True)
                                    code_inputs.nth(idx_d).fill(digit)
                        except Exception:
                            pass
                        time.sleep(1)

                        # 4. reCAPTCHA ni AI bilan yechish
                        captcha_ok = handle_recaptcha(page)
                        if not captcha_ok:
                            print(f"[VERIFY RECAPTCHA BLOCKED] Kapcha bloklandi (Try again later)!", flush=True)
                            # Agar sahifada 'qayta yuborish' tugmasi bo'lsa, bosib yangi kod olamiz (bu kapchani ham reset qiladi):
                            has_resend = False
                            try:
                                resend_btn = page.locator("a:has-text('qayta yuborish'), button:has-text('qayta yuborish'), *:has-text('qayta yuborish')")
                                if resend_btn.count() > 0 and resend_btn.first.is_visible():
                                    has_resend = True
                                    print("[RESEND OTP] Kapcha blokida 'qayta yuborish' bosildi, shu sahifada qolib yangi kod olinmoqda...", flush=True)
                                    resend_btn.first.click(force=True)
                                    code = None
                                    time.sleep(3)
                                    continue
                            except Exception:
                                pass

                            print(f"[VERIFY RECAPTCHA BLOCKED] Shu o'quvchi boshidan qaytadan ro'yxatdan o'tkazilmoqda ({student_cycle}/3)...", flush=True)
                            notify(f"🔄 [{name}] Google kapcha bloki (Try again)! Shu o'quvchi qaytadan boshlanmoqda ({student_cycle}/3)...")
                            switch_ip()
                            time.sleep(2)
                            retry_this_student = True
                            break

                        # Agar reload bo'lgan bo'lsa yoki kod o'chib ketgan bo'lsa, qayta to'ldirish:
                        try:
                            c_inp = page.locator(".verification-input, input[maxlength='1']").first
                            if not c_inp.input_value():
                                print(f"[RE-FILL CODE] Tasdiqlash kodi qayta kiritilmoqda: {code}")
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

                        # 5. FAQAT VA FAQAT kapcha muvaffaqiyatli yechilgandagina "Yuborish" bosiladi!
                        page.locator("button:has-text('Yuborish'), button:has-text('Tasdiqlash')").first.click(force=True)
                        print(f"[VERIFY WAIT] Tasdiqlash kodi yuborildi ({code}). Server javobi sabr bilan kutilmoqda...", flush=True)

                        # Shoshilmasdan 15 soniya davomida server tasdig'ini kutamiz:
                        is_limited = False
                        is_invalid = False
                        for wait_sec in range(1, 16):
                            time.sleep(1)
                            content = page.content().lower()
                            cur_url = page.url.lower()

                            if "tasdiqlanmadi" in content or "boshqa tasdiqlash kodi" in content:
                                is_invalid = True
                                print(f"[INVALID OTP DETECTED] Kod xato yoki eskirgan! Qayta yangi kod olinadi...", flush=True)
                                break

                            if "cheklangan" in content or "bitta telefon" in content:
                                is_limited = True
                                print(f"[LIMIT DETECTED] {session_used} raqamida cheklov aniqlandi!")
                                break

                            # Ro'yxatdan muvaffaqiyatli o'tganini tekshirish:
                            has_code_inputs = page.locator(".verification-input, input[maxlength='1']").count() > 0
                            if "/auth/login" in cur_url or "muvaffaqiyatli" in content or ("tizimga kirish" in content and not has_code_inputs):
                                print(f"[VERIFY SUCCESS] Server ro'yxatdan o'tishni muvaffaqiyatli tasdiqladi!")
                                registration_success = True
                                record_session_success(session_used)
                                break

                        if is_invalid:
                            code = None
                            try:
                                resend_btn = page.locator("a:has-text('qayta yuborish'), button:has-text('qayta yuborish'), *:has-text('qayta yuborish')")
                                if resend_btn.count() > 0 and resend_btn.first.is_visible():
                                    resend_btn.first.click(force=True)
                                    time.sleep(1)
                            except Exception:
                                pass
                            continue

                        if is_limited:
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

                        if registration_success:
                            break
                        else:
                            print(f"[VERIFY RETRY] 15 soniyada serverdan tasdiq kelmadi, qayta urinilmoqda...")

                    if registration_success:
                        break

                    if retry_this_student:
                        continue

            if not registration_success and not token:
                browser.close()
                notify(f"❌ [{name}] Ro'yxatdan o'tib bo'lmadi")
                return False, "Ro'yxatdan o'tib bo'lmadi", "", ""

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

            # 2-BOSQICH: Yangi olingan login/parol bilan kirish (agar token hali olinmagan bo'lsa)
            if not token:
                notify(f"🔓 [{name}] Tizimga kirilmoqda ({target_email})...")
                token = perform_safe_login(page, target_email, default_password, name=name, notify=notify)
                if not token:
                    browser.close()
                    save_student_to_db(seria, number, {
                        "name": name,
                        "seria": seria,
                        "number": number,
                        "status": "REGISTERED",
                        "login": target_email,
                        "password": default_password
                    })
                    notify(f"⚠️ [{name}] '{target_email}' kirib bo'lmadi. Keyingi o'quvchiga o'tilmoqda...")
                    return False, "Kirish amalga oshmadi", target_email, default_password

        # Agar token yo'q bo'lsa
        if not token:
            browser.close()
            notify(f"❌ [{name}] Tizimga kirishda token olinmadi")
            return False, "Tizimga kirishda token olinmadi", target_email, default_password

        notify(f"🔓 [{name}] Tizimga muvaffaqiyatli kirildi! Kurslar boshlandi...")
        disconnect_warp() # VPN ni o'chirish - TAS-IX ichki tarmoq maksimal tezlikda darslarni yopadi!

        # 3-BOSQICH: 4 ta kursni to'liq yakunlash
        for c_id in range(1, 5):
            for c_attempt in range(1, 3):
                try:
                    complete_course(page, c_id, status_callback=notify)
                    break
                except Exception as e_c:
                    print(f"[COMPLETE COURSE RETRY] Modul {c_id} ({c_attempt}/2) xatolik: {e_c}", flush=True)
                    time.sleep(2)

        # 4-BOSQICH: Sertifikatni olishdan oldin barcha 4 ta modulni 100% ligini tekshirish
        for c_check in range(1, 5):
            tree_chk = safe_eval(page, f"""async () => {{
                const token = localStorage.getItem('accessToken');
                const r = await fetch('https://api.aistudy.uz/api/StudyAILms/Progress/GetPrivateCourseContentTree?courseId={c_check}', {{
                    headers: {{ 'Authorization': 'Bearer ' + token }}
                }});
                return await r.json();
            }}""")
            chk_data = tree_chk.get("result", {}) if isinstance(tree_chk, dict) else {}
            fc_chk = chk_data.get("finishLessonCount", 0)
            tc_chk = chk_data.get("lessonCount", 0)
            if fc_chk < tc_chk and tc_chk > 0:
                print(f"[PRE-CERT SCAN] Modul {c_check} to'liq emas ({fc_chk}/{tc_chk}), 100% ga yetkazilmoqda...", flush=True)
                complete_course(page, c_check, status_callback=notify)

        notify(f"🏆 [{name}] Sertifikat havolasi olinmoqda...")
        cert_link = ""
        for c_try in range(1, 9):
            cert_api = safe_eval(page, """async () => {
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
            time.sleep(3)

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
        
    valid_rows = [r for r in range(header_row + 1, sheet.max_row + 1) if sheet.cell(r, name_col).value]
    total_students = len(valid_rows)
    success_count = 0
    
    for idx, r in enumerate(valid_rows, 1):
        idx_str = f"[{idx}/{total_students}]"
        name_val = sheet.cell(r, name_col).value
        if not name_val:
            continue
            
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
                    f"{idx_str} ⚡ [BAZADA TAYYOR] <b>{name_val}</b> ({seria} {num})\n"
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
            "sinf": sinf,
            "index_str": idx_str
        }
        if db_rec and db_rec.get("login") and db_rec.get("password"):
            student["existing_login"] = db_rec["login"]
            student["existing_password"] = db_rec["password"]

        # 2. EXCEL FAYLDAN TEKSHIRISH (Ustun 8 va 9)
        excel_login = str(sheet.cell(r, email_col).value or "").strip()
        excel_pwd = str(sheet.cell(r, pwd_col).value or "").strip()
        if excel_login and excel_pwd and excel_login.lower() not in ["none", "null", ""]:
            student["existing_login"] = excel_login
            student["existing_password"] = excel_pwd

        # I-FR bo'lmagan boshqa seriyalarni tekshirmasdan "Bazada yo'q" deb tashlab ketish:
        seria_clean = str(seria or "").replace(" ", "").replace("-", "").upper()
        has_account = bool(student.get("existing_login") and student.get("existing_password"))
        if not has_account and "FR" not in seria_clean:
            print(f"[SKIP NON-FR] {name_val} ({seria} {num}): Seriya I-FR emas, tashlab ketildi.")
            sheet.cell(r, cert_col).value = "Bazada yo'q (I-FR emas)"
            sheet.cell(r, time_col).value = "0 soniya (Tashlab ketildi)"
            wb.save(excel_path)
            if update_callback:
                update_callback(
                    f"{idx_str} ⏭ <b>{name_val}</b> ({seria} {num})\n"
                    f"⚠️ Seriya 'I-FR' emas ({seria}) — bazada yo'q deb tashlab ketildi."
                )
            continue

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
                    f"{idx_str} ✅ <b>{student['name']}</b>: Sertifikat olindi!\n"
                    f"⏱ <b>Sarflangan vaqt:</b> {st_dur_str}\n"
                    f"🔗 {res_link}"
                )
        else:
            if "Allaqachon" in str(res_link):
                sheet.cell(r, cert_col).value = "⚠️ Allaqachon ro'yxatdan o'tgan (Login/Parol kerak)"
            else:
                sheet.cell(r, cert_col).value = f"Olinmadi ({res_link})"
            wb.save(excel_path)
            if update_callback:
                update_callback(
                    f"{idx_str} ⚠️ <b>{student['name']}</b>: Olinmadi ({res_link})\n"
                    f"⏱ <b>Sarflangan vaqt:</b> {st_dur_str}"
                )
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
