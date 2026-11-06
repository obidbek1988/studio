import os
import sys
import time
import json
import re
import asyncio
from telethon import TelegramClient
from telethon.tl.types import InputMediaContact

API_ID = 26521369
API_HASH = "fa2e0d37e50c4aa3d54c1537b0d88470"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SESSIONS_DIR = os.path.join(BASE_DIR, "sessions")
STATE_FILE = os.path.join(BASE_DIR, "session_pool_state.json")

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

def get_active_session():
    state = load_state()
    valid_sessions = state.get("valid_sessions", [])
    exhausted_set = set(state.get("exhausted", []))
    unauth_set = set(state.get("unauthorized", []))

    cur = state.get("active_session")
    if cur and cur not in exhausted_set and cur not in unauth_set:
        return cur

    # 191 ta tekshirib tayyorlab qo'yilgan sessiyalar navbati
    for s_name in valid_sessions:
        if s_name in exhausted_set or s_name in unauth_set:
            continue
        print(f"[SESSION POOL] Yangi aktiv sessiya tanlandi: {s_name}")
        state["active_session"] = s_name
        save_state(state)
        return s_name

    print("[SESSION POOL ERROR] Barcha tayyor sessiyalar tugadi!")
    return None

def mark_session_exhausted(session_name, reason="limit_reached"):
    state = load_state()
    exhausted = set(state.get("exhausted", []))
    exhausted.add(session_name)
    state["exhausted"] = list(exhausted)
    if state.get("active_session") == session_name:
        state["active_session"] = None
    save_state(state)
    print(f"[SESSION POOL] Sessiya LIMITGA YETDI va ajratib qo'yildi: {session_name} ({reason})")

def record_session_success(session_name):
    state = load_state()
    counts = state.get("success_counts", {})
    counts[session_name] = counts.get(session_name, 0) + 1
    state["success_counts"] = counts
    save_state(state)
    print(f"[SESSION POOL] {session_name} orqali muvaffaqiyatli ro'yxatdan o'tdi (Jami: {counts[session_name]} ta)")

async def _async_ensure_bot_ready(client, bot, me):
    msgs = await client.get_messages(bot, limit=5)
    if not msgs:
        await client.send_message(bot, "/start")
        await asyncio.sleep(2)
        msgs = await client.get_messages(bot, limit=5)

    # Til tanlash (UZB)
    for m in msgs:
        if m.buttons:
            for row in m.buttons:
                for b in row:
                    if "UZB" in (b.text or "").upper():
                        try:
                            await b.click()
                            await asyncio.sleep(1.5)
                        except Exception:
                            pass
                        break

    # Kontakt ulashish (Send contact)
    msgs = await client.get_messages(bot, limit=5)
    needs_contact = False
    for m in msgs:
        if m.buttons:
            for row in m.buttons:
                for b in row:
                    txt = (b.text or "").lower()
                    if "contact" in txt or "raqam" in txt or "telefon" in txt:
                        needs_contact = True
                        break
        if "phone number" in (m.text or "").lower() or "raqamingiz" in (m.text or "").lower():
            needs_contact = True

    if needs_contact:
        print(f"[SESSION POOL] Botga kontakt ulashilmoqda: {me.phone}...")
        contact = InputMediaContact(
            phone_number=me.phone,
            first_name=me.first_name or "User",
            last_name=me.last_name or "",
            vcard=""
        )
        await client.send_file(bot, contact)
        await asyncio.sleep(2.5)

