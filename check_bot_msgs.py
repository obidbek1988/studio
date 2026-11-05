import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import asyncio
from telethon import TelegramClient

async def check():
    client = TelegramClient('5millionsertifikat/tg_session', 2040, 'b18441a1ff607e10a989891a5462e627')
    await client.connect()
    bot = await client.get_entity('aistudy_uz_bot')
    msgs = await client.get_messages(bot, limit=5)
    for m in msgs:
        print('--- MSG ---')
        print('Text:', repr(m.text))
        if m.buttons:
            print('Buttons:', [[b.text for b in row] for row in m.buttons])
    await client.disconnect()

asyncio.run(check())
