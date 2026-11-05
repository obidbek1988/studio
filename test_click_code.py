import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import asyncio
import re
from telethon import TelegramClient

API_ID = 2040
API_HASH = "b18441a1ff607e10a989891a5462e627"
SESSION_PATH = "5millionsertifikat/tg_session"

async def test_get_code():
    client = TelegramClient(SESSION_PATH, API_ID, API_HASH)
    await client.connect()
    bot = await client.get_entity('aistudy_uz_bot')
    
    print("Clicking '🔐 Tasdiqlash kodini olish'...")
    msgs = await client.get_messages(bot, limit=3)
    for m in msgs:
        if m.buttons:
            for row in m.buttons:
                for b in row:
                    if "Tasdiqlash kodini olish" in b.text:
                        await b.click()
                        print(f"Clicked button '{b.text}'!")
                        break
                        
    await asyncio.sleep(2)
    latest = await client.get_messages(bot, limit=2)
    for m in latest:
        print("Bot replied:", repr(m.text))
        match = re.search(r'(\d{6})', m.text or "")
        if match:
            print("🎯🎯🎯 6-XONALI KOD AVTOMAT OLINDI:", match.group(1))
            
    await client.disconnect()

asyncio.run(test_get_code())
