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
    
    msgs = await client.get_messages(bot, limit=3)
    # Check if language buttons present
    for m in msgs:
        if m.buttons:
            for row in m.buttons:
                for b in row:
                    if "UZB" in b.text:
                        print("Clicking UZB language button...")
                        await b.click()
                        await asyncio.sleep(2)
                        break
                        
    # Now check latest message for "Tasdiqlash kodini olish"
    msgs = await client.get_messages(bot, limit=3)
    for m in msgs:
        print("Msg text:", repr(m.text))
        if m.buttons:
            for row in m.buttons:
                for b in row:
                    print("Button:", b.text)
                    if "Tasdiqlash kodini olish" in b.text or "kodini olish" in b.text or "kod" in b.text.lower():
                        print("Clicking 'Tasdiqlash kodini olish'...")
                        await b.click()
                        await asyncio.sleep(2)
                        break
                        
    # Get reply
    msgs = await client.get_messages(bot, limit=3)
    for m in msgs:
        print("Latest text:", repr(m.text))
        match = re.search(r'(\d{6})', m.text or "")
        if match:
            print("🎉 FOUND 6-DIGIT CODE:", match.group(1))
            break
            
    await client.disconnect()

asyncio.run(test_get_code())
