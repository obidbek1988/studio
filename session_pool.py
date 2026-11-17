# -*- coding: utf-8 -*-
"""
5 MILLION SESSION POOL (CHEKSIZ 1 TA SESSIYA VA KONTAKT ALMASHTIRISH DVIGATELI)
Yangilangan sana: 17.11.2026

Prinsip:
1. Bitta asosiy Telegram sessiyasi tanlanadi (masalan: 998330072869 yoki tg_session).
2. @aistudy_uz_bot bitta kontakt raqamiga 5 ta o'quvchi limitini qo'ygan.
3. Har 5 ta o'quvchidan so'ng (yoki limit xabari kelganda):
   - '⚙️ Sozlamalar' -> '📞 Kontaktni o'zgartirish' bosiladi.
   - Yangi O'zbekiston raqami bilan kontakt kartasi (InputMediaContact) yuboriladi.
   - Bot yangi raqamni bir zumda qabul qilib, unga yangi 5 talik limit ochib beradi.
4. Natijada 1 TA TELEGRAM SESSIYASI CHEKSIZ (minglab bolalar uchun) to'xtovsiz ishlaydi!
"""

import os
import sys
import time
import json
import re
import random
import asyncio
import concurrent.futures
from telethon import TelegramClient
from telethon.tl.types import InputMediaContact

API_ID = 26521369
API_HASH = "fa2e0d37e50c4aa3d54c1537b0d88470"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SESSIONS_DIR = os.path.join(BASE_DIR, "sessions")
STATE_FILE = os.path.join(BASE_DIR, "session_pool_state.json")

def generate_random_uz_phone():
    """O'zbekiston prefikslari bo'yicha to'g'ri formatdagi tasodifiy raqam yaratish"""
    prefix = random.choice(["90", "91", "93", "94", "95", "97", "98", "99", "88", "33"])
    tail = f"{random.randint(1000000, 9999999)}"
    return f"+998{prefix}{tail}"

CONSUMED_CODES = set()
CONSUMED_MSG_IDS = set()

def invalidate_last_code(code=None, session_name=None):
    """Eskirgan yoki xato deb topilgan kod va kontaktni bekor qilish"""
    global CONSUMED_CODES
    if code:
        CONSUMED_CODES.add(str(code).strip())
    state = load_state()
    state["needs_contact_rotation"] = True
    state["contact_usage_count"] = 5
    save_state(state)
    print(f"[SESSION POOL] Kod bekor qilindi ({code}) va yangi kontakt talab qilindi!", flush=True)

def normalize_session_name(name):
    """Sessiya nomini tozalab, sof raqamlar ko'rinishiga keltiradi"""
    if not name:
        return ""
    name = str(name).strip()
    if name.endswith(".session"):
        name = name[:-8]
    digits = re.sub(r'\D', '', name)
    return digits if digits else name

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data
        except Exception:
            pass
    return {
        "active_session": "998330072869",
        "current_contact_phone": None,
        "contact_usage_count": 0,
        "needs_contact_rotation": False,
        "valid_sessions": [],
        "exhausted": [],
        "unauthorized": [],
        "success_counts": {}
    }

def _async_sync_state_to_gh(state_copy):
    tok = os.environ.get("GH_TOKEN")
    if not tok:
        return
    try:
        import requests, base64
        headers = {'Authorization': f'token {tok}', 'Accept': 'application/vnd.github.v3+json'}
        r = requests.get('https://api.github.com/repos/obidbek1988/studio-core/contents/session_pool_state.json', headers=headers, timeout=10)
        if r.status_code == 200:
            sha = r.json().get('sha')
            content_bytes = json.dumps(state_copy, indent=2, ensure_ascii=False).encode('utf-8')
            content_b64 = base64.b64encode(content_bytes).decode('utf-8')
            requests.put('https://api.github.com/repos/obidbek1988/studio-core/contents/session_pool_state.json', headers=headers, json={
                'message': 'Auto-sync session pool state (unlimited session)',
                'content': content_b64,
                'sha': sha,
                'branch': 'main'
            }, timeout=10)
    except Exception:
        pass

def save_state(state):
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[STATE SAVE ERROR] {e}")

    try:
        import threading
        state_copy = json.loads(json.dumps(state))
        threading.Thread(target=_async_sync_state_to_gh, args=(state_copy,), daemon=True).start()
    except Exception:
        pass

