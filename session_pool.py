import os
import sys
import time
import json
import re
import asyncio
import concurrent.futures
from telethon import TelegramClient
from telethon.tl.types import InputMediaContact

API_ID = 26521369
API_HASH = "fa2e0d37e50c4aa3d54c1537b0d88470"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SESSIONS_DIR = os.path.join(BASE_DIR, "sessions")
STATE_FILE = os.path.join(BASE_DIR, "session_pool_state.json")

def normalize_session_name(name):
    """Sessiya nomini tozalab, sof raqamlar ko'rinishiga keltiradi (masalan: +998330497040 -> 998330497040)"""
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
                return json.load(f)
        except Exception:
            pass
    return {
        "active_session": None,
        "valid_sessions": [],
        "exhausted": [],
        "unauthorized": [],
        "success_counts": {}
    }

def save_state(state):
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[STATE SAVE ERROR] {e}")

def get_candidate_sessions():
    state = load_state()
    valid = state.get("valid_sessions", [])
    raw_exhausted = state.get("exhausted", [])
    raw_unauth = state.get("unauthorized", [])

    exhausted = {normalize_session_name(x) for x in raw_exhausted if x}
    unauth = {normalize_session_name(x) for x in raw_unauth if x}
    active = normalize_session_name(state.get("active_session"))

    candidates = []
    if active and active not in exhausted and active not in unauth:
        candidates.append(active)

    for s in valid:
        clean_s = normalize_session_name(s)
        if clean_s and clean_s not in exhausted and clean_s not in unauth and clean_s not in candidates:
            candidates.append(clean_s)

    if not candidates and os.path.exists(SESSIONS_DIR):
        for fn in os.listdir(SESSIONS_DIR):
            if fn.endswith(".session"):
                name = fn[:-8]
                clean_n = normalize_session_name(name)
                if clean_n and clean_n not in exhausted and clean_n not in unauth and clean_n not in candidates:
                    candidates.append(clean_n)
    return candidates

def mark_session_exhausted(session_name, reason="limit_reached"):
    state = load_state()
    clean = normalize_session_name(session_name)
    exhausted = {normalize_session_name(x) for x in state.get("exhausted", []) if x}
    if clean:
        exhausted.add(clean)
    state["exhausted"] = sorted(list(exhausted))

    active = normalize_session_name(state.get("active_session"))
    if not active or active == clean:
        state["active_session"] = None

    save_state(state)
    print(f"[SESSION POOL] Sessiya LIMITGA YETDI: {clean} ({reason}) - Sessiyalar ro'yxatidan butunlay chetlatildi!", flush=True)

def record_session_success(session_name):
    state = load_state()
    clean = normalize_session_name(session_name)
    if not clean:
        clean = str(session_name)
    counts = state.get("success_counts", {})
    counts[clean] = counts.get(clean, 0) + 1
    state["success_counts"] = counts
    save_state(state)
    print(f"[SESSION POOL] {clean} orqali ro'yxatdan o'tdi (Jami: {counts[clean]} ta)", flush=True)

