import sys
import asyncio
import re
from telethon import TelegramClient

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

API_ID = 2040
API_HASH = "b18441a1ff607e10a989891a5462e627"
SESSION_PATH = "5millionsertifikat/tg_session"
BOT_USERNAME = "aistudy_uz_bot"

async def get_verification_code():
    print(f"🤖 @{BOT_USERNAME} botidan tasdiqlash kodi olinmoqda...", flush=True)
    client = TelegramClient(SESSION_PATH, API_ID, API_HASH)
    await client.connect()
    
    if not await client.is_user_authorized():
        print("❌ Telegram sessiyasi faol emas!")
        await client.disconnect()
        return None
        
    # Botga /start yuboramiz yoki mavjud tugmani qidiramiz
    bot = await client.get_entity(BOT_USERNAME)
    
    # Oxirgi xabarni tekshiramiz
    messages = await client.get_messages(bot, limit=5)
    
    # "Tasdiqlash kodini olish" tugmasini bosamiz
    clicked = False
    for msg in messages:
        if msg.buttons:
            for row in msg.buttons:
                for btn in row:
                    if "Tasdiqlash kodini olish" in btn.text or "kodini olish" in btn.text:
                        print(f"🔘 '{btn.text}' tugmasi bosilmoqda...", flush=True)
                        await btn.click()
                        clicked = True
                        break
                if clicked:
                    break
        if clicked:
            break
            
    if not clicked:
        # Tugma topilmasa /start yozamiz
        print("💬 Botga /start yuborilmoqda...", flush=True)
        await client.send_message(bot, "/start")
        await asyncio.sleep(2)
        # Qaytgan xabardagi tugmani bosamiz
        new_msgs = await client.get_messages(bot, limit=2)
        for msg in new_msgs:
            if msg.buttons:
                for row in msg.buttons:
                    for btn in row:
                        if "Tasdiqlash kodini olish" in btn.text or "kodini olish" in btn.text:
                            print(f"🔘 '{btn.text}' tugmasi bosildi!", flush=True)
                            await btn.click()
                            clicked = True
                            break
                    if clicked:
                        break
            if clicked:
                break
                
    # 2-3 soniya javob xabarini kutamiz
    print("⏳ Bot javobi kutilmoqda...", flush=True)
    code = None
    for _ in range(10):
        await asyncio.sleep(1)
        latest_msgs = await client.get_messages(bot, limit=3)
        for msg in latest_msgs:
            # "Sizning tasdiqlash kodingiz 👉 587269"
            match = re.search(r'(\d{6})', msg.text or "")
            if match and ("tasdiqlash" in msg.text.lower() or "kod" in msg.text.lower()):
                code = match.group(1)
                print(f"🎯 6 XONALI TASDIQLASH KODI TOPILDI: [{code}]", flush=True)
                break
        if code:
            break
            
    await client.disconnect()
    return code

if __name__ == "__main__":
    c = asyncio.run(get_verification_code())
    print("Yakuniy kod:", c)