def get_candidate_sessions():
    """
    Aktiv sessiyani birinchi o'ringa qo'yadi.
    Har bir kompyuter yoki worker o'ziga biriktirilgan mustaqil sessiyadan foydalanadi.
    """
    state = load_state()
    primary = state.get("active_session")
    candidates = []
    if primary:
        clean_p = normalize_session_name(primary)
        if clean_p:
            candidates.append(clean_p)

    valid = state.get("valid_sessions", [])
    raw_unauth = state.get("unauthorized", [])
    unauth = {normalize_session_name(x) for x in raw_unauth if x}

    for s in valid:
        clean_s = normalize_session_name(s)
        if clean_s and clean_s not in unauth and clean_s not in candidates:
            candidates.append(clean_s)

    # Agar hech qanday sessiya bo'lmasa, zaxira tg_session yoki 998330072869
    if not candidates:
        if os.path.exists(os.path.join(BASE_DIR, "tg_session.session")):
            candidates.append("tg_session")
        else:
            candidates.append("998330072869")

    return candidates

def mark_session_unauthorized(session_name):
    state = load_state()
    clean = normalize_session_name(session_name)
    unauth = {normalize_session_name(x) for x in state.get("unauthorized", []) if x}
    if clean:
        unauth.add(clean)
    state["unauthorized"] = sorted(list(unauth))
    active = normalize_session_name(state.get("active_session"))
    if not active or active == clean:
        state["active_session"] = None
    save_state(state)
    print(f"[SESSION POOL] Sessiya NOFAOL (unauthorized): {clean} - Chetlatildi!", flush=True)

def mark_session_exhausted(session_name, reason="limit_reached"):
    """
    Cheksiz Telegram rejimida sessiya O'CHIRILMAYDI!
    Faqatgina keyingi gal yangi kontakt raqami ulanishi belgilanadi.
    """
    state = load_state()
    clean = normalize_session_name(session_name)
    print(f"[SESSION POOL] 5 talik limit yoki taqiq aniqlandi ({reason}). Sessiya: {clean} SAQLAB QOLINDI, yangi kontakt ulanadi!", flush=True)
    state["needs_contact_rotation"] = True
    state["contact_usage_count"] = 5
    save_state(state)

def record_session_success(session_name):
    state = load_state()
    clean = normalize_session_name(session_name)
    if not clean:
        clean = str(session_name)
    counts = state.get("success_counts", {})
    counts[clean] = counts.get(clean, 0) + 1
    state["success_counts"] = counts
    # Kontakt orqali o'tganlar soni
    state["contact_usage_count"] = state.get("contact_usage_count", 0) + 1
    if state["contact_usage_count"] >= 5:
        state["needs_contact_rotation"] = True
        print(f"[SESSION POOL] Ushbu kontakt 5 ta o'quvchini to'liq o'tkazdi. Keyingisi uchun yangi kontakt ulanadi!", flush=True)
    save_state(state)
    print(f"[SESSION POOL] {clean} orqali muvaffaqiyatli ro'yxatdan o'tdi (Jami: {counts[clean]} ta)", flush=True)

async def change_contact_in_bot(client, bot, new_phone=None):
    """
    @aistudy_uz_bot da kontaktni yangi raqamga almashtirish
    """
    if not new_phone:
        new_phone = generate_random_uz_phone()

    print(f"\n[UNLIMITED POOL] Yangi kontakt raqami biriktirilmoqda: {new_phone}...", flush=True)

    # 1. Sozlamalar tugmasi
    msgs = await client.get_messages(bot, limit=5)
    settings_clicked = False
    for m in msgs:
        if m.buttons:
            for row in m.buttons:
                for b in row:
                    bt = (b.text or "").lower()
                    if any(w in bt for w in ["sozlamalar", "settings", "⚙️"]):
                        try:
                            await b.click()
                            settings_clicked = True
                            print(f"[UNLIMITED POOL] '⚙️ Sozlamalar' bosildi", flush=True)
                            await asyncio.sleep(1.5)
                            break
                        except Exception: pass
                if settings_clicked: break
        if settings_clicked: break

    if not settings_clicked:
        await client.send_message(bot, "/start")
        await asyncio.sleep(1.5)
        msgs = await client.get_messages(bot, limit=3)
        for m in msgs:
            if m.buttons:
                for row in m.buttons:
                    for b in row:
                        bt = (b.text or "").lower()
                        if any(w in bt for w in ["sozlamalar", "settings", "⚙️"]):
                            try:
                                await b.click()
                                settings_clicked = True
                                await asyncio.sleep(1.5)
                                break
                            except Exception: pass
                    if settings_clicked: break
            if settings_clicked: break

    # 2. Kontaktni o'zgartirish tugmasi
    msgs = await client.get_messages(bot, limit=3)
    change_clicked = False
    for m in msgs:
        if m.buttons:
            for row in m.buttons:
                for b in row:
                    bt = (b.text or "").lower()
                    if any(w in bt for w in ["kontaktni", "change contact", "raqamni"]):
                        try:
                            await b.click()
                            change_clicked = True
                            print(f"[UNLIMITED POOL] '📞 Kontaktni o'zgartirish' bosildi", flush=True)
                            await asyncio.sleep(1.5)
                            break
                        except Exception: pass
                if change_clicked: break
        if change_clicked: break

    # 3. Yangi kontakt kartasini yuborish
    contact = InputMediaContact(
        phone_number=new_phone,
        first_name="Talaba",
        last_name="",
        vcard=""
    )
    try:
        await client.send_file(bot, contact)
        print(f"[UNLIMITED POOL] Yangi kontakt kartasi yuborildi: {new_phone}", flush=True)
        await asyncio.sleep(2.0)
    except Exception as e_send:
        print(f"[UNLIMITED POOL] Kontakt yuborishda xatolik: {e_send}", flush=True)
        return False, None

    # Holatni saqlash
    state = load_state()
    state["current_contact_phone"] = new_phone
    state["contact_usage_count"] = 0
    state["needs_contact_rotation"] = False
    save_state(state)
    print(f"✅ [UNLIMITED POOL] Bot yangi raqamni qabul qildi: {new_phone} (Yangi 5 talik limit ochildi!)\n", flush=True)
    return True, new_phone

