import sys
import asyncio
from telethon import TelegramClient

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

API_ID = 2040
API_HASH = "b18441a1ff607e10a989891a5462e627"
PHONE = "+998910443271"
SESSION_PATH = "5millionsertifikat/tg_session"

async def main():
    passwords = ["Obidbekqobilov@gmail,com", "Obidbekqobilov@gmail.com", "obidbekqobilov@gmail.com"]
    client = TelegramClient(SESSION_PATH, API_ID, API_HASH)
    await client.connect()
    
    for pwd in passwords:
        try:
            print(f"Parol sinab ko'rilmoqda: {pwd}...", flush=True)
            await client.sign_in(password=pwd)
            print("🎉🎉🎉 TELEGRAM 100% MUVAFFAQIYATLI ULANDI!", flush=True)
            me = await client.get_me()
            print(f"👤 Xush kelibsiz, {me.first_name}! (ID: {me.id}, @{me.username})", flush=True)
            await client.disconnect()
            return
        except Exception as e:
            print(f"Parol xatosi ({pwd}): {e}", flush=True)
            
    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
