import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import asyncio
from telethon import TelegramClient

API_ID = 2040
API_HASH = "b18441a1ff607e10a989891a5462e627"
SESSION_PATH = "5millionsertifikat/tg_session"

async def share_contact():
    client = TelegramClient(SESSION_PATH, API_ID, API_HASH)
    await client.connect()
    bot = await client.get_entity('aistudy_uz_bot')
    
    msgs = await client.get_messages(bot, limit=3)
    for m in msgs:
        if m.buttons:
            for row in m.buttons:
                for b in row:
                    if "Kontaktni yuborish" in b.text:
                        print("Clicking 'Kontaktni yuborish' with share_phone=True...")
                        await b.click(share_phone=True)
                        print("Contact shared successfully!")
                        break
                        
    await asyncio.sleep(3)
    latest = await client.get_messages(bot, limit=3)
    for m in latest:
        print("Reply:", repr(m.text))
        if m.buttons:
            print("Buttons now:", [[b.text for b in row] for row in m.buttons])
            
    await client.disconnect()

asyncio.run(share_contact())