async def _fetch_from_one_session(session_name):
    session_path = os.path.join(SESSIONS_DIR, session_name)
    c = TelegramClient(session_path, API_ID, API_HASH)
    try:
        await asyncio.wait_for(c.connect(), timeout=7.0)
        if not await c.is_user_authorized():
            print(f"[SESSION] {session_name} nofaol (unauthorized)", flush=True)
            await c.disconnect()
            return None, "unauthorized"

        me = await c.get_me()
        bot = await c.get_entity("@aistudy_uz_bot")

        # 1. Botga /start yuborib eng yangi menyuni olish
        try:
            await c.send_message(bot, "/start")
            await asyncio.sleep(1.0)
        except Exception:
            pass
        msgs = await c.get_messages(bot, limit=5)

        # Til tanlash bo'lsa
        for m in msgs:
            if m.buttons:
                for row in m.buttons:
                    for b in row:
                        if "UZB" in (b.text or "").upper():
                            try:
                                await b.click()
                                await asyncio.sleep(1)
                                msgs = await c.get_messages(bot, limit=5)
                            except: pass
                            break

        # Kontakt ulashish so'ralsa
        needs_contact = False
        for m in msgs:
            txt = (m.text or "").lower()
            if any(w in txt for w in ["telefon", "raqam", "kontakt", "share"]):
                needs_contact = True
                break
            if m.buttons:
                for row in m.buttons:
                    for b in row:
                        bt = (b.text or "").lower()
                        if any(w in bt for w in ["raqam", "telefon", "share", "kontakt"]):
                            needs_contact = True
                            break
                    if needs_contact: break
            if needs_contact: break

        if needs_contact and me.phone:
            contact = InputMediaContact(phone_number=me.phone, first_name=me.first_name or "User", last_name="", vcard="")
            try:
                await c.send_file(bot, contact)
                await asyncio.sleep(1.5)
                msgs = await c.get_messages(bot, limit=5)
            except: pass

        # Kod olish tugmasini 1 MARTA bosish
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
                                print(f"[TG BOT CLICK] ({session_name}) da 1 marta 'Kod olish' bosildi!", flush=True)
                                break
                            except: pass
                    if clicked: break
            if clicked: break

        # Kodni kutish - FAQAT tugma bosilgandan KEYIN kelgan yangi xabarni olamiz!
        phone_num = f"+{me.phone}" if me.phone else session_name
        for wait_s in range(1, 26):
            await asyncio.sleep(1)
            latest = await c.get_messages(bot, limit=3)
            for m in latest:
                if m.out:
                    continue
                # Tugma bosilgandan keyin kelgan xabar bo'lishi shart!
                if m.date.timestamp() < (click_time - 2):
                    continue

                txt = m.text or ""
                m_code = re.search(r'\b(\d{6})\b', txt)
                if m_code and any(w in txt.lower() for w in ["verification", "tasdiqlash", "code", "kod", "aistudy"]):
                    code = m_code.group(1)
                    print(f"\n=======================================================", flush=True)
                    print(f"[TG BOT XABAR] ({phone_num}) dan YANGI kod keldi: [{code}]", flush=True)
                    print(f"=======================================================\n", flush=True)
                    await c.disconnect()
                    return code, phone_num

        await c.disconnect()
        return None, "no_code"
    except Exception as e:
        try: await c.disconnect()
        except: pass
        return None, str(e)

def fetch_tg_code_from_pool(max_candidates=5):
    candidates = get_candidate_sessions()
    if not candidates:
        print("[SESSION POOL] Faol sessiyalar topilmadi!", flush=True)
        return None, None

    import concurrent.futures

    state = load_state()
    for s_name in candidates[:max_candidates]:
        print(f"[SESSION POOL] Tekshirilmoqda: {s_name}...", flush=True)
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                fut = pool.submit(lambda s: asyncio.run(_fetch_from_one_session(s)), s_name)
                code, status = fut.result(timeout=45.0)

            if code:
                phone_display = status if status and status != "ok" else s_name
                print(f"[SESSION POOL CODE] {phone_display} dan yangi kod olindi: [{code}]", flush=True)
                state["active_session"] = s_name
                save_state(state)
                return code, phone_display
            else:
                print(f"[SESSION POOL] {s_name} ({status}), navbatdagisiga o'tilmoqda...", flush=True)
                if status == "unauthorized":
                    unauth = set(state.get("unauthorized", []))
                    unauth.add(s_name)
                    state["unauthorized"] = list(unauth)
                    save_state(state)
        except Exception as ex:
            print(f"[SESSION POOL ERROR] {s_name}: {ex}", flush=True)

    return None, None

def fetch_code_for_phone_ending(last_digits, timeout=30.0):
    """Oxirgi 4 ta raqam bo'yicha sessiyani topib, undan kod olish (Tiklash uchun)"""
    last_digits = str(last_digits).strip()
    matched_sessions = []
    if os.path.exists(SESSIONS_DIR):
        for fn in os.listdir(SESSIONS_DIR):
            if fn.endswith(".session"):
                clean_name = fn[:-8]
                clean_digits = re.sub(r'\D', '', clean_name)
                if clean_digits.endswith(last_digits):
                    matched_sessions.append(clean_name)
    
    print(f"[RECOVERY POOL] Oxirgi {last_digits} bo'yicha topilgan sessiyalar: {matched_sessions}", flush=True)
    for s_name in matched_sessions:
        print(f"[RECOVERY] {s_name} sessiyasidan kod so'ralmoqda...", flush=True)
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                fut = executor.submit(lambda s=s_name: asyncio.run(_fetch_from_one_session(s)))
                code, status = fut.result(timeout=timeout)
            if code:
                phone_display = status if status and status != "ok" else s_name
                print(f"[RECOVERY SUCCESS] Kod olindi: [{code}] (Raqam: {phone_display})", flush=True)
                return code, phone_display
        except Exception as e:
            print(f"[RECOVERY ERROR] {s_name}: {e}", flush=True)

    # Agar aniq topilmasa, eng yangi faol sessiyalardan urinib ko'ramiz
    return fetch_tg_code_from_pool(max_candidates=4)

if __name__ == "__main__":
    code, s = fetch_tg_code_from_pool()
    print("FINAL CODE:", code, "from", s)
