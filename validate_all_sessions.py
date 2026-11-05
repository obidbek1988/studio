import os
import sys
import asyncio
import json
sys.stdout.reconfigure(encoding='utf-8')
from telethon import TelegramClient

API_ID = 26521369
API_HASH = "fa2e0d37e50c4aa3d54c1537b0d88470"

SESSIONS_DIR = r"d:\5millionbot\sessions"
files = [f for f in os.listdir(SESSIONS_DIR) if f.endswith(".session")]
print(f"Total session files in folder: {len(files)}")

async def check_session(f):
    name = f[:-8]
    full_path = os.path.join(SESSIONS_DIR, name)
    client = TelegramClient(full_path, API_ID, API_HASH)
    try:
        await client.connect()
        auth = await client.is_user_authorized()
        phone = ""
        user_name = ""
        if auth:
            me = await client.get_me()
            phone = me.phone or ""
            user_name = me.first_name or ""
        await client.disconnect()
        return name, auth, phone, user_name
    except Exception as e:
        try: await client.disconnect()
        except Exception: pass
        return name, False, "", str(e)

async def main():
    valid_sessions = []
    invalid_sessions = []
    
    # Check in batches of 10
    batch_size = 10
    for i in range(0, len(files), batch_size):
        batch = files[i:i+batch_size]
        tasks = [check_session(f) for f in batch]
        results = await asyncio.gather(*tasks)
        for name, auth, phone, info in results:
            if auth:
                print(f"[VALID] {name} -> Phone: {phone}, Name: {info}")
                valid_sessions.append(name)
            else:
                invalid_sessions.append(name)
        print(f"Progress: {min(i+batch_size, len(files))}/{len(files)} | Valid: {len(valid_sessions)} | Invalid: {len(invalid_sessions)}")

    print(f"\n==========================================")
    print(f"SCAN COMPLETED!")
    print(f"VALID ACTIVE SESSIONS: {len(valid_sessions)}")
    print(f"INVALID / EXPIRED SESSIONS: {len(invalid_sessions)}")
    print(f"==========================================")

    # Save to session_pool_state.json
    state_file = r"d:\5millionbot\session_pool_state.json"
    state = {
        "active_session": valid_sessions[0] if valid_sessions else None,
        "valid_sessions": valid_sessions,
        "exhausted": ["tg_session", "+998910443271", "998910443271"],
        "unauthorized": invalid_sessions,
        "success_counts": {}
    }
    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)
    print("Saved ready state to session_pool_state.json!")

if __name__ == "__main__":
    asyncio.run(main())