async def _fetch_from_one_session(session_name):
    # Sessiya yo'lini topish
    clean_name = normalize_session_name(session_name)
    session_path = None
    if session_name == "tg_session" or os.path.exists(os.path.join(BASE_DIR, f"{session_name}.session")):
        session_path = os.path.join(BASE_DIR, session_name)
    elif os.path.exists(os.path.join(SESSIONS_DIR, f"{clean_name}.session")):
        session_path = os.path.join(SESSIONS_DIR, clean_name)
    elif os.path.exists(os.path.join(SESSIONS_DIR, f"+{clean_name}.session")):
        session_path = os.path.join(SESSIONS_DIR, f"+{clean_name}")
    else:
        # To'g'ridan-to'g'ri izlash
        session_path = os.path.join(SESSIONS_DIR, session_name)

    c = TelegramClient(session_path, API_ID, API_HASH)
    try:
        await asyncio.wait_for(c.connect(), timeout=7.0)
        if not await c.is_user_authorized():
            print(f"[SESSION] {session_name} nofaol (unauthorized)", flush=True)
            await c.disconnect()
            return None, "unauthorized"

        me = await c.get_me()
        session_phone = f"+{me.phone}" if me and me.phone else session_name
        bot = await c.get_entity("@aistudy_uz_bot")

        # 1. Kontakt holatini tekshirish
        state = load_state()
        state["active_session"] = clean_name
        current_contact = state.get("current_contact_phone")
        usage_count = state.get("contact_usage_count", 0)
        needs_rotation = state.get("needs_contact_rotation", False) or (usage_count >= 5) or not current_contact

        if needs_rotation:
            print(f"[UNLIMITED POOL] Kontaktni yangilash talab etiladi (Hozirgi: {current_contact}, O'tilgan: {usage_count}/5)...", flush=True)
            ok, new_phone = await change_contact_in_bot(c, bot)
            if ok:
                current_contact = new_phone
                usage_count = 0
                state = load_state()

        # 2. 'Kod olish' tugmasini 1 marta bosish
        msgs = await c.get_messages(bot, limit=5)
        click_time = time.time()
        clicked = False
        for m in msgs:
            if m.buttons:
                for row in m.buttons:
                    for b in row:
                        bt = (b.text or "").lower()
                        if any(w in bt for w in ["tasdiqlash", "verification", "kod", "code", "retry", "qayta"]):
                            try:
                                await b.click()
                                clicked = True
                                print(f"[TG BOT CLICK] 'Kod olish' tugmasi bosildi ({b.text})", flush=True)
                                break
                            except Exception: pass
                    if clicked: break
            if clicked: break

        if not clicked:
            # Agar tugma ko'rinmasa /start yuborish
            await c.send_message(bot, "/start")
            await asyncio.sleep(1.5)
            msgs = await c.get_messages(bot, limit=3)
            for m in msgs:
                if m.buttons:
                    for row in m.buttons:
                        for b in row:
                            bt = (b.text or "").lower()
                            if any(w in bt for w in ["tasdiqlash", "verification", "kod", "code"]):
                                try:
                                    await b.click()
                                    clicked = True
                                    break
                                except Exception: pass
                        if clicked: break
                if clicked: break

        # 3. Kodni kutish va tahlil qilish
        for wait_s in range(1, 15):
            await asyncio.sleep(1.0)
            latest = await c.get_messages(bot, limit=3)
            for m in latest:
                if m.out:
                    continue
                if m.date.timestamp() < (click_time - 2):
                    continue

                txt = (m.text or "").strip()
                txt_low = txt.lower()

                # Kodni izlash (6 ta raqam)
                m_code = re.search(r'\b(\d{6})\b', txt)
                if m_code and any(w in txt_low for w in ["verification", "tasdiqlash", "code", "kod", "aistudy", "kodingiz", "👉"]):
                    found_code = m_code.group(1)
                    if found_code in CONSUMED_CODES or m.id in CONSUMED_MSG_IDS:
                        continue
                    code = found_code
                    CONSUMED_CODES.add(code)
                    CONSUMED_MSG_IDS.add(m.id)
                    phone_display = f"Sessiya: {session_phone} | Kontakt: {current_contact} ({usage_count + 1}/5)"
                    print(f"\n=======================================================", flush=True)
                    print(f"🎉 [TG KOD OLINDI] {code} [{phone_display}]", flush=True)
                    print(f"=======================================================\n", flush=True)
                    await c.disconnect()
                    return code, phone_display

                # Limitga yetganlik xabari
                if any(w in txt_low for w in ["limit", "cheklov", "faqat bitta", "bitta telefon", "kechirasiz", "mumkin emas"]):
                    print(f"⚠️ [TG BOT LIMIT] 5 talik limit aniqlandi! Avtomatik yangi kontaktga ulanmoqda...", flush=True)
                    ok, new_phone = await change_contact_in_bot(c, bot)
                    if ok:
                        current_contact = new_phone
                        usage_count = 0
                        # Yangi limit ochildi, darhol 'Kod olish'ni qayta bosamiz
                        await asyncio.sleep(1.5)
                        new_msgs = await c.get_messages(bot, limit=3)
                        for nm in new_msgs:
                            if nm.buttons:
                                for nr in nm.buttons:
                                    for nb in nr:
                                        if any(w in (nb.text or "").lower() for w in ["kod", "code", "verification", "tasdiqlash"]):
                                            await nb.click()
                                            break
                        # Keyingi 10 soniyada yangi kodni kutish
                        for _ in range(10):
                            await asyncio.sleep(1.0)
                            fresh = await c.get_messages(bot, limit=2)
                            for fm in fresh:
                                if not fm.out:
                                    fm_txt = fm.text or ""
                                    m_fresh = re.search(r'\b(\d{6})\b', fm_txt)
                                    if m_fresh:
                                        fresh_code = m_fresh.group(1)
                                        phone_display = f"Sessiya: {session_phone} | Kontakt: {new_phone} (1/5)"
                                        print(f"🎉 [TG KOD OLINDI (YANGI LIMIT)]: {fresh_code} [{phone_display}]", flush=True)
                                        await c.disconnect()
                                        return fresh_code, phone_display
                    await c.disconnect()
                    return None, "limit_exhausted"

        await c.disconnect()
        return None, "no_code"
    except Exception as e:
        try: await c.disconnect()
        except: pass
        return None, str(e)

