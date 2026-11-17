# -*- coding: utf-8 -*-
"""
ON-DEMAND CLUSTER ORDER WORKER
Alohida virtual kompyuterda bitta buyurtmani to'liq bajarib, 
mijozga tayyor Excelni topshirib o'zini o'zi o'chiruvchi dastur.
"""

import os
import sys
import time
import json
import argparse
import requests
import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

def send_telegram_msg(bot_token, chat_id, text):
    if not bot_token or not chat_id:
        return
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        requests.post(url, json={
            "chat_id": int(chat_id),
            "text": text,
            "parse_mode": "HTML"
        }, timeout=10)
    except Exception as e:
        print(f"[TG NOTIFY ERROR] {e}")

def send_telegram_doc(bot_token, chat_id, file_path, caption="", custom_filename=None):
    if not bot_token or not chat_id or not os.path.exists(file_path):
        return
    try:
        doc_name = custom_filename or os.path.basename(file_path)
        url = f"https://api.telegram.org/bot{bot_token}/sendDocument"
        with open(file_path, "rb") as f:
            requests.post(url, data={
                "chat_id": int(chat_id),
                "caption": caption,
                "parse_mode": "HTML"
            }, files={"document": (doc_name, f)}, timeout=120)
    except Exception as e:
        print(f"[TG DOC ERROR] {e}")

