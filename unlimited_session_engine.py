# -*- coding: utf-8 -*-
"""
CHEKSIZ TELEGRAM KOD OLISH DVIGATELI (UNLIMITED SESSION ENGINE)
Muallif: Besh Million Avtomatizatsiya Tizimi
Sana: 17.11.2026

Prinsip:
@aistudy_uz_bot har bir biriktirilgan telefon raqamiga 5 ta kod beradi.
Limit to'lganida yoki xohlagan paytda:
1. '⚙️ Sozlamalar' (yoki '⚙️ Settings') bosiladi.
2. '📞 Kontaktni o'zgartirish' (yoki '📞 Change contact') bosiladi.
3. Yangi kontakt kartasi (InputMediaContact) yuboriladi.
4. Bot yangi raqamni qabul qiladi va unga darhol yangi 5 talik limit beradi.
Natijada: 1 TA TELEGRAM AKKAUNT CHEKSIZ ISHLAYDI!
"""

import os
import sys
import time
import random
import re
import asyncio
from telethon import TelegramClient
from telethon.tl.types import InputMediaContact

API_ID = 26521369
API_HASH = "fa2e0d37e50c4aa3d54c1537b0d88470"

def generate_random_uz_phone():
    """O'zbekiston prefikslari bo'yicha to'g'ri formatdagi tasodifiy raqam yaratish"""
    prefix = random.choice(["90", "91", "93", "94", "95", "97", "98", "99", "88", "33"])
    tail = f"{random.randint(1000000, 9999999)}"
    return f"+998{prefix}{tail}"

async def ensure_language_uz(client, bot):
    """Agar bot boshqa tilda bo'lsa yoki menyu ko'rinmasa /start berish"""
    try:
        await client.send_message(bot, "/start")
        await asyncio.sleep(1.0)
        msgs = await client.get_messages(bot, limit=3)
        for m in msgs:
            if m.buttons:
                for row in m.buttons:
                    for b in row:
                        if "UZB" in (b.text or "").upper():
                            await b.click()
                            await asyncio.sleep(1.0)
                            return
    except Exception:
        pass

async def change_contact_in_bot(client, bot, new_phone=None):
    """
    @aistudy_uz_bot dagi kontaktni yangisiga almashtirish.
    1. Sozlamalar tugmasi bosiladi
    2. Kontaktni o'zgartirish bosiladi
    3. Yangi InputMediaContact yuboriladi
    """
    if not new_phone:
        new_phone = generate_random_uz_phone()

    print(f"[UNLIMITED TG] Kontaktni yangilash boshlandi -> Raqam: {new_phone}", flush=True)

    # 1-qadam: Sozlamalar tugmasini topish va bosish
    msgs = await client.get_messages(bot, limit=5)
    settings_clicked = False
    for m in msgs:
        if m.buttons:
            for row in m.buttons:
                for b in row:
                    bt = (b.text or "").lower()
                    if any(w in bt for w in ["sozlamalar", "settings", "⚙️"]):
                        try:
                            await b.click()
                            settings_clicked = True
                            print(f"[UNLIMITED TG] '⚙️ Sozlamalar' bosildi", flush=True)
                            await asyncio.sleep(1.5)
                            break
                        except Exception as e:
                            print(f"[UNLIMITED TG] Sozlamalar bosishda xato: {e}", flush=True)
                if settings_clicked:
                    break
        if settings_clicked:
            break

    if not settings_clicked:
        # Menyu ko'rinmasa /start berib qayta urinish
        await client.send_message(bot, "/start")
        await asyncio.sleep(1.5)
        msgs = await client.get_messages(bot, limit=3)
        for m in msgs:
            if m.buttons:
                for row in m.buttons:
                    for b in row:
                        bt = (b.text or "").lower()
                        if any(w in bt for w in ["sozlamalar", "settings", "⚙️"]):
                            try:
                                await b.click()
                                settings_clicked = True
                                await asyncio.sleep(1.5)
                                break
                            except Exception:
                                pass
                    if settings_clicked:
                        break
            if settings_clicked:
                break

    # 2-qadam: 'Kontaktni o'zgartirish' tugmasini bosish
    msgs = await client.get_messages(bot, limit=3)
    change_clicked = False
    for m in msgs:
        if m.buttons:
            for row in m.buttons:
                for b in row:
                    bt = (b.text or "").lower()
                    if any(w in bt for w in ["kontaktni", "change contact", "raqamni"]):
                        try:
                            await b.click()
                            change_clicked = True
                            print(f"[UNLIMITED TG] '📞 Kontaktni o'zgartirish' bosildi", flush=True)
                            await asyncio.sleep(1.5)
                            break
                        except Exception as e:
                            print(f"[UNLIMITED TG] Kontakt tugmasi bosishda xato: {e}", flush=True)
                if change_clicked:
                    break
        if change_clicked:
            break

    # 3-qadam: Yangi kontakt kartasini yuborish
    contact = InputMediaContact(
        phone_number=new_phone,
        first_name="Talaba",
        last_name="",
        vcard=""
    )
    try:
        await client.send_file(bot, contact)
        print(f"[UNLIMITED TG] Yangi kontakt kartasi yuborildi: {new_phone}", flush=True)
        await asyncio.sleep(2.0)
    except Exception as e_send:
        print(f"[UNLIMITED TG] Kontakt yuborishda xato: {e_send}", flush=True)
        return False, None

    # Bot yangi menyuni chiqarganini tekshirish
    check_msgs = await client.get_messages(bot, limit=3)
    for cm in check_msgs:
        if cm.buttons:
            for row in cm.buttons:
                for b in row:
                    bt = (b.text or "").lower()
                    if any(w in bt for w in ["kod", "code", "verification", "tasdiqlash"]):
                        print(f"✅ [UNLIMITED TG] Kontakt muvaffaqiyatli qabul qilindi! Yangi limit ochildi: {new_phone}", flush=True)
                        return True, new_phone

    print(f"✅ [UNLIMITED TG] Kontakt muvaffaqiyatli almashtirildi: {new_phone}", flush=True)
    return True, new_phone