def fetch_tg_code_from_pool(max_candidates=3):
    """
    Asosiy funksiya: 1 ta sessiyadan cheksiz kod olish.
    """
    candidates = get_candidate_sessions()
    if not candidates:
        print("[SESSION POOL] Faol sessiyalar topilmadi!", flush=True)
        return None, None

    for s_name in candidates[:max_candidates]:
        print(f"[SESSION POOL] Kod so'ralmoqda: {s_name}...", flush=True)
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                fut = pool.submit(lambda s: asyncio.run(_fetch_from_one_session(s)), s_name)
                code, status = fut.result(timeout=40.0)

            if code:
                phone_display = status if status and status != "ok" else s_name
                print(f"[SESSION POOL CODE] {phone_display} dan yangi kod olindi: [{code}]", flush=True)
                return code, phone_display
            elif status == "limit_exhausted":
                print(f"[SESSION POOL] {s_name} da kontakt almashtirildi, qayta urinilmoqda...", flush=True)
                mark_session_exhausted(s_name, reason="limit_exhausted")
            elif status == "unauthorized":
                print(f"[SESSION POOL] {s_name} nofaol sessiya, chetlatilmoqda...", flush=True)
                mark_session_unauthorized(s_name)
            else:
                print(f"[SESSION POOL INFO] {s_name}: @aistudy_uz_bot dan yangi kod kelmadi ({status}). Sessiya saqlab qolindi.", flush=True)
        except Exception as ex:
            print(f"[SESSION POOL WARNING] {s_name}: Aloqa uzildi yoki taymaut ({ex}). Sessiya saqlab qolindi.", flush=True)

    return None, None

def fetch_code_for_phone_ending(last_digits, timeout=30.0):
    """Tiklash jarayonida kod olish"""
    return fetch_tg_code_from_pool(max_candidates=2)

if __name__ == "__main__":
    code, s = fetch_tg_code_from_pool()
    print("NATIJA:", code, s)
