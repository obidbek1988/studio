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
import concurrent.futures
import requests
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
PARALLEL_WORKERS = 10
excel_lock = threading.Lock()
CURRENT_ACTIVE_TOKEN_WORKERS = 0

def get_active_token_workers():
    global CURRENT_ACTIVE_TOKEN_WORKERS
    return CURRENT_ACTIVE_TOKEN_WORKERS

def normalize_birthdate_for_input(raw_bdate):
    """
    Tug'ilgan sanani 'DD/MM/YYYY' formatiga xatosiz keltirish.
    Kun, oy va yilni aniq ajratib oladi (hech qachon teskari bo'lmaydi).
    """
    if hasattr(raw_bdate, "strftime"):
        return raw_bdate.strftime("%d/%m/%Y")
    
    s = str(raw_bdate or "").strip()
    parts = re.split(r'[\.\-\/\s]', s)
    if len(parts) == 3:
        p1, p2, p3 = parts[0].strip(), parts[1].strip(), parts[2].strip()
        if len(p3) == 4 and 1990 <= int(p3) <= 2026:
            yr = p3
            d1, d2 = int(p1), int(p2)
        elif len(p1) == 4 and 1990 <= int(p1) <= 2026:
            yr = p1
            d1, d2 = int(p2), int(p3)
        else:
            yr = p3.zfill(4)
            d1, d2 = int(p1), int(p2)

        if d1 > 12 and d2 <= 12:
            day, mon = d1, d2
        elif d2 > 12 and d1 <= 12:
            day, mon = d2, d1
        else:
            day, mon = d1, d2

        return f"{str(day).zfill(2)}/{str(mon).zfill(2)}/{yr}"

    digits = "".join(c for c in s if c.isdigit())
    if len(digits) == 8:
        if 1990 <= int(digits[4:]) <= 2026:
            yr = digits[4:]
            d1, d2 = int(digits[:2]), int(digits[2:4])
        elif 1990 <= int(digits[:4]) <= 2026:
            yr = digits[:4]
            d1, d2 = int(digits[4:6]), int(digits[6:8])
        else:
            yr = digits[4:]
            d1, d2 = int(digits[:2]), int(digits[2:4])

        if d1 > 12 and d2 <= 12:
            day, mon = d1, d2
        elif d2 > 12 and d1 <= 12:
            day, mon = d2, d1
        else:
            day, mon = d1, d2

        return f"{str(day).zfill(2)}/{str(mon).zfill(2)}/{yr}"
            
    return s