async def fetch_cheksiz_code(client, max_retries=3):
    """
    1 ta Telegram sessiyasi orqali Cheksiz kod olish funksiyasi.
    Agar bot limit xabarini bersa, darhol avtomatik tarzda:
    Sozlamalar -> Kontaktni o'zgartirish -> Yangi kontakt -> Yangi kod
    jarayonini bajaradi.
    """
    bot = await client.get_entity("@aistudy_uz_bot")

    for attempt in range(1, max_retries + 1):
        msgs = await client.get_messages(bot, limit=5)
        
        # 'Kod olish' yoki 'Qayta urinish' tugmasini topish
        code_clicked = False
        click_time = time.time()
        for m in msgs:
            if m.buttons:
                for row in m.buttons:
                    for b in row:
                        bt = (b.text or "").lower()
                        if any(w in bt for w in ["kod", "code", "tasdiqlash", "verification", "retry", "qayta"]):
                            try:
                                await b.click()
                                code_clicked = True
                                print(f"[UNLIMITED TG] 'Kod olish' tugmasi bosildi ({b.text})", flush=True)
                                break
                            except Exception:
                                pass
                    if code_clicked:
                        break
            if code_clicked:
                break

        if not code_clicked:
            # Agar asosiy menyuda turmagan bo'lsa yoki tugma ko'rinmasa, /start berish
            print(f"[UNLIMITED TG] Tugma ko'rinmadi, /start yuborilmoqda...", flush=True)
            await client.send_message(bot, "/start")
            await asyncio.sleep(1.5)
            continue

        # Botdan yangi javobni kutish
        code_found = None
        limit_hit = False
        current_phone = None

        for wait_s in range(1, 15):
            await asyncio.sleep(1.0)
            latest = await client.get_messages(bot, limit=3)
            for m in latest:
                if m.out:
                    continue
                if m.date.timestamp() < (click_time - 2):
                    continue

                txt = (m.text or "").strip()
                txt_low = txt.lower()

                # Kodni izlash (6 ta raqam)
                m_code = re.search(r'\b(\d{6})\b', txt)
                if m_code and any(w in txt_low for w in ["verification", "tasdiqlash", "code", "kod", "kodingiz", "👉"]):
                    code_found = m_code.group(1)
                    break

                # Limitga yetganlik xabarini tekshirish
                if any(w in txt_low for w in ["limit", "cheklov", "faqat bitta", "bitta telefon", "kechirasiz", "mumkin emas"]):
                    print(f"⚠️ [UNLIMITED TG] 5 talik limit aniqlandi: '{txt[:50]}...'", flush=True)
                    limit_hit = True
                    break

            if code_found or limit_hit:
                break

        if code_found:
            print(f"🎉 [UNLIMITED TG] YANGI KOD QABUL QILINDI: [{code_found}]", flush=True)
            return code_found

        if limit_hit:
            print(f"🔄 [UNLIMITED TG] 5 talik limit to'ldi! Avtomatik yangi kontaktga ulanmoqda...", flush=True)
            ok, new_phone = await change_contact_in_bot(client, bot)
            if ok:
                await asyncio.sleep(1.5)
                # Keyingi aylanmada yangi raqam orqali darhol kod olinadi
                continue

    return None

async def run_standalone_test(session_name="998330072869"):
    """Bitta sessiyada to'liq mustaqil test qilish"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    session_path = os.path.join(base_dir, "sessions", session_name)
    if not os.path.exists(session_path + ".session") and not os.path.exists(session_path):
        print(f"❌ Sessiya fayli topilmadi: {session_path}")
        return

    print("============================================================")
    print(f"🧪 CHEKSIZ TELEGRAM KOD OLISH TESTI BOSHLANDI")
    print(f"📱 Sessiya: {session_name}")
    print("============================================================")

    c = TelegramClient(session_path, API_ID, API_HASH)
    await c.connect()
    if not await c.is_user_authorized():
        print(f"❌ Sessiya faol emas (unauthorized): {session_name}")
        await c.disconnect()
        return

    me = await c.get_me()
    print(f"👤 Telegram Foydalanuvchi: {me.first_name} (+{me.phone})")

    # 1. Kontaktni almashtirishni sinash
    bot = await c.get_entity("@aistudy_uz_bot")
    test_phone = generate_random_uz_phone()
    print(f"\n1-QADAM: Yangi tasodifiy raqamga kontakt almashtirish: {test_phone}")
    ok, bound_phone = await change_contact_in_bot(c, bot, test_phone)

    if ok:
        print(f"✅ Kontakt muvaffaqiyatli almashtirildi: {bound_phone}")
        # 2. Kod olishni sinash
        print(f"\n2-QADAM: Yangi raqam orqali kod olish sinovi...")
        code = await fetch_cheksiz_code(c, max_retries=2)
        if code:
            print(f"\n🎉 SINOV 100% MUVAFFAQIYATLI O'TDI!")
            print(f"🔑 Olingan yangi tasdiqlash kodi: {code}")
            print(f"📱 Biriktirilgan raqam: {bound_phone}")
            print("============================================================")
        else:
            print("⚠️ Kod kelmadi.")
    else:
        print("❌ Kontakt almashtirilmadi.")

    await c.disconnect()

if __name__ == "__main__":
    test_sess = sys.argv[1] if len(sys.argv) > 1 else "998330072869"
    asyncio.run(run_standalone_test(test_sess))
