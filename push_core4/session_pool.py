import os
import sys
import time
import json
import re
from telethon.sync import TelegramClient
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

def get_all_session_names():
    if not os.path.exists(SESSIONS_DIR):
        return []
    files = [f for f in os.listdir(SESSIONS_DIR) if f.endswith(".session")]
    names = [f[:-8] for f in files]
    names.sort()
    return names

def is_session_authorized(session_name):
    session_path = os.path.join(SESSIONS_DIR, session_name)
    client = None
    try:
        client = TelegramClient(session_path, API_ID, API_HASH)
        client.connect()
        auth = client.is_user_authorized()
        client.disconnect()
        return auth
    except Exception as e:
        print(f"[AUTH CHECK ERROR] {session_name}: {e}")
        if client:
            try:
                client.disconnect()
            except Exception:
                pass
        return False

def get_active_session():
    state = load_state()
    all_sessions = get_all_session_names()
    exhausted_set = set(state.get("exhausted", []))
    unauth_set = set(state.get("unauthorized", []))

    cur = state.get("active_session")
    if cur and cur not in exhausted_set and cur not in unauth_set:
        if is_session_authorized(cur):
            return cur
        else:
            print(f"[SESSION POOL] {cur} yaroqsiz (unauthorized), ro'yxatdan chiqarilmoqda...")
            unauth_set.add(cur)
            state["unauthorized"] = list(unauth_set)
            save_state(state)

    for s_name in all_sessions:
        if s_name in exhausted_set or s_name in unauth_set:
            continue
        print(f"[SESSION POOL] Yangi sessiya tekshirilmoqda: {s_name}...")
        if is_session_authorized(s_name):
            print(f"[SESSION POOL] Yangi aktiv sessiya tanlandi: {s_name}")
            state["active_session"] = s_name
            save_state(state)
            return s_name
        else:
            print(f"[SESSION POOL] {s_name} unauthorized, belgilandi.")
            unauth_set.add(s_name)
            state["unauthorized"] = list(unauth_set)
            save_state(state)

    print("[SESSION POOL ERROR] Barcha sessiyalar tugadi yoki yaroqsiz!")
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

def ensure_bot_ready(client, bot, me):
    """Bot bilan muloqotni (/start, til, kontakt ulashish) to'liq avtomatlashtiradi"""
    msgs = client.get_messages(bot, limit=5)
    
    # 1. Agar botda umuman xabar bo'lmasa yoki /start kerak bo'lsa
    if not msgs:
        client.send_message(bot, "/start")
        time.sleep(2)
        msgs = client.get_messages(bot, limit=5)

    # 2. Agar til tanlash so'ralgan bo'lsa
    for m in msgs:
        if m.buttons:
            for row in m.buttons:
                for b in row:
                    if "UZB" in (b.text or "").upper():
                        try:
                            b.click()
                            time.sleep(1.5)
                        except Exception:
                            pass
                        break

    # 3. Agar kontakt so'ralayotgan bo'lsa ("Send contact" yoki "Raqamni ulashish")
    msgs = client.get_messages(bot, limit=5)
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
        client.send_file(bot, contact)
        time.sleep(3)

def fetch_tg_code_from_pool(max_retries=10):
    """
    Faol sessiya orqali @aistudy_uz_bot dan tasdiqlash kodini oladi.
    Agar sessiya yaroqsiz bo'lsa, avtomatik keyingisiga o'tadi.
    """
    for attempt in range(max_retries):
        session_name = get_active_session()
        if not session_name:
            print("[SESSION POOL] Faol sessiya topilmadi!")
            return None, None

        session_path = os.path.join(SESSIONS_DIR, session_name)
        client = None
        try:
            client = TelegramClient(session_path, API_ID, API_HASH)
            client.connect()
            if not client.is_user_authorized():
                print(f"[SESSION POOL] {session_name} unauthorized!")
                client.disconnect()
                state = load_state()
                unauth = set(state.get("unauthorized", []))
                unauth.add(session_name)
                state["unauthorized"] = list(unauth)
                if state.get("active_session") == session_name:
                    state["active_session"] = None
                save_state(state)
                continue

            me = client.get_me()
            bot = client.get_entity("@aistudy_uz_bot")

            # Bot tayyorgarligi (start / contact / til)
            ensure_bot_ready(client, bot, me)

            initial_msgs = client.get_messages(bot, limit=1)
            last_msg_id = initial_msgs[0].id if initial_msgs else 0

            # Kod olish tugmasini bosish
            messages = client.get_messages(bot, limit=5)
            clicked = False
            for msg in messages:
                if msg.buttons:
                    for row in msg.buttons:
                        for b in row:
                            t = (b.text or "").lower()
                            if "tasdiqlash" in t or "verification code" in t:
                                b.click()
                                clicked = True
                                break
                        if clicked:
                            break
                if clicked:
                    break

            if not clicked:
                client.send_message(bot, "/start")
                time.sleep(2)
                ensure_bot_ready(client, bot, me)
                msgs = client.get_messages(bot, limit=5)
                for m in msgs:
                    if m.buttons:
                        for row in m.buttons:
                            for b in row:
                                t = (b.text or "").lower()
                                if "tasdiqlash" in t or "verification code" in t:
                                    b.click()
                                    clicked = True
                                    break
                            if clicked:
                                break
                    if clicked:
                        break

            # Kod kelishini 20 soniya kutish
            code = None
            for _ in range(15):
                time.sleep(1.5)
                latest = client.get_messages(bot, limit=5)
                for msg in latest:
                    if msg.id > last_msg_id:
                        txt = msg.text or ""
                        match = re.search(r'\b(\d{6})\b', txt)
                        if match:
                            code = match.group(1)
                            break
                if code:
                    break

            client.disconnect()
            if code:
                print(f"[SESSION POOL CODE] {session_name} ({me.phone}) dan kod olindi: {code}")
                return code, session_name
            else:
                print(f"[SESSION POOL] {session_name} dan yangi kod kelmadi, qayta urinilmoqda...")
        except Exception as e:
            print(f"[SESSION POOL FETCH ERROR] {session_name}: {e}")
            if client:
                try:
                    client.disconnect()
                except Exception:
                    pass
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
    print("TEST FINAL RESULT:", code, "from session:", s)
