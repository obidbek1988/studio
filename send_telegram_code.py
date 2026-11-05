import sys
import asyncio
from telethon import TelegramClient

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Rasmiy Telegram API ma'lumotlari
API_ID = 2040
API_HASH = "b18441a1ff607e10a989891a5462e627"
PHONE = "+998910443271"
SESSION_PATH = "5millionsertifikat/tg_session"

async def main():
    print(f"📡 Telegram rasmiy serveriga xavfsiz ulanish: {PHONE}...", flush=True)
    client = TelegramClient(SESSION_PATH, API_ID, API_HASH)
    await client.connect()
    
    if await client.is_user_authorized():
        print("✅ Telegram allaqachon ulangan va tayyor!", flush=True)
        me = await client.get_me()
        print(f"👤 Akkaunt: {me.first_name} (@{me.username})", flush=True)
        await client.disconnect()
        return
        
    print(f"📩 {PHONE} raqamiga Telegram orqali 5 xonali tasdiqlash kodi yuborilmoqda...", flush=True)
    try:
        sent = await client.send_code_request(PHONE)
        print("✅ KOD MUVAFFAQIYATLI YUBORILDI!", flush=True)
        print(f"📌 Phone code hash: {sent.phone_code_hash}", flush=True)
        with open("5millionsertifikat/phone_code_hash.txt", "w") as f:
            f.write(sent.phone_code_hash)
    except Exception as e:
        print(f"❌ Xatolik: {e}", flush=True)
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