def main():
    parser = argparse.ArgumentParser(description="Run single order in isolated cloud worker")
    parser.add_argument("--order-id", required=True, help="Order identifier")
    parser.add_argument("--chat-id", required=True, type=int, help="Telegram user chat ID")
    parser.add_argument("--user-name", default="Mijoz", help="Client name")
    parser.add_argument("--service-mode", default="full_cert", choices=["full_cert", "login_only"], help="Service mode")
    parser.add_argument("--session-name", default="", help="Dedicated Telegram session")
    parser.add_argument("--excel-file", required=True, help="Path or filename of the Excel order")

    args = parser.parse_args()

    bot_token = os.environ.get("BOT_TOKEN", "")
    admin_id = os.environ.get("ADMIN_ID", "")
    if admin_id and admin_id.isdigit():
        admin_id = int(admin_id)

    order_id = args.order_id
    chat_id = args.chat_id
    user_name = args.user_name
    service_mode = args.service_mode
    session_name = args.session_name
    excel_file = args.excel_file

    print("============================================================")
    print(f"🚀 ON-DEMAND VIRTUAL WORKER ISHGA TUSHDI!")
    print(f"🆔 Buyurtma ID: {order_id}")
    print(f"👤 Mijoz: {user_name} (Chat ID: {chat_id})")
    print(f"🌟 Xizmat: {service_mode}")
    print(f"📱 Biriktirilgan Sessiya: {session_name}")
    print(f"📁 Excel fayl: {excel_file}")
    print("============================================================")

    # 1. Excel faylni topish
    excel_path = Path(excel_file)
    if not excel_path.is_absolute():
        if (BASE_DIR / "orders" / excel_file).exists():
            excel_path = BASE_DIR / "orders" / excel_file
        elif (BASE_DIR / excel_file).exists():
            excel_path = BASE_DIR / excel_file
        elif os.path.exists(f"core_temp/orders/{excel_file}"):
            excel_path = Path(f"core_temp/orders/{excel_file}")

    if not excel_path.exists():
        err_msg = f"❌ Buyurtma fayli topilmadi: {excel_file}"
        print(err_msg)
        send_telegram_msg(bot_token, chat_id, err_msg)
        sys.exit(1)

    # 2. Sessiyani biriktirish
    if session_name:
        try:
            import session_pool
            state = session_pool.load_state()
            state["active_session"] = session_name
            state["needs_contact_rotation"] = False
            session_pool.save_state(state)
            print(f"[WORKER] Sessiya biriktirildi: {session_name}")
        except Exception as e_s:
            print(f"[WORKER SESSION ERROR] {e_s}")

    srv_title = "To'liq Sertifikat olish" if service_mode == "full_cert" else "Faqat Login-parol olish"
    start_msg = (
        f"⚡ <b>Buyurtmangiz bo'yicha maxsus Virtual Kompyuter ish boshladi!</b>\n\n"
        f"📁 Fayl: <b>{os.path.basename(str(excel_path))}</b>\n"
        f"🌟 Xizmat turi: <b>{srv_title}</b>\n"
        f"📱 Biriktirilgan Sessiya: <code>{session_name}</code>\n"
        f"🚀 Quvvat: <b>15 ta parallel oqim</b>\n\n"
        f"<i>(Jarayon real vaqtda yangilanadi va yakunlangach tayyor fayl shu yerga yuboriladi)</i>"
    )
    send_telegram_msg(bot_token, chat_id, start_msg)

    # 3. Dvigatelni ishga tushirish
    import process_5million_excel

    def tg_callback(msg):
        print(f"[WORKER LOG] {msg}", flush=True)
        # Faqat muhim xabarlarni telegramga yuborish
        m_str = str(msg).strip()
        if any(k in m_str for k in ["✅", "⚠️", "📩", "Token olindi", "Buyurtma qabul"]):
            send_telegram_msg(bot_token, chat_id, m_str)

    start_ts = time.time()
    try:
        res = process_5million_excel.process_excel_order(
            str(excel_path),
            update_callback=tg_callback,
            service_mode=service_mode
        )
        if len(res) == 3:
            success_cnt, total_cnt, dur_sec = res
        else:
            success_cnt, total_cnt = res
            dur_sec = time.time() - start_ts
    except Exception as e_exec:
        print(f"[WORKER EXECUTION ERROR] {e_exec}")
        send_telegram_msg(bot_token, chat_id, f"❌ Buyurtmani bajarishda xatolik yuz berdi: {e_exec}")
        sys.exit(1)

    dur_min = int(dur_sec // 60)
    dur_rem = int(dur_sec % 60)
    dur_text = f"{dur_min} daqiqa {dur_rem} soniya" if dur_min > 0 else f"{dur_rem} soniya"

    # 4. Tayyor Excelni mijozga yuborish
    finish_caption = (
        f"🎉 <b>BUYURTMA MUVAFFAQIYATLI YAKUNLANDI!</b>\n\n"
        f"📁 Fayl: <b>{os.path.basename(str(excel_path))}</b>\n"
        f"👥 Natija: <b>{success_cnt} / {total_cnt} ta o'quvchi</b>\n"
        f"⏱ Sarflangan vaqt: <b>{dur_text}</b>\n"
        f"🌟 Xizmat: <b>{srv_title}</b>\n\n"
        f"✅ Barcha o'quvchilar rasmiy havolalari bilan Excel faylga muhrlandi!"
    )
    send_telegram_doc(bot_token, chat_id, str(excel_path), caption=finish_caption)

    # 5. Adminga hisobot
    if admin_id and admin_id != chat_id:
        admin_report = (
            f"✅ <b>ON-DEMAND WORKER YAKUNLANDI:</b>\n"
            f"👤 Mijoz: <b>{user_name}</b> (ID: <code>{chat_id}</code>)\n"
            f"📁 Fayl: <code>{os.path.basename(str(excel_path))}</code>\n"
            f"👥 Natija: <b>{success_cnt}/{total_cnt} ta</b> | Vaqt: {dur_text}\n"
            f"📱 Sessiya: <code>{session_name}</code>\n"
            f"ℹ️ Virtual Kompyuter o'z vazifasini tugatib o'chmoqda."
        )
        send_telegram_msg(bot_token, admin_id, admin_report)

    # 6. Markaziy bazani sinxronlash
    try:
        process_5million_excel.sync_db_to_cloud()
        print("[WORKER] Baza studio-core ga muvaffaqiyatli saqlandi!")
    except Exception as e_sync:
        print(f"[WORKER SYNC ERROR] {e_sync}")

    print("============================================================")
    print(f"🎉 WORKER VAZIFASI 100% BITDI. VIRTUAL KOMPYUTER O'CHMOQDA...")
    print("============================================================")

if __name__ == "__main__":
    main()