def load_students_db():
    if DB_PATH.exists():
        try:
            with open(DB_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[LOAD DB ERROR] {e}")
    return {}

def get_cloud_sync_token():
    token = os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN")
    if not token:
        for p in ["token.txt", "../token.txt", "core_temp/token.txt"]:
            if os.path.exists(p):
                try:
                    t = open(p).read().strip()
                    if t and len(t) > 10:
                        return t
                except Exception:
                    pass
    return token

def _sync_db_to_cloud_worker(json_text):
    try:
        import os, urllib.request, json, base64
        token = get_cloud_sync_token()
        if not token:
            return

        api_url = "https://api.github.com/repos/obidbek1988/studio-core/contents/students_db.json"
        req = urllib.request.Request(api_url)
        req.add_header("Authorization", f"token {token}")
        req.add_header("User-Agent", "Mozilla/5.0")
        sha = None
        try:
            with urllib.request.urlopen(req) as resp:
                data = json.loads(resp.read().decode())
                sha = data.get("sha")
        except Exception:
            pass

        put_data = {
            "message": "Auto-sync students_db.json",
            "content": base64.b64encode(json_text.encode("utf-8")).decode("utf-8")
        }
        if sha:
            put_data["sha"] = sha

        put_req = urllib.request.Request(api_url, data=json.dumps(put_data).encode("utf-8"), method="PUT")
        put_req.add_header("Authorization", f"token {token}")
        put_req.add_header("Content-Type", "application/json")
        put_req.add_header("User-Agent", "Mozilla/5.0")
        with urllib.request.urlopen(put_req) as resp:
            pass
        print("[CLOUD DB SYNC] students_db.json GitHub-ga real vaqtda saqlandi!", flush=True)
    except Exception as e:
        print(f"[CLOUD DB SYNC ERROR] {e}", flush=True)

def sync_active_order_to_cloud(excel_path=None, state_dict=None):
    """Faol buyurtma holati va Excel faylini studio-core ga avtomatik sinxron qilish"""
    def _order_sync_worker():
        try:
            import os, urllib.request, json, base64
            token = get_cloud_sync_token()
            if not token:
                return

            # 1. active_order_state.json ni yangilash
            if state_dict:
                st_url = "https://api.github.com/repos/obidbek1988/studio-core/contents/active_order_state.json"
                st_text = json.dumps(state_dict, indent=2, ensure_ascii=False)
                sha = None
                try:
                    r1 = urllib.request.Request(st_url, headers={"Authorization": f"token {token}", "User-Agent": "Mozilla/5.0"})
                    with urllib.request.urlopen(r1) as resp:
                        sha = json.loads(resp.read().decode()).get("sha")
                except Exception:
                    pass
                put_d = {
                    "message": f"Sync active_order_state ({state_dict.get('status', 'PROCESSING')})",
                    "content": base64.b64encode(st_text.encode("utf-8")).decode("utf-8")
                }
                if sha:
                    put_d["sha"] = sha
                pr1 = urllib.request.Request(st_url, data=json.dumps(put_d).encode("utf-8"), method="PUT", headers={"Authorization": f"token {token}", "Content-Type": "application/json", "User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(pr1):
                    pass

            # 2. active_order.xlsx ni yangilash
            if excel_path and os.path.exists(excel_path):
                ex_url = "https://api.github.com/repos/obidbek1988/studio-core/contents/active_order.xlsx"
                sha_ex = None
                try:
                    r2 = urllib.request.Request(ex_url, headers={"Authorization": f"token {token}", "User-Agent": "Mozilla/5.0"})
                    with urllib.request.urlopen(r2) as resp:
                        sha_ex = json.loads(resp.read().decode()).get("sha")
                except Exception:
                    pass
                with open(excel_path, "rb") as ef:
                    ex_bytes = ef.read()
                put_ex = {
                    "message": "Sync active_order.xlsx for auto-resume",
                    "content": base64.b64encode(ex_bytes).decode("utf-8")
                }
                if sha_ex:
                    put_ex["sha"] = sha_ex
                pr2 = urllib.request.Request(ex_url, data=json.dumps(put_ex).encode("utf-8"), method="PUT", headers={"Authorization": f"token {token}", "Content-Type": "application/json", "User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(pr2):
                    pass
                print("[CLOUD ORDER SYNC] active_order.xlsx va state studio-core ga muvaffaqiyatli saqlandi!", flush=True)
        except Exception as e:
            print(f"[CLOUD ORDER SYNC ERROR] {e}", flush=True)

    threading.Thread(target=_order_sync_worker, daemon=True).start()

def sync_db_to_cloud_async(db_dict):
    try:
        json_text = json.dumps(db_dict, indent=2, ensure_ascii=False)
        t = threading.Thread(target=_sync_db_to_cloud_worker, args=(json_text,), daemon=True)
        t.start()
    except Exception:
        pass

def save_students_db(db):
    try:
        with open(DB_PATH, "w", encoding="utf-8") as f:
            json.dump(db, f, indent=2, ensure_ascii=False)
        sync_db_to_cloud_async(db)
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
    """Cloudflare WARP orqali toza yangi IP olish (Faqat Google kapcha blok berganda)"""
    warp_exe = r"C:\Program Files\Cloudflare\Cloudflare WARP\warp-cli.exe"
    if os.path.exists(warp_exe):
        for w_try in range(1, 3):
            try:
                print(f"[WARP] Google blok tufayli yangi toza IP olinmoqda ({w_try}/2)...", flush=True)
                subprocess.run([warp_exe, "--accept-tos", "disconnect"], capture_output=True, timeout=8)
                time.sleep(1)
                subprocess.run([warp_exe, "--accept-tos", "connect"], capture_output=True, timeout=8)
                time.sleep(2)
                print(f"[WARP] Yangi toza IP muvaffaqiyatli ulandi!", flush=True)
                return True
            except Exception as ew:
                print(f"[WARP ERROR] {ew}", flush=True)
                time.sleep(1)
    time.sleep(2)
    return True

def launch_universal_browser(p, headless=False):
    """
    Universal brauzer ochuvchi:
    1. AnyDesk va ekranda jonli ko'rinishi uchun headless=False (Ochiq Google Chrome).
    2. Agar tizimda Google Chrome bo'lsa 'chrome' kanali bilan ochadi.
       Agar Google Chrome o'rnatilmagan bo'lsa, standart Playwright Chromium orqali ochadi.
    """
    browser_args = [
        "--no-sandbox",
        "--disable-blink-features=AutomationControlled",
        "--disable-features=Translate",
        "--no-default-browser-check",
        "--disable-popup-blocking",
        "--mute-audio"
    ]
    # Agar maxsus HEADLESS=1 berilmasa, har doim EKRANDA OCHIQ (headless=False) ishlaydi:
    env_headless = os.environ.get("HEADLESS", "0").strip().lower()
    actual_headless = True if env_headless in ("1", "true", "yes") else False

    try:
        return p.chromium.launch(
            channel="chrome",
            headless=actual_headless,
            args=browser_args
        )
    except Exception:
        return p.chromium.launch(
            headless=actual_headless,
            args=browser_args
        )

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
    for attempt in range(1, 4):
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
                        print("[RECAPTCHA BLOK] Google blok chiqardi (Try again later)! Yangi toza IP olinmoqda...", flush=True)
                        switch_ip()
                        time.sleep(2)
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
                                print("[RECAPTCHA] Yangi toza IP orqali blok muvaffaqiyatli ketdi!", flush=True)
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
    """@aistudy_uz_bot dan SMS tasdiqlash kodini olish"""
    if os.environ.get("MANUAL_OTP") == "1":
        print("\n" + "="*55, flush=True)
        print("🔔 [RO'YXATDAN O'TISH] TELEGRAM TASDIQLASH KODI KERAK!", flush=True)
        print("👉 @aistudy_uz_bot dan kelgan 6 ta raqamli kodni yozing:")
        print("="*55 + "\n", flush=True)
        try:
            import winsound
            winsound.Beep(1200, 500)
        except Exception:
            pass
        while True:
            c = input("👉 TELEGRAM KODINI KIRITING (6 ta raqam): ").strip()
            c = re.sub(r'\D', '', c)
            if len(c) == 6:
                return c, "Qo'lda kiritildi"
            print("⚠️ Kod 6 ta raqamdan iborat bo'lishi kerak! Qayta tering.")

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

LAST_LOGIN_ERROR = ""

def perform_safe_login(page, email, password, name="", notify=None):
    """Xavfsiz, 3 martalik va Google kapcha blokini hisobga oluvchi login qilish"""
    global LAST_LOGIN_ERROR
    LAST_LOGIN_ERROR = ""
    
    attempt = 1
    max_attempts = 3
    captcha_block_count = 0

    while attempt <= max_attempts:
        try:
            page.goto("https://omp.aistudy.uz/auth/login?debug_bypass=omp-dev-master-99", wait_until="domcontentloaded")
            page.wait_for_timeout(2000)
            page.evaluate("document.querySelectorAll('.devtools-overlay, .telegram-popup-overlay, .p-dialog-mask').forEach(e => e.remove());")

            switch_to_login_tab(page)
            time.sleep(0.5)

            u_inp = page.locator("input#username, input[formcontrolname='username']").first
            u_inp.click(force=True)
            u_inp.fill(email)
            time.sleep(0.3)

            p_inp = page.locator("input#password, input[formcontrolname='password']").first
            p_inp.click(force=True)
            p_inp.fill(password)
            time.sleep(0.5)

            if notify:
                notify(f"🎧 [{name}] reCAPTCHA audio Whisper AI orqali yechilmoqda ({attempt}/{max_attempts})...")

            # Google reCAPTCHA Whisper AI orqali to'liq yechish
            c_ok = handle_recaptcha(page)
            time.sleep(1)

            # Google kapcha IP bloki ("try again later") tekshiruvi
            is_blocked = False
            try:
                for f in page.frames:
                    if "bframe" in f.url or "recaptcha" in f.url:
                        fc = f.content().lower()
                        if "try again later" in fc or "automated queries" in fc:
                            is_blocked = True
                            break
            except Exception:
                pass

            if is_blocked:
                captcha_block_count += 1
                print(f"[LOGIN RECAPTCHA BLOCK] Google kapcha bloki! Bu urinishga hisoblanmaydi ({captcha_block_count}). Yangi toza IP olinmoqda...", flush=True)
                if notify:
                    notify(f"⏳ [{name}] Google kapcha bloki! Yangi toza IP olinmoqda (Urinish kuymaydi: {attempt}/{max_attempts})...")
                switch_ip()
                time.sleep(3)
                continue  # attempt oshmaydi, qayta urinib ko'radi

            if not c_ok:
                print(f"[LOGIN RECAPTCHA FAIL] Kapcha yechilmadi ({attempt}/{max_attempts})")
                LAST_LOGIN_ERROR = "Google reCAPTCHA yechilmadi"
                attempt += 1
                time.sleep(2)
                continue

            # Agar reload bo'lgan bo'lsa, inputlarni qayta to'ldiramiz
            try:
                cur_u = page.locator("input#username, input[formcontrolname='username']").first.input_value()
                if not cur_u or cur_u != email:
                    u2 = page.locator("input#username, input[formcontrolname='username']").first
                    u2.fill(email)
                    p2 = page.locator("input#password, input[formcontrolname='password']").first
                    p2.fill(password)
            except Exception:
                pass

            # Endi "Tizimga kirish" tugmasini bosamiz
            page.locator("button:has-text('Tizimga kirish')").last.click(force=True)
            page.wait_for_timeout(3500)

            token = page.evaluate("() => localStorage.getItem('accessToken')")
            if not token:
                page.wait_for_timeout(2500)
                token = page.evaluate("() => localStorage.getItem('accessToken')")

            if token:
                print(f"[LOGIN SUCCESS] Tizimga muvaffaqiyatli kirildi ({email})!")
                LAST_LOGIN_ERROR = ""
                return token

            page_text = page.content().lower()
            if "topilmadi" in page_text or "not found" in page_text or "mavjud emas" in page_text:
                print(f"[LOGIN NOT FOUND] '{email}' bo'yicha foydalanuvchi topilmadi!")
                LAST_LOGIN_ERROR = "Foydalanuvchi topilmadi (login mavjud emas)"
                return None
            elif "noto'g'ri" in page_text or "xato" in page_text or "invalid" in page_text:
                print(f"[LOGIN BAD CREDENTIALS] '{email}' parol noto'g'ri!")
                LAST_LOGIN_ERROR = "Parol noto'g'ri kiritildi"
                return None

            LAST_LOGIN_ERROR = "Tizimga kirishda token olinmadi"
            attempt += 1
            time.sleep(1)
        except Exception as el:
            print(f"[LOGIN EXCEPTION] {el}")
            LAST_LOGIN_ERROR = f"Login jarayonida xatolik: {str(el)[:50]}"
            attempt += 1
            time.sleep(1)

    if not LAST_LOGIN_ERROR:
        LAST_LOGIN_ERROR = "3 ta urinishda ham kirib bo'lmadi"
    return None

def recover_and_login_student(page, pnfl, name="", notify=None, default_password="Dilnuraxon2015"):
    """PINFL (JSHSHIR) orqali parolni tiklash va tizimga kirish (Allaqachon ro'yxatdan o'tganlar uchun)"""
    for main_attempt in range(1, 4):
        try:
            from session_pool import fetch_code_for_phone_ending, fetch_tg_code_from_pool
            print(f"\n[RECOVERY START] {name} uchun PINFL={pnfl} orqali tiklash ({main_attempt}/3)...", flush=True)
            page.goto("https://omp.aistudy.uz/auth/forgot-password?debug_bypass=omp-dev-master-99", wait_until="domcontentloaded")
            time.sleep(2.5)
            page.evaluate("document.querySelectorAll('.devtools-overlay, .telegram-popup-overlay, .p-dialog-mask').forEach(e => e.remove());")

            # 1. Login - Parol tabini bosish
            page.evaluate("""() => {
                const tabs = Array.from(document.querySelectorAll("p-tab, [role='tab'], button"));
                const loginTab = tabs.find(el => el.textContent && el.textContent.includes('Login'));
                if (loginTab) {
                    loginTab.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));
                    loginTab.click();
                }
            }""")
            time.sleep(1.5)

            # 2. PINFL ni kiritish
            u_input = page.locator("input#username, input[formcontrolname='username']").first
            u_input.click(force=True)
            u_input.fill("")
            u_input.fill(str(pnfl).strip())
            time.sleep(1)

            # 3. "Kodni olish" / "Yuborish" tugmasini bosish
            sub_btn = page.locator("button[type='submit'], button:has-text('Kodni olish'), button:has-text('Yuborish')").first
            sub_btn.click(force=True)
            time.sleep(3)

            # 4. Sahifadagi xabarni tekshiramiz (telefon raqami oxirgi 4 ta soni)
            page_text = page.locator("body").inner_text()
            print(f"[RECOVERY PAGE TEXT] {page_text[:200]}...", flush=True)

            phone_4 = None
            m_ph = re.search(r'998[\*\d\s]*(\d{4})', page_text)
            if m_ph:
                phone_4 = m_ph.group(1)
            else:
                matches = re.findall(r'\b(\d{4})\b', page_text)
                valid_4 = [m for m in matches if m not in ["2024", "2025", "2026", "2027"]]
                if valid_4:
                    phone_4 = valid_4[-1]

            if phone_4:
                print(f"[RECOVERY PHONE] Oxirgi 4 ta raqam aniqlandi: {phone_4}", flush=True)
                # TEZDA TEKSHIRISH: Bu raqam bizning 3600+ ta sessiyamiz ichida bormi?
                from session_pool import SESSIONS_DIR
                has_matching_session = False
                if os.path.exists(SESSIONS_DIR):
                    for s_fn in os.listdir(SESSIONS_DIR):
                        if s_fn.endswith(".session"):
                            cln_digits = re.sub(r'\D', '', s_fn[:-8])
                            if cln_digits.endswith(phone_4):
                                has_matching_session = True
                                break

                if not has_matching_session and os.environ.get("MANUAL_OTP") != "1":
                    print(f"[RECOVERY SKIP] Oxiri {phone_4} bo'lgan raqam bizning sessiyalarimizda yo'q (shaxsiy raqam)!", flush=True)
                    if notify:
                        notify(f"⚠️ [{name}] Bu raqam (...{phone_4}) bizning bazamizda yo'q (shaxsiy raqam). Keyingi o'quvchiga o'tilmoqda...")
                    return False, "personal_phone"

                if notify:
                    notify(f"📱 [{name}] Telegram raqami: oxiri {phone_4}. Sessiyadan kod olinmoqda...")

            # 5. Sessiyadan kodni olamiz
            code = None
            session_used = None
            if os.environ.get("MANUAL_OTP") == "1":
                print("\n" + "="*55, flush=True)
                print(f"🔔 [PAROLNI TIKLASH] TELEGRAM KODI KERAK! ({name})", flush=True)
                if phone_4:
                    print(f"📱 Saytdagi raqam oxiri: ...{phone_4}", flush=True)
                print("👉 @aistudy_uz_bot dan kelgan 6 xonali kodni yozing:")
                print("="*55 + "\n", flush=True)
                try:
                    import winsound
                    winsound.Beep(1200, 500)
                except Exception:
                    pass
                while True:
                    c = input("👉 TELEGRAM KODINI KIRITING (6 ta raqam): ").strip()
                    c = re.sub(r'\D', '', c)
                    if len(c) == 6:
                        code = c
                        session_used = f"Qo'lda (...{phone_4})" if phone_4 else "Qo'lda kiritildi"
                        break
                    print("⚠️ Kod 6 ta raqam bo'lishi kerak! Qayta tering.")
            else:
                if phone_4:
                    code, session_used = fetch_code_for_phone_ending(phone_4)
                if not code:
                    code, session_used = fetch_tg_code_from_pool()

            if not code:
                print(f"[RECOVERY FAIL] Telegram sessiyalardan kod kelmadi!", flush=True)
                switch_ip()
                time.sleep(2)
                continue

            print(f"[RECOVERY CODE] Kod olindi: {code} (Sessiya: {session_used}). Kiritilmoqda...", flush=True)
            if notify:
                notify(f"🔐 [{name}] Kod olindi ({code}) [{session_used}]. Kiritilmoqda...")

            # 6. Katakchalarga kodni kiritish
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

            code_inps = page.locator(".verification-input, input[maxlength='1']")
            for c_i in range(min(6, code_inps.count())):
                try:
                    code_inps.nth(c_i).fill(code[c_i])
                except Exception:
                    pass
            time.sleep(1)

            # 7. Kodni tasdiqlash uchun "Yuborish" tugmasini bosish
            print(f"[RECOVERY SUBMIT] Kod yuborilmoqda (Yuborish tugmasi bosildi)...", flush=True)
            try:
                page.locator("button:has-text('Yuborish'), button:has-text('Tasdiqlash'), button[type='submit']").last.click(force=True)
            except Exception:
                pass
            time.sleep(3)

            # 8. Yangi parol kiritish oynasi chiqadi (Form 2)
            p_inputs = page.locator("input#password, input[formcontrolname='password'], input[type='password']")
            if p_inputs.count() > 0:
                print(f"[RECOVERY NEW PWD] Yangi parol o'rnatilmoqda: {default_password}", flush=True)
                p_inputs.first.fill(default_password)
                cp_input = page.locator("input#confirmPassword, input[formcontrolname='confirmPassword']").first
                if cp_input.count() > 0:
                    cp_input.fill(default_password)
                time.sleep(1)

                # Kapchani yechish
                cap_ok = handle_recaptcha(page)
                if not cap_ok:
                    print(f"[RECOVERY CAPTCHA BLOCKED] Kapcha bloklandi (Try again later)! IP almashtirilib, sahifa yangidan boshlanadi...", flush=True)
                    if notify:
                        notify(f"🔄 [{name}] Kapcha bloki (Try again)! IP almashtirilib, tiklash qaytadan boshlanmoqda ({main_attempt}/3)...")
                    switch_ip()
                    time.sleep(3)
                    continue # Sahifani qaytadan yangi IP bilan ochamiz!

                # "Tasdiqlash" / "Saqlash" / "Yuborish" tugmasini bosish
                print(f"[RECOVERY CONFIRM] Tasdiqlash tugmasi bosilmoqda...", flush=True)
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
                    print(f"[RECOVERY RETRY] Parol formasi hali ham ochiq, IP almashtirilib qayta uriniladi...", flush=True)
                    switch_ip()
                    time.sleep(2)
                    continue

            # 9. Endi tizimga yangi parol bilan kirish
            token = perform_safe_login(page, pnfl, default_password, name=name, notify=notify)
            if not token:
                token = page.evaluate("() => localStorage.getItem('accessToken')")
            if token:
                return True, token
        except Exception as e:
            print(f"[RECOVERY EXCEPTION {main_attempt}] {e}", flush=True)
            switch_ip()
            time.sleep(2)

    return False, None

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



# =========================================================================
# 4-PARALLEL BACKGROUND WORKERS & API PIPELINE
# =========================================================================

def solve_quiz_api(session, headers, quiz_id):
    """Testni avtomatik to'g'ri javoblar bilan API orqali topshirish"""
    try:
        r = session.get(f"https://api.aistudy.uz/api/StudyAILms/Quiz/GetQuizById?id={quiz_id}", headers=headers, timeout=15)
        if r.status_code != 200:
            return None
        quiz_data = r.json().get("result", {})
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

        payload = {
            "quizId": quiz_id,
            "quizQuestions": quiz_questions_payload
        }
        r_check = session.post("https://api.aistudy.uz/api/StudyAILms/Quiz/CheckQuizAndSaveResult", headers=headers, json=payload, timeout=15)
        return r_check.json() if r_check.status_code == 200 else None
    except Exception as e_q:
        print(f"[QUIZ SOLVE API ERROR] {e_q}")
        return None


def complete_course_api(session, token, course_id, status_callback=None):
    """Kursni to'liq 100% serverga muhrlab yakunlash (API orqali - fon rejimida)"""
    course_names = {
        1: "1-modul: Sun'iy intellekt asoslari",
        2: "2-modul: Prompt muhandisligi asoslari",
        3: "3-modul: Promptlar yozish va LLM amaliyot",
        4: "4-modul: Yakuniy imtihon testlari"
    }
    c_title = course_names.get(course_id, f"{course_id}-modul")
    if status_callback:
        status_callback(f"📚 {c_title} 100% yopilmoqda...")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Origin": "https://omp.aistudy.uz",
        "Referer": "https://omp.aistudy.uz/"
    }

    try:
        session.post(f"https://api.aistudy.uz/api/StudyAILms/Progress/StartCourseProgress?courseId={course_id}", headers=headers, json={}, timeout=15)
    except Exception as e:
        print(f"[START PROGRESS ERR] {e}")
    time.sleep(1.0)

    tree = {}
    for _ in range(3):
        try:
            r = session.get(f"https://api.aistudy.uz/api/StudyAILms/Progress/GetPrivateCourseContentTree?courseId={course_id}", headers=headers, timeout=15)
            if r.status_code == 200:
                tree = r.json().get("result", {})
                break
        except Exception:
            time.sleep(1)

    modules = tree.get("children", [])
    completed_count = tree.get("finishLessonCount", 0)
    total_count = tree.get("lessonCount", 20)

    for mod in modules:
        lessons = mod.get("children", [])
        for les in lessons:
            les_id = les.get("id")
            les_type = les.get("type")
            les_status = les.get("status")

            if les_type == 2:
                if les_status == 2:
                    continue

                rand_used = random.randint(190, 340)
                for attempt in range(1, 6):
                    try:
                        resp = session.post(
                            "https://api.aistudy.uz/api/StudyAILms/UserWatchStory/CreateOrUpdateLessonWatch",
                            headers=headers,
                            json={
                                "lessonId": les_id,
                                "language": "uz",
                                "percentJson": {"uz": "100.00", "ru": "100.00", "en": "100.00"},
                                "usedTime": rand_used
                            },
                            timeout=15
                        )
                        if resp.status_code == 429:
                            time.sleep(6.0)
                            continue
                        if resp.status_code in (200, 204):
                            completed_count += 1
                            print(f"    [OK API] Modul {course_id} - Dars {les_id} yopildi (✔) [Ko'rish: {rand_used}s] ({completed_count}/{total_count})")
                            time.sleep(random.uniform(5.12, 5.38))
                            break
                    except Exception as e:
                        print(f"[WATCH ERR] {e}")
                    time.sleep(5.0)

            elif les_type == 3:
                if les_status == 2:
                    continue
                solve_quiz_api(session, headers, les_id)
                completed_count += 1
                print(f"    [OK API] Modul {course_id} - Test {les_id} topshirildi (✔) ({completed_count}/{total_count})")
                time.sleep(2.0)

    for audit_try in range(1, 4):
        time.sleep(2.5)
        try:
            r = session.get(f"https://api.aistudy.uz/api/StudyAILms/Progress/GetPrivateCourseContentTree?courseId={course_id}", headers=headers, timeout=15)
            tree_data = r.json().get("result", {}) if r.status_code == 200 else {}
        except Exception:
            tree_data = {}
        fc = tree_data.get("finishLessonCount", 0)
        tc = tree_data.get("lessonCount", 0)
        if fc >= tc and tc > 0:
            break
        for m in tree_data.get("children", []):
            for l in m.get("children", []):
                lid = l.get("id")
                ltype = l.get("type")
                lstatus = l.get("status")
                if lstatus != 2:
                    if ltype == 2:
                        try:
                            session.post(
                                "https://api.aistudy.uz/api/StudyAILms/UserWatchStory/CreateOrUpdateLessonWatch",
                                headers=headers,
                                json={
                                    "lessonId": lid,
                                    "language": "uz",
                                    "percentJson": {"uz": "100.00", "ru": "100.00", "en": "100.00"},
                                    "usedTime": 300
                                },
                                timeout=15
                            )
                        except Exception:
                            pass
                        time.sleep(5.2)
                    elif ltype == 3:
                        solve_quiz_api(session, headers, lid)
                        time.sleep(2.0)

    if status_callback:
        status_callback(f"✅ {c_title} 100% muvaffaqiyatli yakunlandi!")
    return True


def get_certificate_api(session, headers):
    """Sertifikat havolasini API orqali olish"""
    for c_try in range(1, 9):
        try:
            r = session.get("https://api.aistudy.uz/api/StudyAILms/Certificate/GetCertificateByUser", headers=headers, timeout=15)
            if r.status_code == 200:
                res_obj = r.json()
                if res_obj and res_obj.get("result"):
                    cid = res_obj.get("result", {}).get("id") or res_obj.get("result", {}).get("certificateId")
                    if cid:
                        return f"https://omp.aistudy.uz/certificate?id={cid}"
        except Exception:
            pass
        time.sleep(3)
    return None


def complete_student_courses_api(token, student, notify=None):
    """Bitta o'quvchining 4 ta modulini API orqali parallel fonda 100% yopish va sertifikat olish"""
    name = student["name"]
    session = requests.Session()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Origin": "https://omp.aistudy.uz",
        "Referer": "https://omp.aistudy.uz/"
    }

    for c_id in range(1, 5):
        for c_attempt in range(1, 3):
            try:
                complete_course_api(session, token, c_id, status_callback=notify)
                break
            except Exception as e_c:
                print(f"[API COURSE RETRY] Modul {c_id} ({c_attempt}/2) xatolik: {e_c}", flush=True)
                time.sleep(2)

    for c_check in range(1, 5):
        try:
            r = session.get(f"https://api.aistudy.uz/api/StudyAILms/Progress/GetPrivateCourseContentTree?courseId={c_check}", headers=headers, timeout=15)
            chk_data = r.json().get("result", {}) if r.status_code == 200 else {}
            fc_chk = chk_data.get("finishLessonCount", 0)
            tc_chk = chk_data.get("lessonCount", 0)
            if fc_chk < tc_chk and tc_chk > 0:
                print(f"[PRE-CERT SCAN API] Modul {c_check} to'liq emas ({fc_chk}/{tc_chk}), 100% ga yetkazilmoqda...", flush=True)
                complete_course_api(session, token, c_check, status_callback=notify)
        except Exception:
            pass

    if notify:
        notify(f"🏆 [{name}] Sertifikat havolasi olinmoqda...")
    cert_link = get_certificate_api(session, headers)
    return cert_link


def login_or_register_single_student(student, update_callback=None):
    """O'quvchini Playwright orqali tizimga kiritish yoki ro'yxatdan o'tkazish (Faqat Login/Token bosqichi)"""
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
        return False, None, "", "", "Bazada yo'q (I-FR emas)"

    notify(f"⏳ [{name}] Jarayon boshlandi ({seria} {number})...")

    with sync_playwright() as p:
        browser = launch_universal_browser(p, headless=False)
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            locale="en-US",
            permissions=["clipboard-read", "clipboard-write"],
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        context.add_init_script("""
            window._sys_dt_bypass = true;
            window.__last_copied_login = '';
            if (navigator.clipboard && navigator.clipboard.writeText) {
                const origWrite = navigator.clipboard.writeText.bind(navigator.clipboard);
                navigator.clipboard.writeText = async (text) => {
                    window.__last_copied_login = text;
                    return origWrite(text);
                };
            }
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
            # SMART TIMEOUT: Kapcha yechish, IP almashtirish va Telegram kod kutish vaqti
            # bu hisobga kirmaydi! Sof qotib qolish / harakatsizlik vaqti 180 soniya (3 daqiqa).
            student_idle_start = time.time()
            for student_cycle in range(1, 4):
                if registration_success or token:
                    break
                if time.time() - student_idle_start > 180:
                    print(f"[STUDENT TIMEOUT] {name} uchun 3 daqiqalik harakatsizlik limiti to'ldi, keyingi o'quvchiga o'tilmoqda...", flush=True)
                    notify(f"⏱ [{name}] Jarayon 3 daqiqa qotib qolgani sababli, keyingi o'quvchiga o'tilmoqda...")
                    break

                is_already_registered = False
                is_new_student = False
                has_error = False
                retry_this_student = False

                # Metrika formasini to'ldirish (Google kapcha bloki urinishga hisoblanmaydi!)
                form_attempt = 1
                captcha_block_count = 0
                while form_attempt <= 3 and captcha_block_count < 10:
                    notify(f"📝 [{name}] Metrika kiritilmoqda ({seria} {number}) [Urinish: {student_cycle}.{form_attempt}]...")
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
                    page.evaluate("""() => {
                        const btns = Array.from(document.querySelectorAll('button, .btn-switch, .switch-item, [role="tab"], p-tab'));
                        const metr = btns.find(b => b.textContent && (b.textContent.includes("Tug'ilganlik") || b.textContent.includes('guvohnoma') || b.textContent.includes('Metrika')));
                        if (metr) {
                            metr.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));
                            metr.click();
                        }
                    }""")
                    time.sleep(1.5)

                    # Seriya katakchasi mavjudligini tekshirish
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

                    b_formatted = normalize_birthdate_for_input(cur_bdate)
                    page.evaluate("document.querySelectorAll('.telegram-popup-overlay, .devtools-overlay, .p-dialog-mask').forEach(e => e.remove());")
                    b_input = page.locator("input#birthdate, input[formcontrolname='birthdate'], input.p-datepicker-input").first
                    b_input.click(force=True)
                    b_input.fill("")
                    b_input.fill(b_formatted)
                    b_input.press("Tab")
                    page.evaluate("() => { if (document.activeElement) document.activeElement.blur(); }")
                    time.sleep(1.0)

                    # reCAPTCHA ni AI bilan yechish
                    notify(f"🎧 [{name}] reCAPTCHA Whisper AI orqali yechilmoqda ({form_attempt}/3)...")
                    captcha_solved = handle_recaptcha(page)
                    student_idle_start = time.time()  # Kapchadan keyin taymer yangilanadi

                    if not captcha_solved:
                        captcha_block_count += 1
                        print(f"[RECAPTCHA TRY AGAIN LATER] Google kapcha bloki! Bu 3 martalik limitga hisoblanmaydi ({captcha_block_count}). Toza IP olinmoqda...")
                        notify(f"⏳ [{name}] Google kapcha bloki! Yangi toza IP olinmoqda (Urinish kuymaydi: {form_attempt}/3)...")
                        switch_ip()
                        time.sleep(3)
                        continue  # E'tibor bering: form_attempt oshmaydi!

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
                        print(f"[STEP 1 RETRY] Serverdan javob kelmadi, qayta urinilmoqda ({form_attempt}/3)...", flush=True)
                        notify(f"⏳ [{name}] Server javobi kechikmoqda, qayta urinilmoqda ({form_attempt}/3)...")
                        form_attempt += 1  # Faqat server javob bermaganda urinish oshadi!
                        time.sleep(2)
                        continue

                if has_error:
                    browser.close()
                    notify(f"❌ [{name}] Metrika davlat bazasida topilmadi ({seria} {number})")
                    return False, None, "", "", "Metrika davlat bazasida topilmadi (No content)"

                if is_already_registered:
                    pnfl_matches = re.findall(r'\b\d{14}\b', content)
                    pnfl = pnfl_matches[0] if pnfl_matches else None
                    if not pnfl:
                        try:
                            all_text = page.locator("body").inner_text()
                            m14 = re.findall(r'\b\d{14}\b', all_text)
                            if m14:
                                pnfl = m14[0]
                        except Exception:
                            pass

                    # AGAR 14 xonali PINFL bo'lmasa, saytdagi login yonidagi 📋 kopiya tugmasini 1 marta bosib buferdan olamiz!
                    if not pnfl:
                        try:
                            # 1. Saytdagi 📋 nusxa olish (kopy) tugmasini 1 marta bosamiz
                            page.evaluate("""() => {
                                const allEls = Array.from(document.querySelectorAll('*'));
                                const container = allEls.find(el => el.innerText && el.innerText.includes('Tizimga kirish') && !el.innerText.includes('sahifasiga'));
                                if (container) {
                                    const btn = container.querySelector('button, svg, [role="button"], span.cursor-pointer, i') || container;
                                    btn.click();
                                }
                            }""")
                            try:
                                copy_locator = page.locator("*:has-text('Tizimga kirish'):not(:has-text('sahifasiga'))").locator("button, svg, i, span.cursor-pointer").last
                                if copy_locator.count() > 0 and copy_locator.is_visible():
                                    copy_locator.click(force=True)
                            except Exception:
                                pass
                            time.sleep(1)

                            # 2. Buferga (clipboard) tushgan toza loginni olamiz
                            copied = page.evaluate("""() => {
                                return window.__last_copied_login || '';
                            }""")
                            if not copied:
                                try:
                                    copied = page.evaluate("() => navigator.clipboard.readText()")
                                except Exception:
                                    pass

                            if copied and isinstance(copied, str) and copied.strip():
                                cand = copied.strip()
                                if cand.lower() not in ["sahifasiga", "qaytish"]:
                                    pnfl = cand
                                    print(f"[CLIPBOARD COPIED SUCCESS] 📋 Kopiya tugmasidan toza login olindi: {pnfl}", flush=True)

                            # 3. Zaxira sifatida element matnini ham tekshirib qo'yamiz:
                            if not pnfl:
                                cand = page.evaluate("""() => {
                                    const allEls = Array.from(document.querySelectorAll('*'));
                                    const container = allEls.find(el => el.innerText && el.innerText.includes('Tizimga kirish') && !el.innerText.includes('sahifasiga'));
                                    if (container) {
                                        const clean = container.innerText.replace('Tizimga kirish', '').trim().split(/\\s+/);
                                        return clean[0] || null;
                                    }
                                    return null;
                                }""")
                                if cand and cand.lower() not in ["sahifasiga", "qaytish"]:
                                    pnfl = cand.strip()
                                    print(f"[FALLBACK DOM USERNAME] Login olindi: {pnfl}", flush=True)
                        except Exception as e_clip:
                            print(f"[COPY BUTTON ERROR] {e_clip}", flush=True)

                    detected_login = str(pnfl).strip() if pnfl else target_email

                    # Login va parollarni tekshirish
                    candidate_passwords = []
                    db_rec_chk = get_student_from_db(seria, number)
                    known_pwd = (db_rec_chk.get("password") or "") if db_rec_chk else ""
                    if not known_pwd and student.get("existing_password"):
                        known_pwd = student["existing_password"]
                    if known_pwd:
                        candidate_passwords.append(known_pwd)

                    # Agar login bizning bot ochgan login bo'lsa (maktab. bilan boshlansa)
                    if "maktab." in detected_login.lower():
                        if student_password and student_password not in candidate_passwords:
                            candidate_passwords.append(student_password)
                        if name_parts:
                            alt_pwd = f"{name_parts[0]}{birth_year}"
                            if alt_pwd not in candidate_passwords:
                                candidate_passwords.append(alt_pwd)
                        # Zaxira yil variantlari
                        if f"{first_name}2014" not in candidate_passwords:
                            candidate_passwords.append(f"{first_name}2014")
                        if f"{first_name}2015" not in candidate_passwords:
                            candidate_passwords.append(f"{first_name}2015")
                        if "Maktab29" not in candidate_passwords:
                            candidate_passwords.append("Maktab29")

                    # Saytdagi loginning o'zini parol sifatida sinash (Login = Parol):
                    if detected_login and detected_login not in candidate_passwords:
                        candidate_passwords.append(detected_login)

                    # Ehtimoliy parollar bilan tizimga kirishni sinab ko'ramiz
                    logged_in = False
                    for try_pwd in candidate_passwords:
                        print(f"[TRY BOT PASSWORD] Login: {detected_login}, Parol: {try_pwd} sinab ko'rilmoqda...", flush=True)
                        login_token = perform_safe_login(page, detected_login, try_pwd, name=name)
                        if login_token:
                            notify(f"⚡ [{name}] Tizimga muvaffaqiyatli kirildi! ({try_pwd})")
                            token = login_token
                            target_email = detected_login
                            default_password = try_pwd
                            registration_success = True
                            logged_in = True
                            save_student_to_db(seria, number, {
                                "name": name,
                                "birthdate": birthdate_digits,
                                "seria": seria,
                                "number": number,
                                "login": detected_login,
                                "password": try_pwd,
                                "status": "LOGGED_IN"
                            })
                            break

                    if logged_in:
                        break

                    # AGAR PAROL BO'LMASA YOKI MOS KELMASA:
                    # Begona loginlar yoki paroli noma'lumlar tiklanmaydi, 1 soniyada tashlab ketiladi:
                    browser.close()
                    save_student_to_db(seria, number, {
                        "name": name,
                        "birthdate": birthdate_digits,
                        "seria": seria,
                        "number": number,
                        "login": detected_login,
                        "status": "ALREADY_REGISTERED_NO_PASSWORD"
                    })
                    msg_no_pwd = f"Allaqachon ro'yxatdan o'tgan (Login: {detected_login}, Parol yo'q)"
                    notify(f"⚠️ [{name}] {msg_no_pwd}. Tashlab ketilmoqda...")
                    return False, None, detected_login, "", msg_no_pwd

                if not is_new_student and not is_already_registered:
                    if student_cycle < 3:
                        switch_ip()
                        continue
                    browser.close()
                    notify(f"❌ [{name}] Ro'yxatdan o'tish oynasiga o'tib bo'lmadi (Kapcha yechilmadi)")
                    return False, None, "", "", "Ro'yxatdan o'tish oynasiga o'tib bo'lmadi (Kapcha yechilmadi)"

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
                    clean_attempts = 0
                    max_clean_attempts = 2
                    session_rotations = 0

                    while clean_attempts < max_clean_attempts and session_rotations < 3:
                        session_rotations += 1
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

                            notify(f"📩 [{name}] Telegram botdan (@aistudy_uz_bot) tasdiqlash kodi olinmoqda ...")
                            code, session_used = get_telegram_verification_code()
                            student_idle_start = time.time()  # Kod kelgach taymer yangilanadi
                            if code:
                                notify(f"📩 [{name}] Yangi kod olindi: {code} (Raqam: {session_used}). Kiritilmoqda...")
                            if not code:
                                time.sleep(3)
                                code, session_used = get_telegram_verification_code()
                                student_idle_start = time.time()
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
                            # Agar sahifada 'qayta yuborish' tugmasi bo'lsa va 1-urinish bo'lsa, bosib ko'ramiz:
                            has_resend = False
                            if session_rotations < 2:
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

                        if is_limited:
                            # LIMIT HISOBLANMAYDI! Cheklovga uchragan sessiya darhol chetlatiladi va yangi sessiyaga o'tiladi
                            notify(f"⚠️ [{name}] {session_used} raqami limitga yetgan, butunlay chetlatildi. Yangi sessiyadan kod olinmoqda...")
                            mark_session_exhausted(session_used, reason="Bitta raqam cheklovi")
                            code = None
                            session_used = None
                            try:
                                resend_btn = page.locator("button:has-text('qayta'), a:has-text('qayta')")
                                if resend_btn.count() > 0 and resend_btn.first.is_visible():
                                    resend_btn.first.click(force=True)
                                    time.sleep(2)
                            except Exception:
                                pass
                            continue  # LIMIT HISOBLANMAYDI (clean_attempts oshirilmaydi)

                        if is_invalid:
                            clean_attempts += 1
                            notify(f"⚠️ [{name}] Kod xato yoki eskirgan ({clean_attempts}/3 toza urinish)...")
                            code = None
                            session_used = None
                            try:
                                resend_btn = page.locator("a:has-text('qayta yuborish'), button:has-text('qayta yuborish'), *:has-text('qayta yuborish')")
                                if resend_btn.count() > 0 and resend_btn.first.is_visible():
                                    resend_btn.first.click(force=True)
                                    time.sleep(1)
                            except Exception:
                                pass
                            continue

                        if registration_success:
                            break
                        else:
                            clean_attempts += 1
                            print(f"[VERIFY RETRY] 15 soniyada serverdan tasdiq kelmadi ({clean_attempts}/3), qayta urinilmoqda...")

                    if registration_success:
                        break

                    if retry_this_student:
                        continue

            if not registration_success and not token:
                browser.close()
                notify(f"❌ [{name}] Ro'yxatdan o'tib bo'lmadi")
                return False, None, "", "", "Ro'yxatdan o'tib bo'lmadi"

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
                    fail_msg = f"Kirish amalga oshmadi ({LAST_LOGIN_ERROR})" if LAST_LOGIN_ERROR else "Kirish amalga oshmadi"
                    notify(f"⚠️ [{name}] '{target_email}' kirib bo'lmadi ({LAST_LOGIN_ERROR or 'Xatolik'}). Keyingi o'quvchiga o'tilmoqda...")
                    return False, None, target_email, default_password, fail_msg

        # Agar token yo'q bo'lsa
        if not token:
            browser.close()
            notify(f"❌ [{name}] Tizimga kirishda token olinmadi")
            return False, None, target_email, default_password, "Tizimga kirishda token olinmadi"

        notify(f"🔓 [{name}] Tizimga muvaffaqiyatli kirildi! Kurslar boshlandi...")
        disconnect_warp() # VPN ni o'chirish - TAS-IX ichki tarmoq maksimal tezlikda darslarni yopadi!
        browser.close()
        return True, token, target_email, default_password, ""


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
        browser = launch_universal_browser(p, headless=False)
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            locale="en-US",
            permissions=["clipboard-read", "clipboard-write"],
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        context.add_init_script("""
            window._sys_dt_bypass = true;
            window.__last_copied_login = '';
            if (navigator.clipboard && navigator.clipboard.writeText) {
                const origWrite = navigator.clipboard.writeText.bind(navigator.clipboard);
                navigator.clipboard.writeText = async (text) => {
                    window.__last_copied_login = text;
                    return origWrite(text);
                };
            }
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

                # Metrika formasini to'ldirish (Google kapcha bloki urinishga hisoblanmaydi!)
                form_attempt = 1
                captcha_block_count = 0
                while form_attempt <= 3 and captcha_block_count < 10:
                    notify(f"📝 [{name}] Metrika kiritilmoqda ({seria} {number}) [Urinish: {student_cycle}.{form_attempt}]...")
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
                    page.evaluate("""() => {
                        const btns = Array.from(document.querySelectorAll('button, .btn-switch, .switch-item, [role="tab"], p-tab'));
                        const metr = btns.find(b => b.textContent && (b.textContent.includes("Tug'ilganlik") || b.textContent.includes('guvohnoma') || b.textContent.includes('Metrika')));
                        if (metr) {
                            metr.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));
                            metr.click();
                        }
                    }""")
                    time.sleep(1.5)

                    # Seriya katakchasi mavjudligini tekshirish
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

                    b_formatted = normalize_birthdate_for_input(cur_bdate)
                    page.evaluate("document.querySelectorAll('.telegram-popup-overlay, .devtools-overlay, .p-dialog-mask').forEach(e => e.remove());")
                    b_input = page.locator("input#birthdate, input[formcontrolname='birthdate'], input.p-datepicker-input").first
                    b_input.click(force=True)
                    b_input.fill("")
                    b_input.fill(b_formatted)
                    b_input.press("Tab")
                    page.evaluate("() => { if (document.activeElement) document.activeElement.blur(); }")
                    time.sleep(1.0)

                    # reCAPTCHA ni AI bilan yechish
                    notify(f"🎧 [{name}] reCAPTCHA Whisper AI orqali yechilmoqda ({form_attempt}/3)...")
                    captcha_solved = handle_recaptcha(page)
                    student_idle_start = time.time()  # Kapchadan keyin taymer yangilanadi

                    if not captcha_solved:
                        captcha_block_count += 1
                        print(f"[RECAPTCHA TRY AGAIN LATER] Google kapcha bloki! Bu 3 martalik limitga hisoblanmaydi ({captcha_block_count}). Toza IP olinmoqda...")
                        notify(f"⏳ [{name}] Google kapcha bloki! Yangi toza IP olinmoqda (Urinish kuymaydi: {form_attempt}/3)...")
                        switch_ip()
                        time.sleep(3)
                        continue  # E'tibor bering: form_attempt oshmaydi!

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
                        print(f"[STEP 1 RETRY] Serverdan javob kelmadi, qayta urinilmoqda ({form_attempt}/3)...", flush=True)
                        notify(f"⏳ [{name}] Server javobi kechikmoqda, qayta urinilmoqda ({form_attempt}/3)...")
                        form_attempt += 1  # Faqat server javob bermaganda urinish oshadi!
                        time.sleep(2)
                        continue

                if has_error:
                    browser.close()
                    notify(f"❌ [{name}] Metrika davlat bazasida topilmadi ({seria} {number})")
                    return False, "Metrika davlat bazasida topilmadi (No content)", "", ""

                if is_already_registered:
                    pnfl_matches = re.findall(r'\b\d{14}\b', content)
                    pnfl = pnfl_matches[0] if pnfl_matches else None
                    if not pnfl:
                        try:
                            all_text = page.locator("body").inner_text()
                            m14 = re.findall(r'\b\d{14}\b', all_text)
                            if m14:
                                pnfl = m14[0]
                        except Exception:
                            pass

                    # AGAR 14 xonali PINFL bo'lmasa, saytdagi login yonidagi 📋 kopiya tugmasini 1 marta bosib buferdan olamiz!
                    if not pnfl:
                        try:
                            # 1. Saytdagi 📋 nusxa olish (kopy) tugmasini 1 marta bosamiz
                            page.evaluate("""() => {
                                const allEls = Array.from(document.querySelectorAll('*'));
                                const container = allEls.find(el => el.innerText && el.innerText.includes('Tizimga kirish') && !el.innerText.includes('sahifasiga'));
                                if (container) {
                                    const btn = container.querySelector('button, svg, [role="button"], span.cursor-pointer, i') || container;
                                    btn.click();
                                }
                            }""")
                            try:
                                copy_locator = page.locator("*:has-text('Tizimga kirish'):not(:has-text('sahifasiga'))").locator("button, svg, i, span.cursor-pointer").last
                                if copy_locator.count() > 0 and copy_locator.is_visible():
                                    copy_locator.click(force=True)
                            except Exception:
                                pass
                            time.sleep(1)

                            # 2. Buferga (clipboard) tushgan toza loginni olamiz
                            copied = page.evaluate("""() => {
                                return window.__last_copied_login || '';
                            }""")
                            if not copied:
                                try:
                                    copied = page.evaluate("() => navigator.clipboard.readText()")
                                except Exception:
                                    pass

                            if copied and isinstance(copied, str) and copied.strip():
                                cand = copied.strip()
                                if cand.lower() not in ["sahifasiga", "qaytish"]:
                                    pnfl = cand
                                    print(f"[CLIPBOARD COPIED SUCCESS] 📋 Kopiya tugmasidan toza login olindi: {pnfl}", flush=True)

                            # 3. Zaxira sifatida element matnini ham tekshirib qo'yamiz:
                            if not pnfl:
                                cand = page.evaluate("""() => {
                                    const allEls = Array.from(document.querySelectorAll('*'));
                                    const container = allEls.find(el => el.innerText && el.innerText.includes('Tizimga kirish') && !el.innerText.includes('sahifasiga'));
                                    if (container) {
                                        const clean = container.innerText.replace('Tizimga kirish', '').trim().split(/\\s+/);
                                        return clean[0] || null;
                                    }
                                    return null;
                                }""")
                                if cand and cand.lower() not in ["sahifasiga", "qaytish"]:
                                    pnfl = cand.strip()
                                    print(f"[FALLBACK DOM USERNAME] Login olindi: {pnfl}", flush=True)
                        except Exception as e_clip:
                            print(f"[COPY BUTTON ERROR] {e_clip}", flush=True)

                    if pnfl:
                        # 1. Avval oddiy parollar bilan to'g'ridan-to'g'ri kirishni sinab ko'ramiz (2 soniyada kirib ketishi mumkin!)
                        direct_login_ok = False
                        if not str(pnfl).isdigit() or len(str(pnfl)) != 14:
                            first_part = name.split()[0].capitalize() if name else ""
                            byear = birthdate_digits[-4:] if len(birthdate_digits) >= 4 else "2014"
                            passwords_to_try = [default_password, "Maktab29", f"{first_part}{byear}", f"{first_part}2014", f"{first_part}2015"]
                            seen_pwd = []
                            for p_try in passwords_to_try:
                                if p_try and p_try not in seen_pwd:
                                    seen_pwd.append(p_try)
                            for p_try in seen_pwd:
                                print(f"[DIRECT LOGIN TRY] {pnfl} bilan {p_try} paroli tekshirilmoqda...", flush=True)
                                login_token = perform_safe_login(page, pnfl, p_try, name=name)
                                if login_token:
                                    print(f"[DIRECT LOGIN SUCCESS] {pnfl} to'g'ridan-to'g'ri tizimga kirdi!", flush=True)
                                    notify(f"⚡ [{name}] Mavjud login ({pnfl}) bilan to'g'ridan-to'g'ri tizimga kirildi!")
                                    token = login_token
                                    target_email = pnfl
                                    default_password = p_try
                                    registration_success = True
                                    direct_login_ok = True
                                    save_student_to_db(seria, number, {
                                        "name": name,
                                        "birthdate": birthdate_digits,
                                        "seria": seria,
                                        "number": number,
                                        "login": pnfl,
                                        "password": default_password,
                                        "status": "REGISTERED"
                                    })
                                    break

                        if direct_login_ok:
                            break

                        # 2. Agar to'g'ridan-to'g'ri kirmasa, tiklash orqali parolni yangilaymiz
                        notify(f"🔑 [{name}] Allaqachon ro'yxatdan o'tgan! Login/PINFL ({pnfl}) orqali hisob tiklanmoqda...")
                        rec_ok, rec_token = recover_and_login_student(page, pnfl, name=name, notify=notify, default_password=default_password)
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
                                "status": "REGISTERED"
                            })
                            break
                        else:
                            if rec_token == "personal_phone":
                                browser.close()
                                notify(f"⚠️ [{name}] Shaxsiy raqamga ulangan, bizning bazada yo'q. Tashlab ketilmoqda...")
                                return False, "Shaxsiy raqamga ulangan (Bazada yo'q)", "", ""
                            if student_cycle < 3:
                                print(f"[PINFL RETRY] Tiklashda kapcha bloki, IP yangilanib qayta urinilmoqda...")
                                switch_ip()
                                time.sleep(2)
                                continue
                            else:
                                browser.close()
                                notify(f"⚠️ [{name}] PINFL ({pnfl}) orqali hisobni tiklab bo'lmadi")
                                return False, "PINFL orqali tiklab bo'lmadi", "", ""
                    else:
                        browser.close()
                        notify(f"⚠️ [{name}] Bu o'quvchi ALLAQACHON ro'yxatdan o'tgan (PINFL topilmadi)!")
                        return False, "Allaqachon ro'yxatdan o'tgan (Login/Parol kerak)", "", ""

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
                    clean_attempts = 0
                    max_clean_attempts = 2
                    session_rotations = 0

                    while clean_attempts < max_clean_attempts and session_rotations < 3:
                        session_rotations += 1
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

                            notify(f"📩 [{name}] Telegram botdan (@aistudy_uz_bot) tasdiqlash kodi olinmoqda ...")
                            code, session_used = get_telegram_verification_code()
                            student_idle_start = time.time()  # Kod kelgach taymer yangilanadi
                            if code:
                                notify(f"📩 [{name}] Yangi kod olindi: {code} (Raqam: {session_used}). Kiritilmoqda...")
                            if not code:
                                time.sleep(3)
                                code, session_used = get_telegram_verification_code()
                                student_idle_start = time.time()
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
                            # Agar sahifada 'qayta yuborish' tugmasi bo'lsa va 1-urinish bo'lsa, bosib ko'ramiz:
                            has_resend = False
                            if session_rotations < 2:
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

                        if is_limited:
                            # LIMIT HISOBLANMAYDI! Cheklovga uchragan sessiya darhol chetlatiladi va yangi sessiyaga o'tiladi
                            notify(f"⚠️ [{name}] {session_used} raqami limitga yetgan, butunlay chetlatildi. Yangi sessiyadan kod olinmoqda...")
                            mark_session_exhausted(session_used, reason="Bitta raqam cheklovi")
                            code = None
                            session_used = None
                            try:
                                resend_btn = page.locator("button:has-text('qayta'), a:has-text('qayta')")
                                if resend_btn.count() > 0 and resend_btn.first.is_visible():
                                    resend_btn.first.click(force=True)
                                    time.sleep(2)
                            except Exception:
                                pass
                            continue  # LIMIT HISOBLANMAYDI (clean_attempts oshirilmaydi)

                        if is_invalid:
                            clean_attempts += 1
                            notify(f"⚠️ [{name}] Kod xato yoki eskirgan ({clean_attempts}/3 toza urinish)...")
                            code = None
                            session_used = None
                            try:
                                resend_btn = page.locator("a:has-text('qayta yuborish'), button:has-text('qayta yuborish'), *:has-text('qayta yuborish')")
                                if resend_btn.count() > 0 and resend_btn.first.is_visible():
                                    resend_btn.first.click(force=True)
                                    time.sleep(1)
                            except Exception:
                                pass
                            continue

                        if registration_success:
                            break
                        else:
                            clean_attempts += 1
                            print(f"[VERIFY RETRY] 15 soniyada serverdan tasdiq kelmadi ({clean_attempts}/3), qayta urinilmoqda...")

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
                    fail_msg = f"Kirish amalga oshmadi ({LAST_LOGIN_ERROR})" if LAST_LOGIN_ERROR else "Kirish amalga oshmadi"
                    notify(f"⚠️ [{name}] '{target_email}' kirib bo'lmadi ({LAST_LOGIN_ERROR or 'Xatolik'}). Keyingi o'quvchiga o'tilmoqda...")
                    return False, fail_msg, target_email, default_password

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
    """Excel faylni qabul qilib, barcha o'quvchilarga sertifikat olib berish (Parallel konveyer bilan)"""
    excel_start_time = time.time()
    wb = openpyxl.load_workbook(excel_path)
    sheet = wb.active

    col_widths = {c: sheet.column_dimensions[openpyxl.utils.get_column_letter(c)].width for c in range(1, 15) if openpyxl.utils.get_column_letter(c) in sheet.column_dimensions}
    h_row = 1
    h_vals = [sheet.cell(h_row, c).value for c in range(1, 15)]
    name_col = next((idx_c for idx_c, v in enumerate(h_vals, 1) if v and any(x in str(v).lower() for x in ["f.i.sh", "fish", "ism", "familiya", "fio"])), 2)
    bdate_col = next((idx_c for idx_c, v in enumerate(h_vals, 1) if v and any(x in str(v).lower() for x in ["tug'ilgan", "bdate", "birth", "sana"])), 3)
    seria_col = next((idx_c for idx_c, v in enumerate(h_vals, 1) if v and any(x in str(v).lower() for x in ["seriya", "series", "ser"])), 4)
    num_col = next((idx_c for idx_c, v in enumerate(h_vals, 1) if v and any(x in str(v).lower() for x in ["raqam", "number", "num"])), 5)
    sinf_col = next((idx_c for idx_c, v in enumerate(h_vals, 1) if v and any(x in str(v).lower() for x in ["sinf", "class"])), 6)
    cert_col = next((idx_c for idx_c, v in enumerate(h_vals, 1) if v and any(x in str(v).lower() for x in ["sertifikat", "cert", "link"])), 7)
    email_col = next((idx_c for idx_c, v in enumerate(h_vals, 1) if v and any(x in str(v).lower() for x in ["email", "login", "foydalanuvchi"])), 8)
    pwd_col = next((idx_c for idx_c, v in enumerate(h_vals, 1) if v and any(x in str(v).lower() for x in ["parol", "password", "kod"])), 9)
    time_col = next((idx_c for idx_c, v in enumerate(h_vals, 1) if v and any(x in str(v).lower() for x in ["vaqt", "sarflangan", "duration"])), 10)

    # Sarlavhalarni to'g'ri o'rnatish
    sheet.cell(h_row, cert_col).value = "Sertifikat havolasi"
    sheet.cell(h_row, email_col).value = "Login (Email)"
    sheet.cell(h_row, pwd_col).value = "Parol"
    sheet.cell(h_row, time_col).value = "Sarflangan vaqt"

    valid_rows = []
    for r in range(2, sheet.max_row + 1):
        if sheet.cell(r, name_col).value:
            valid_rows.append(r)
    total_students = len(valid_rows)

    parallel_msg = f"⚡ <b>{PARALLEL_WORKERS} ta parallel oqimda</b> darslar va sertifikatlar olinadi..." if PARALLEL_WORKERS > 1 else "Ketma-ket rejimda ishlamoqda..."
    if update_callback:
        update_callback(f"📊 Buyurtma qabul qilindi: Jami <b>{total_students} ta</b> o'quvchi mavjud.\n{parallel_msg}")

    success_count = 0
    active_workers = []
    worker_results = []
    worker_lock = threading.Lock()

    def run_worker_task(student_data, row_idx, tok, em, pw, start_t, idx_label):
        try:
            def worker_notify(m):
                if update_callback:
                    if idx_label and not str(m).strip().startswith(idx_label.strip()):
                        update_callback(f"{idx_label} {m}")
                    else:
                        update_callback(m)

            cert_url = complete_student_courses_api(tok, student_data, notify=worker_notify)
            duration_str = format_duration(time.time() - start_t)
            if cert_url and "certificate?id=" in cert_url:
                with excel_lock:
                    w = openpyxl.load_workbook(excel_path)
                    s = w.active
                    s.cell(row_idx, cert_col).value = cert_url
                    s.cell(row_idx, cert_col).hyperlink = cert_url
                    s.cell(row_idx, cert_col).font = Font(color="0000FF", underline="single")
                    if em: s.cell(row_idx, email_col).value = em
                    if pw: s.cell(row_idx, pwd_col).value = pw
                    s.cell(row_idx, time_col).value = duration_str
                    w.save(excel_path)
                save_student_to_db(student_data["seria"], student_data["number"], {
                    "name": student_data["name"],
                    "birthdate": student_data["birthdate"],
                    "seria": student_data["seria"],
                    "number": student_data["number"],
                    "login": em,
                    "password": pw,
                    "certificate": cert_url,
                    "status": "COMPLETED"
                })
                with worker_lock:
                    worker_results.append((row_idx, True, cert_url))
                if update_callback:
                    update_callback(
                        f"{idx_label} ✅ <b>{student_data['name']}</b>: Sertifikat olindi!\n"
                        f"⏱ <b>Sarflangan vaqt:</b> {duration_str}\n"
                        f"🔗 {cert_url}"
                    )
                return True
            else:
                with excel_lock:
                    w = openpyxl.load_workbook(excel_path)
                    s = w.active
                    s.cell(row_idx, cert_col).value = "Olinmadi (Sertifikat topilmadi)"
                    s.cell(row_idx, time_col).value = duration_str
                    w.save(excel_path)
                with worker_lock:
                    worker_results.append((row_idx, False, "Sertifikat topilmadi"))
                if update_callback:
                    update_callback(
                        f"{idx_label} ⚠️ <b>{student_data['name']}</b>: Olinmadi (Sertifikat topilmadi)\n"
                        f"⏱ <b>Sarflangan vaqt:</b> {duration_str}"
                    )
                return False
        except Exception as e_w:
            print(f"[WORKER THREAD ERROR] {student_data['name']}: {e_w}")
            with worker_lock:
                worker_results.append((row_idx, False, str(e_w)))
            return False

    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, PARALLEL_WORKERS)) as executor:
        for idx, r in enumerate(valid_rows, 1):
            # Bekor qilish (Otmen) tekshiruvi:
            cancel_flag = Path(__file__).resolve().parent / "cancel_order.flag"
            if cancel_flag.exists():
                print("[ORDER CANCELLED] Foydalanuvchi buyurtmani to'xtatdi (Otmen)!", flush=True)
                if update_callback:
                    update_callback("🛑 Buyurtma to'liq to'xtatildi (Otmen).")
                try: cancel_flag.unlink()
                except Exception: pass
                break

            idx_str = f"[{idx}/{total_students}]"
            name_val = sheet.cell(r, name_col).value
            if not name_val:
                continue

            student_start_time = time.time()

            raw_bdate = sheet.cell(r, bdate_col).value
            bdate_formatted = normalize_birthdate_for_input(raw_bdate)
            bdate_str = "".join(c for c in bdate_formatted if c.isdigit())

            seria = str(sheet.cell(r, seria_col).value or "").strip().upper()
            raw_num = str(sheet.cell(r, num_col).value or "").strip()
            num = raw_num.zfill(7) if len(raw_num) < 7 and raw_num.isdigit() else raw_num
            sinf = str(sheet.cell(r, sinf_col).value or "5-A").strip()

            # 1. Excelda allaqachon bormi?
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

            # 2. Bazadan tekshirish
            db_rec = get_student_from_db(seria, num)
            cert_link = (db_rec.get("certificate") or db_rec.get("cert_url") or "") if db_rec else ""
            if cert_link and "certificate?id=" in cert_link:
                sheet.cell(r, cert_col).value = cert_link
                sheet.cell(r, cert_col).hyperlink = cert_link
                sheet.cell(r, cert_col).font = Font(color="0000FF", underline="single")
                if db_rec.get("login"): sheet.cell(r, email_col).value = db_rec["login"]
                if db_rec.get("password"): sheet.cell(r, pwd_col).value = db_rec["password"]
                sheet.cell(r, time_col).value = "0 soniya (Bazada tayyor)"
                with excel_lock:
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

            student = {
                "name": str(name_val).strip(),
                "birthdate": bdate_str,
                "birthdate_formatted": bdate_formatted,
                "seria": seria,
                "number": num,
                "sinf": sinf,
                "index_str": idx_str
            }
            if db_rec and db_rec.get("login") and db_rec.get("password"):
                student["existing_login"] = db_rec["login"]
                student["existing_password"] = db_rec["password"]

            excel_login = str(sheet.cell(r, email_col).value or "").strip()
            excel_pwd = str(sheet.cell(r, pwd_col).value or "").strip()
            if excel_login and excel_pwd and excel_login.lower() not in ["none", "null", ""]:
                student["existing_login"] = excel_login
                student["existing_password"] = excel_pwd

            seria_clean = str(seria or "").replace(" ", "").replace("-", "").upper()
            has_account = bool(student.get("existing_login") and student.get("existing_password"))
            if not has_account and "FR" not in seria_clean:
                print(f"[SKIP NON-FR] {name_val} ({seria} {num}): Seriya I-FR emas, tashlab ketildi.")
                sheet.cell(r, cert_col).value = "Bazada yo'q (I-FR emas)"
                sheet.cell(r, time_col).value = "0 soniya (Tashlab ketildi)"
                with excel_lock:
                    wb.save(excel_path)
                if update_callback:
                    update_callback(
                        f"{idx_str} ⏭ <b>{name_val}</b> ({seria} {num})\n"
                        f"⚠️ Seriya 'I-FR' emas ({seria}) — bazada yo'q deb tashlab ketildi."
                    )
                continue

            # Parallel slotlar to'lgan bo'lsa, kamida 1 tasi bo'shashini kutamiz:
            while len([f for f in active_workers if not f.done()]) >= PARALLEL_WORKERS:
                time.sleep(1.0)

            # Asosiy oqimda navbatdagi o'quvchini tizimga kiritamiz (Login yoki Ro'yxatdan o'tish):
            try:
                ok_log, token, email, pwd, err_msg = login_or_register_single_student(student, update_callback=update_callback)
            except Exception as e_login:
                print(f"[LOGIN PIPELINE ERROR] {name_val}: {e_login}")
                ok_log, token, email, pwd, err_msg = False, None, "", "", str(e_login)

            if not ok_log or not token:
                st_dur_str = format_duration(time.time() - student_start_time)
                with excel_lock:
                    w = openpyxl.load_workbook(excel_path)
                    s = w.active
                    s.cell(r, time_col).value = st_dur_str
                    if "Allaqachon" in str(err_msg):
                        s.cell(r, cert_col).value = f"⚠️ {err_msg}" if not str(err_msg).startswith("⚠️") else err_msg
                        if email: s.cell(r, email_col).value = email
                        s.cell(r, pwd_col).value = "Parol yo'q"
                    else:
                        s.cell(r, cert_col).value = f"Olinmadi ({err_msg})"
                    w.save(excel_path)
                if update_callback:
                    update_callback(
                        f"{idx_str} ⚠️ <b>{student['name']}</b>: Olinmadi ({err_msg})\n"
                        f"⏱ <b>Sarflangan vaqt:</b> {st_dur_str}"
                    )
                continue

            # Login muvaffaqiyatli bo'lsa, darslarni yopish va sertifikat olishni fondagi parallel workerga topshiramiz:
            fut = executor.submit(run_worker_task, student, r, token, email, pwd, student_start_time, idx_str)
            active_workers.append(fut)
            CURRENT_ACTIVE_TOKEN_WORKERS = len([f for f in active_workers if not f.done()])
            if update_callback:
                update_callback(f"⚡ <b>{student['name']}</b>: Token olindi! Darslarni yopishga topshirildi (Orqa fonda: <b>{CURRENT_ACTIVE_TOKEN_WORKERS}/{PARALLEL_WORKERS}</b> faol)...")

            if PARALLEL_WORKERS <= 1:
                fut.result()

        concurrent.futures.wait(active_workers)

    for r_idx, is_ok, _ in worker_results:
        if is_ok:
            success_count += 1

    total_excel_duration = time.time() - excel_start_time
    with excel_lock:
        try:
            wb_final = openpyxl.load_workbook(excel_path)
            sh_main = wb_final.active
            sh_main.title = "Barcha o'quvchilar"

            # Zamonaviy styllar
            header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
            header_font = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
            success_fill = PatternFill(start_color="E2EFDA", end_color="E2EFDA", fill_type="solid")
            success_font = Font(name="Segoe UI", size=10, color="276A3C", bold=True)
            fail_fill = PatternFill(start_color="FCE4D6", end_color="FCE4D6", fill_type="solid")
            fail_font = Font(name="Segoe UI", size=10, color="C00000")
            link_font = Font(name="Segoe UI", size=10, color="0563C1", underline="single", bold=True)
            data_font = Font(name="Segoe UI", size=10)
            thin_border = Border(
                left=Side(style='thin', color='D9D9D9'),
                right=Side(style='thin', color='D9D9D9'),
                top=Side(style='thin', color='D9D9D9'),
                bottom=Side(style='thin', color='D9D9D9')
            )
            center_align = Alignment(horizontal="center", vertical="center")
            left_align = Alignment(horizontal="left", vertical="center")

            # 1. Barcha o'quvchilar ma'lumotlarini ajratib olamiz
            all_records = []
            for r_num in valid_rows:
                fio_val = sh_main.cell(r_num, name_col).value
                dob_val = sh_main.cell(r_num, bdate_col).value
                ser_val = sh_main.cell(r_num, seria_col).value
                num_val = sh_main.cell(r_num, num_col).value
                sinf_val = sh_main.cell(r_num, sinf_col).value
                cert_val = str(sh_main.cell(r_num, cert_col).value or "").strip()
                email_val = sh_main.cell(r_num, email_col).value
                pwd_val = sh_main.cell(r_num, pwd_col).value
                time_val = sh_main.cell(r_num, time_col).value
                is_cert_ok = bool(cert_val and "certificate?id=" in cert_val)

                # Agar katakda sertifikat yozilmay qolgan bo'lsa, bazadan to'ldiramiz (Parallel oqimlar bazaga 100% yozadi):
                if not is_cert_ok:
                    db_rec = get_student_from_db(ser_val, num_val)
                    if db_rec and db_rec.get("certificate") and "certificate?id=" in db_rec["certificate"]:
                        cert_val = db_rec["certificate"]
                        if not email_val and db_rec.get("login"): email_val = db_rec["login"]
                        if not pwd_val and db_rec.get("password"): pwd_val = db_rec["password"]
                        if not time_val: time_val = "Tayyor"
                        is_cert_ok = True

                all_records.append({
                    "fio": fio_val,
                    "dob": dob_val,
                    "ser": ser_val,
                    "num": num_val,
                    "sinf": sinf_val,
                    "cert": cert_val,
                    "email": email_val,
                    "pwd": pwd_val,
                    "time": time_val,
                    "is_cert_ok": is_cert_ok
                })

            # 2. Sertifikat olganlarni TEPAGA, olmaganlarni PASTGA saralaymiz
            certs_list = [r for r in all_records if r["is_cert_ok"]]
            no_certs_list = [r for r in all_records if not r["is_cert_ok"]]
            sorted_records = certs_list + no_certs_list

            # Bosh sahifa Header
            headers_main = ["T/r", "F.I.SH (Familiya Ism Sharif)", "Tug'ilgan sana", "Metrika seriyasi", "Metrika raqami", "Sinf", "Sertifikat havolasi / Holati", "Login (Email)", "Parol", "Sarflangan vaqt"]
            sh_main.row_dimensions[1].height = 28
            for col_i, h_text in enumerate(headers_main, 1):
                cell = sh_main.cell(1, col_i, h_text)
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = center_align
                cell.border = thin_border

            # 2-VARAQ: "Qayta ishlash kerak" (Muammoli o'quvchilar alohida jadvali)
            if "Qayta ishlash kerak" in wb_final.sheetnames:
                del wb_final["Qayta ishlash kerak"]
            sh_fail = wb_final.create_sheet(title="Qayta ishlash kerak")
            sh_fail.row_dimensions[1].height = 28
            for col_i, h_text in enumerate(headers_main, 1):
                cf = sh_fail.cell(1, col_i, h_text)
                cf.fill = PatternFill(start_color="C00000", end_color="C00000", fill_type="solid")
                cf.font = header_font
                cf.alignment = center_align
                cf.border = thin_border

            # 3. 1 dan boshlab uzilishsiz ketma-ket jadvalni to'ldiramiz
            cur_row = 2
            fail_row = 2
            for idx, rec in enumerate(sorted_records, 1):
                row_fill = success_fill if rec["is_cert_ok"] else fail_fill
                row_font = success_font if rec["is_cert_ok"] else fail_font

                sh_main.row_dimensions[cur_row].height = 22
                sh_main.cell(cur_row, 1, idx).alignment = center_align
                sh_main.cell(cur_row, 2, rec["fio"]).alignment = left_align
                sh_main.cell(cur_row, 3, rec["dob"]).alignment = center_align
                sh_main.cell(cur_row, 4, rec["ser"]).alignment = center_align
                sh_main.cell(cur_row, 5, rec["num"]).alignment = center_align
                sh_main.cell(cur_row, 6, rec["sinf"]).alignment = center_align
            
                c_cert = sh_main.cell(cur_row, 7, rec["cert"])
                c_cert.alignment = center_align if not rec["is_cert_ok"] else left_align
                if rec["is_cert_ok"]:
                    c_cert.hyperlink = rec["cert"]
                    c_cert.font = link_font
                else:
                    c_cert.font = row_font

                sh_main.cell(cur_row, 8, rec["email"] or "").alignment = left_align
                sh_main.cell(cur_row, 9, rec["pwd"] or "").alignment = center_align
                sh_main.cell(cur_row, 10, rec["time"] or "").alignment = center_align

                for c_i in range(1, 11):
                    c_cell = sh_main.cell(cur_row, c_i)
                    c_cell.fill = row_fill
                    c_cell.border = thin_border
                    if c_i != 7:
                        c_cell.font = data_font

                # Muammolilarni 2-varaqqa nusxalash
                if not rec["is_cert_ok"]:
                    sh_fail.row_dimensions[fail_row].height = 22
                    for c_i in range(1, 11):
                        val = sh_main.cell(cur_row, c_i).value
                        cf = sh_fail.cell(fail_row, c_i, val)
                        cf.fill = fail_fill
                        cf.font = data_font
                        cf.border = thin_border
                        cf.alignment = left_align if c_i in (2, 8) else center_align
                    fail_row += 1

                cur_row += 1

            # 4. JADVAL PASTIDAGI JAMI VA XULOSA QATORLARI (FOOTER)
            total_cnt = len(sorted_records)
            certs_cnt = len(certs_list)
            no_certs_cnt = len(no_certs_list)
            p_ok = round((certs_cnt / total_cnt * 100), 1) if total_cnt > 0 else 0
            p_fail = round((no_certs_cnt / total_cnt * 100), 1) if total_cnt > 0 else 0

            cur_row += 1  # Bitta bo'sh ajratuvchi qator

            footer_data = [
                ("📊 JAMI O'QUVCHILAR SONI:", f"{total_cnt} nafar (100%)", "1F4E78", "D9E1F2"),
                ("🟢 SERTIFIKAT OLGAN O'QUVCHILAR:", f"{certs_cnt} nafar ({p_ok}%)", "276A3C", "E2EFDA"),
                ("⚠️ SERTIFIKAT OLMAGAN O'QUVCHILAR:", f"{no_certs_cnt} nafar ({p_fail}%)", "C00000", "FCE4D6")
            ]

            for lbl, val, t_col, bg_col in footer_data:
                sh_main.merge_cells(start_row=cur_row, start_column=1, end_row=cur_row, end_column=6)
                sh_main.cell(cur_row, 1, lbl).alignment = Alignment(horizontal="right", vertical="center")
                sh_main.cell(cur_row, 1).font = Font(name="Segoe UI", size=11, bold=True, color=t_col)

                sh_main.merge_cells(start_row=cur_row, start_column=7, end_row=cur_row, end_column=10)
                sh_main.cell(cur_row, 7, val).alignment = Alignment(horizontal="center", vertical="center")
                sh_main.cell(cur_row, 7).font = Font(name="Segoe UI", size=11, bold=True, color=t_col)

                f_fill = PatternFill(start_color=bg_col, end_color=bg_col, fill_type="solid")
                for c_idx in range(1, 11):
                    c_f = sh_main.cell(cur_row, c_idx)
                    c_f.fill = f_fill
                    c_f.border = thin_border

                sh_main.row_dimensions[cur_row].height = 24
                cur_row += 1

            # Ustun kengliklarini to'g'rilash (Auto-fit)
            perfect_widths = {
                1: 8,
                2: 36,
                3: 16,
                4: 16,
                5: 16,
                6: 10,
                7: 52,
                8: 34,
                9: 18,
                10: 22
            }
            for ws in [sh_main, sh_fail]:
                for c_idx, w_val in perfect_widths.items():
                    ws.column_dimensions[openpyxl.utils.get_column_letter(c_idx)].width = w_val

            wb_final.save(excel_path)

        except Exception as e_style:
            print(f"[EXCEL STYLING ERROR] {e_style}, asosiy natijalar saqlangan!", flush=True)
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