async def _async_fetch_code(session_name):
    from datetime import datetime, timezone
    session_path = os.path.join(SESSIONS_DIR, session_name)
    client = TelegramClient(session_path, API_ID, API_HASH)
    try:
        await client.connect()
        auth = await client.is_user_authorized()
        if not auth:
            print(f"[SESSION POOL] {session_name} unauthorized!")
            await client.disconnect()
            return None, "unauthorized"

        me = await client.get_me()
        bot = await client.get_entity("@aistudy_uz_bot")

        await _async_ensure_bot_ready(client, bot, me)

        initial_msgs = await client.get_messages(bot, limit=5)
        last_msg_id = initial_msgs[0].id if initial_msgs else 0
        now = datetime.now(timezone.utc)

        # 1. Agar so'nggi 75 soniya ichida kod allaqachon kelgan bo'lsa, uni darhol olamiz
        for msg in initial_msgs:
            if msg.date and (now - msg.date).total_seconds() < 75:
                txt = msg.text or ""
                m = re.search(r'\b(\d{6})\b', txt)
                if m and any(w in txt.lower() for w in ["verification", "tasdiqlash", "code", "kod"]):
                    code = m.group(1)
                    print(f"[SESSION POOL] Mavjud xabardan tayyor kod olindi: {code}")
                    await client.disconnect()
                    return code, "ok"

        # 2. Kod olish yoki Retry tugmasini bosish
        clicked = False
        for msg in initial_msgs:
            if msg.buttons:
                for row in msg.buttons:
                    for b in row:
                        t = (b.text or "").lower()
                        if any(w in t for w in ["tasdiqlash", "verification", "kod", "code", "retry", "qayta"]):
                            try:
                                await b.click()
                                clicked = True
                                break
                            except Exception:
                                pass
                    if clicked:
                        break
            if clicked:
                break

        if not clicked:
            await client.send_message(bot, "/start")
            await asyncio.sleep(1.5)
            await _async_ensure_bot_ready(client, bot, me)
            msgs = await client.get_messages(bot, limit=5)
            for m in msgs:
                if m.buttons:
                    for row in m.buttons:
                        for b in row:
                            t = (b.text or "").lower()
                            if any(w in t for w in ["tasdiqlash", "verification", "kod", "code", "retry", "qayta"]):
                                try:
                                    await b.click()
                                    clicked = True
                                    break
                                except Exception:
                                    pass
                        if clicked:
                            break
                if clicked:
                    break

        # 3. Yangi xabar kelishini 15 soniya kutish
        code = None
        for _ in range(12):
            await asyncio.sleep(1.2)
            latest = await client.get_messages(bot, limit=3)
            for msg in latest:
                if msg.id > last_msg_id or (msg.date and (datetime.now(timezone.utc) - msg.date).total_seconds() < 75):
                    txt = msg.text or ""
                    m = re.search(r'\b(\d{6})\b', txt)
                    if m and any(w in txt.lower() for w in ["verification", "tasdiqlash", "code", "kod"]):
                        code = m.group(1)
                        break
            if code:
                break

        await client.disconnect()
        return code, "ok"
    except Exception as e:
        try:
            await client.disconnect()
        except Exception:
            pass
        return None, str(e)

async def _fetch_with_timeout(session_name):
    try:
        return await asyncio.wait_for(_async_fetch_code(session_name), timeout=25.0)
    except asyncio.TimeoutError:
        print(f"[SESSION POOL] {session_name} 25 soniyada javob bermadi (Timeout)!")
        return None, "timeout"

def fetch_tg_code_from_pool(max_retries=10):
    """
    Aktiv sessiya orqali kod oladi. Barcha telethon chaqiruvlari toza asyncio orqali xatosiz ishlaydi.
    """
    for attempt in range(max_retries):
        session_name = get_active_session()
        if not session_name:
            print("[SESSION POOL] Faol sessiya topilmadi!")
            return None, None

        code, status = asyncio.run(_fetch_with_timeout(session_name))
        if code:
            print(f"[SESSION POOL CODE] {session_name} dan kod olindi: {code}")
            return code, session_name
        else:
            print(f"[SESSION POOL] {session_name} xatosi: {status}, keyingisiga o'tilmoqda...")
            state = load_state()
            unauth = set(state.get("unauthorized", []))
            unauth.add(session_name)
            state["unauthorized"] = list(unauth)
            if state.get("active_session") == session_name:
                state["active_session"] = None
            save_state(state)

    return None, None

if __name__ == "__main__":
    code, s = fetch_tg_code_from_pool()
    print("FINAL CODE:", code, "from", s)
