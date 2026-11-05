import sys
import asyncio
from telethon import TelegramClient

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

API_ID = 2040
API_HASH = "b18441a1ff607e10a989891a5462e627"
PHONE = "+998910443271"
SESSION_PATH = "5millionsertifikat/tg_session"

async def login_with_code(code, password=None):
    with open("5millionsertifikat/phone_code_hash.txt", "r") as f:
        phone_code_hash = f.read().strip()
        
    client = TelegramClient(SESSION_PATH, API_ID, API_HASH)
    await client.connect()
    
    try:
        await client.sign_in(PHONE, code, phone_code_hash=phone_code_hash)
        print("🎉 TELEGRAM MUVAFFAQIYATLI ULANDI!", flush=True)
        me = await client.get_me()
        print(f"👤 Xush kelibsiz, {me.first_name}! (@{me.username})", flush=True)
        return True
    except Exception as e:
        if "Two-steps verification" in str(e) or "SessionPasswordNeededError" in str(type(e)):
            print("🔐 2-bosqichli parol (Two-step password) kerak!", flush=True)
            if password:
                await client.sign_in(password=password)
                print("🎉 2-bosqichli parol bilan muvaffaqiyatli ulandi!", flush=True)
                return True
        print(f"❌ Xato: {e}", flush=True)
        return False
    finally:
        await client.disconnect()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        code = sys.argv[1].strip()
        pwd = sys.argv[2].strip() if len(sys.argv) > 2 else None
        asyncio.run(login_with_code(code, pwd))
    else:
        print("Foydalanish: python complete_telegram_login.py <KOD> [2-BOSQICHLI_PAROL]")
