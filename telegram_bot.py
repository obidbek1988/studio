# -*- coding: utf-8 -*-
"""
=============================================================================
5 MILLION PROMPTER (omp.aistudy.uz) - BOSHQARUVCHI TELEGRAM BOT
Bot: @Beshmillionagentbot
Token: 9215921692:AAFscb1vWXl9LMe-IHLo7VZrkLeKL1xJkhQ
=============================================================================
"""

import os
import io
import re
import sys
import time
import json
import queue
import socket
import datetime
import threading
import traceback
import subprocess
import requests
from collections import deque
from pathlib import Path
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

# UTF-8 chiqish
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Global jurnallash (Console jonli log uchun)
LOG_BUFFER = deque(maxlen=60)

class LogInterceptor:
    def __init__(self, original_stream):
        self.original_stream = original_stream

    def write(self, s):
        try:
            self.original_stream.write(s)
            self.original_stream.flush()
        except Exception:
            pass
        if s and s.strip():
            now_str = datetime.datetime.now().strftime("%H:%M:%S")
            for line in s.splitlines():
                cl = line.strip()
                if cl:
                    LOG_BUFFER.append(f"[{now_str}] {cl}")

    def flush(self):
        try:
            self.original_stream.flush()
        except Exception:
            pass

sys.stdout = LogInterceptor(sys.stdout)
sys.stderr = LogInterceptor(sys.stderr)

# Asosiy yo'llar
BASE_DIR = Path(__file__).resolve().parent
CONFIG_FILE = BASE_DIR / "bot_config.json"
USERS_DB_FILE = BASE_DIR / "bot_users_db.json"
ORDERS_DIR = BASE_DIR / "orders"
TEMPLATES_DIR = BASE_DIR / "templates"
AI_INBOX_FILE = BASE_DIR / "ai_feedback_inbox.json"
STUDENTS_DB_FILE = BASE_DIR / "students_db.json"
PAUSE_FILE = BASE_DIR / "bot_pause_state.txt"

os.makedirs(ORDERS_DIR, exist_ok=True)
os.makedirs(TEMPLATES_DIR, exist_ok=True)

# Standart konfiguratsiya
DEFAULT_CONFIG = {
    "bot_token": "9215921692:AAFscb1vWXl9LMe-IHLo7VZrkLeKL1xJkhQ",
    "admin_id": 6580113791,
    "admin_username": "@OBIDBEK1988",
    "admin_tg_url": "https://t.me/OBIDBEK1988",
    "card_info": "5614 6812 1100 2260 (QOBILOV OBIDJON)",
    "anydesk_id": "1873514815",
    "anydesk_pwd": "UzbekCoders2026!",
    "cert_price": 3500
}

def load_config():
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                for k, v in DEFAULT_CONFIG.items():
                    if k not in cfg:
                        cfg[k] = v
                return cfg
        except Exception as e:
            print(f"[CONFIG ERROR] {e}")
    save_config(DEFAULT_CONFIG)
    return DEFAULT_CONFIG.copy()

def save_config(cfg):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[SAVE CONFIG ERROR] {e}")

def load_users_db():
    if USERS_DB_FILE.exists():
        try:
            with open(USERS_DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"users": {}, "orders": [], "kassa": {"total_revenue": 0, "total_certs": 0}}

def save_users_db(db):
    try:
        with open(USERS_DB_FILE, "w", encoding="utf-8") as f:
            json.dump(db, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[SAVE USERS DB ERROR] {e}")

def create_excel_template(file_path):
    """5 Million Prompter rasmiy Excel shablonini generatsiya qilish"""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "5 Million O'quvchilar"

    headers = [
        "T/r",
        "F.I.SH (Familiya Ism Sharif)",
        "Tug'ilgan sana (kun.oy.yil)",
        "Metrika seriyasi",
        "Metrika raqami",
        "Sinf",
        "Sertifikat havolasi",
        "Login (Email)",
        "Parol"
    ]

    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    center_align = Alignment(horizontal="center", vertical="center")
    border_thin = Border(
        left=Side(style='thin', color='D9D9D9'),
        right=Side(style='thin', color='D9D9D9'),
        top=Side(style='thin', color='D9D9D9'),
        bottom=Side(style='thin', color='D9D9D9')
    )

    ws.append(headers)
    for col_num in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=col_num)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_align

    # Namuna qatorlari
    samples = [
        [1, "ALIYEV VALI G'ANIYEVICH", "15.04.2012", "I-FR", "1234567", "5-A", "", "", ""],
        [2, "KARIMOVA MALIKA AZIZ QIZI", "20.09.2013", "II-FR", "7654321", "6-B", "", "", ""],
        [3, "TOSHPULATOV BEHZOD OTABEK O'G'LI", "05.11.2011", "I-TN", "9876543", "7-V", "", "", ""]
    ]

    for row_data in samples:
        ws.append(row_data)

    for row in ws.iter_rows(min_row=2, max_row=4, min_col=1, max_col=len(headers)):
        for cell in row:
            cell.border = border_thin
            if cell.column in [1, 3, 4, 5, 6]:
                cell.alignment = center_align

    # Ustun kengliklari
    col_widths = {1: 8, 2: 36, 3: 20, 4: 18, 5: 18, 6: 12, 7: 35, 8: 30, 9: 18}
    for col_idx, width in col_widths.items():
        ws.column_dimensions[openpyxl.utils.get_column_letter(col_idx)].width = width

    wb.save(file_path)
    return file_path


# Global holat
admin_input_state = {}
order_progress_state = {
    "current_order": None,
    "total": 0,
    "done": 0,
    "success": 0,
    "failed": 0,
    "status": "Bo'sh (Kutilmoqda)",
    "current_student": ""
}


class TelegramBotServer:
    def __init__(self):
        self.config = load_config()
        self.token = self.config.get("bot_token")
        self.admin_id = self.config.get("admin_id")
        self.base_url = f"https://api.telegram.org/bot{self.token}"
        self.offset = 0
        self.is_running = True
        self.is_paused = PAUSE_FILE.exists()
        self.session = requests.Session()

        # Shablonni tayyorlab qo'yish
        self.template_path = BASE_DIR / "shablon_5million.xlsx"
        if not self.template_path.exists():
            create_excel_template(str(self.template_path))

    # =========================================================================
    # TELEGRAM API ASOSIY METODLARI
    # =========================================================================
    def api_call(self, method, data=None, files=None, timeout=30):
        url = f"{self.base_url}/{method}"
        try:
            if files:
                r = self.session.post(url, data=data, files=files, timeout=timeout)
            else:
                r = self.session.post(url, json=data, timeout=timeout)
            return r.json()
        except Exception as e:
            print(f"[API CALL ERROR {method}] {e}")
            return {"ok": False, "error": str(e)}

    def send_message(self, chat_id, text, reply_markup=None, parse_mode="HTML"):
        data = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": True
        }
        if reply_markup:
            data["reply_markup"] = reply_markup
        return self.api_call("sendMessage", data)

    def send_document(self, chat_id, file_path, caption="", reply_markup=None):
        if not os.path.exists(file_path):
            return self.send_message(chat_id, f"❌ Fayl topilmadi: {file_path}")
        with open(file_path, "rb") as f:
            data = {"chat_id": chat_id, "caption": caption, "parse_mode": "HTML"}
            if reply_markup:
                data["reply_markup"] = json.dumps(reply_markup)
            return self.api_call("sendDocument", data=data, files={"document": f}, timeout=120)

    def send_photo(self, chat_id, photo_bytes, caption="", reply_markup=None):
        data = {"chat_id": chat_id, "caption": caption, "parse_mode": "HTML"}
        if reply_markup:
            data["reply_markup"] = json.dumps(reply_markup)
        return self.api_call("sendPhoto", data=data, files={"photo": ("screenshot.png", photo_bytes, "image/png")})

    def edit_message(self, chat_id, message_id, text, reply_markup=None, parse_mode="HTML"):
        data = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": True
        }
        if reply_markup:
            data["reply_markup"] = reply_markup
        return self.api_call("editMessageText", data)

    def answer_callback_query(self, callback_query_id, text=None, show_alert=False):
        data = {"callback_query_id": callback_query_id}
        if text:
            data["text"] = text
            data["show_alert"] = show_alert
        return self.api_call("answerCallbackQuery", data)

    def download_file(self, file_id, dest_path):
        res = self.api_call("getFile", {"file_id": file_id})
        if res.get("ok"):
            file_path = res["result"]["file_path"]
            download_url = f"https://api.telegram.org/file/bot{self.token}/{file_path}"
            r = self.session.get(download_url, timeout=60)
            if r.status_code == 200:
                with open(dest_path, "wb") as f:
                    f.write(r.content)
                return dest_path
        return None

    # =========================================================================
    # KLAVIATURALAR (ADMIN & FOYDALANUVCHI)
    # =========================================================================
    def get_reply_keyboard(self, chat_id: int):
        if self.admin_id and chat_id == self.admin_id:
            return {
                "keyboard": [
                    [{"text": "🎓 5 Million Prompter (Besh Million)"}],
                    [{"text": "⏸ To'xtatish (Pauza)"}, {"text": "▶️ Qolgan joyidan davom ettirish"}],
                    [{"text": "🤖 Robot Agentlar Dashboard"}, {"text": "🌐 Web Any (Brauzerda)"}],
                    [{"text": "🧹 Keshni tozalash (Yangi buyurtma)"}, {"text": "🖥 Klaster (Kompyuterlar holati)"}],
                    [{"text": "⚡ Ishlarni bo'lish (Klasterga)"}, {"text": "📊 Tahlil va Jarayon"}],
                    [{"text": "⚡ Jonli Log (Console)"}, {"text": "📥 Tayyor Sertifikatlar (Excel)"}],
                    [{"text": "💰 Foyda va Kassa"}, {"text": "📸 Kompyuterdan Skrinshot"}],
                    [{"text": "🖥 AnyDesk Jonli Ulanish"}, {"text": "📄 Bo'sh Shablon (.xlsx)"}],
                    [{"text": "🛠 AI Dasturchiga yozish (Skrinshot / Taklif)"}],
                ],
                "resize_keyboard": True,
                "is_persistent": False,
            }
        return {
            "keyboard": [
                [{"text": "🎓 5 Million Prompter"}],
                [{"text": "📥 Excel Shablon olish"}, {"text": "📸 To'lov chekini yuborish"}],
                [{"text": "💰 Narxlar va 50% Avans"}, {"text": "👨‍💼 Admin bilan aloqa"}],
            ],
            "resize_keyboard": True,
            "is_persistent": False,
        }

    # =========================================================================
    # AMALLAR VA XIZMATLAR
    # =========================================================================
    def get_system_stats(self):
        stats = {
            "cpu": 0, "ram": 0, "ram_used": "0 GB", "ram_total": "0 GB",
            "disk": 0, "hostname": socket.gethostname(), "ip": "127.0.0.1"
        }
        try:
            import psutil
            stats["cpu"] = psutil.cpu_percent(interval=0.5)
            vm = psutil.virtual_memory()
            stats["ram"] = vm.percent
            stats["ram_used"] = f"{vm.used / (1024**3):.1f} GB"
            stats["ram_total"] = f"{vm.total / (1024**3):.1f} GB"
            du = psutil.disk_usage("D:\\") if os.path.exists("D:\\") else psutil.disk_usage("C:\\")
            stats["disk"] = du.percent
        except Exception:
            pass
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            stats["ip"] = s.getsockname()[0]
            s.close()
        except Exception:
            pass
        return stats

    def clean_cache(self):
        """Kesh va vaqtincha audio/video fayllarni tozalash"""
        cleared_count = 0
        cleared_size = 0
        dirs_to_clean = [
            BASE_DIR / "temp_audio",
            BASE_DIR / "video_frames",
            BASE_DIR / "__pycache__"
        ]
        for d in dirs_to_clean:
            if d.exists():
                for f in d.glob("*"):
                    try:
                        if f.is_file():
                            cleared_size += f.stat().st_size
                            f.unlink()
                            cleared_count += 1
                    except Exception:
                        pass

        # Ildiz papkadagi captcha va cert png fayllari
        for f in BASE_DIR.glob("captcha_*.mp3"):
            try:
                cleared_size += f.stat().st_size
                f.unlink()
                cleared_count += 1
            except Exception:
                pass

        for f in BASE_DIR.glob("cert_*.png"):
            try:
                cleared_size += f.stat().st_size
                f.unlink()
                cleared_count += 1
            except Exception:
                pass

        return cleared_count, cleared_size / (1024 * 1024)

    def capture_screenshot(self):
        """Kompyuter ekranidan skrinshot olish"""
        try:
            from PIL import ImageGrab
            img = ImageGrab.grab()
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            buf.seek(0)
            return buf.getvalue()
        except Exception as e:
            print(f"[SCREENSHOT ERROR] {e}")
            return None

    def get_anydesk_id(self):
        """AnyDesk ID ni kompyuterdan o'qish"""
        paths = [
            "C:/ProgramData/AnyDesk/system.conf",
            os.path.expanduser("~") + "/AppData/Roaming/AnyDesk/system.conf"
        ]
        for p in paths:
            if os.path.exists(p):
                try:
                    with open(p, "r", encoding="utf-8", errors="ignore") as f:
                        text = f.read()
                    m = re.search(r"ad\.anynet\.id=(\d+)", text)
                    if m:
                        return m.group(1)
                except Exception:
                    pass
        return self.config.get("anydesk_id", "1873514815")

    # =========================================================================
    # 5 MILLION PROMPTER DASTURINI ISHGA TUSHIRISH (PIPELINE)
    # =========================================================================
    def run_5million_pipeline(self, chat_id, user_name, local_file_path, orig_fname):
        """process_5million_excel.py orqali to'liq avtomatik sertifikat olish jarayoni"""
        global order_progress_state
        try:
            self.send_message(
                chat_id,
                f"🎓 <b>BESH MILLION PROMPTER (omp.aistudy.uz) BUYURTMASI QABUL QILINDI!</b>\n\n"
                f"📁 Fayl: <b>{orig_fname}</b>\n"
                f"🤖 Tizim: <b>Playwright + Whisper AI Captcha Solver</b>\n"
                f"⏳ O'quvchilar ro'yxati tekshirilmoqda va darslarni 100% yopish boshlandi...\n\n"
                f"<i>(Har bir o'quvchi natijasi shu yerda real vaqtda xabar qilinadi)</i>"
            )

            order_progress_state["current_order"] = orig_fname
            order_progress_state["status"] = "Jarayonda ⚙️"

            def telegram_progress_callback(msg_text):
                try:
                    if self.is_paused:
                        print("[PAUSED] Jarayon to'xtatilgan, kutilmoqda...")
                        while self.is_paused:
                            time.sleep(2)
                    self.send_message(chat_id, msg_text)
                    if "✅" in msg_text:
                        order_progress_state["success"] += 1
                        order_progress_state["done"] += 1
                    elif "⚠️" in msg_text or "❌" in msg_text:
                        order_progress_state["failed"] += 1
                        order_progress_state["done"] += 1
                except Exception as ex:
                    print(f"[5M TG UPDATE ERROR] {ex}")

            import process_5million_excel
            success_cnt, total_cnt = process_5million_excel.process_excel_order(
                local_file_path,
                update_callback=telegram_progress_callback
            )

            order_progress_state["status"] = "Yakunlandi ✅"
            order_progress_state["done"] = total_cnt
            order_progress_state["success"] = success_cnt

            # Kassaga va hisobotga yozish
            db = load_users_db()
            earned = success_cnt * self.config.get("cert_price", 3500)
            db["kassa"]["total_revenue"] += earned
            db["kassa"]["total_certs"] += success_cnt
            db["orders"].append({
                "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "file": orig_fname,
                "user": user_name,
                "chat_id": chat_id,
                "total": total_cnt,
                "success": success_cnt,
                "earned": earned
            })
            save_users_db(db)

            self.send_message(
                chat_id,
                f"🎉 <b>5 MILLION PROMPTER BUYURTMASI YAKUNLANDI!</b>\n\n"
                f"📊 <b>Natija:</b> {success_cnt} ta o'quvchiga sertifikat olindi (Jami: {total_cnt} ta)!\n"
                f"📥 To'ldirilgan va barcha sertifikat havolalari yozilgan Excel fayl quyida yuborilmoqda 👇"
            )

            self.send_document(
                chat_id,
                local_file_path,
                caption=f"✅ 5 Million Prompter Tayyor Sertifikatlar ({success_cnt}/{total_cnt} ta)"
            )
        except Exception as e:
            print(f"[5MILLION ENGINE ERROR] {e}")
            traceback.print_exc()
            order_progress_state["status"] = f"Xatolik: {str(e)[:50]}"
            self.send_message(
                chat_id,
                f"❌ <b>5 Million Prompter jarayonida xatolik yuz berdi:</b>\n"
                f"<code>{str(e)[:300]}</code>"
            )

    # =========================================================================
    # BUYRUQLAR VA TUGMALARNI QAYTA ISHLASH (PROCESS UPDATE)
    # =========================================================================
    def process_update(self, upd):
        # 1. Callback Queries (Inline tugmalar)
        if "callback_query" in upd:
            cb = upd["callback_query"]
            cb_id = cb["id"]
            chat_id = cb["message"]["chat"]["id"]
            msg_id = cb["message"]["message_id"]
            data = cb.get("data", "")

            if data == "refresh_dash":
                self.answer_callback_query(cb_id, "Dashboard yangilandi! 🔄")
                self.send_dashboard_view(chat_id, edit_msg_id=msg_id)
                return

            if data == "refresh_screen":
                self.answer_callback_query(cb_id, "Yangi skrinshot olinmoqda... 📸")
                screen_bytes = self.capture_screenshot()
                if screen_bytes:
                    markup = {"inline_keyboard": [[{"text": "🔄 Yangilash", "callback_data": "refresh_screen"}]]}
                    self.send_photo(chat_id, screen_bytes, caption=f"📸 <b>Jonli Skrinshot:</b> {datetime.datetime.now().strftime('%H:%M:%S')}", reply_markup=markup)
                return

            if data == "refresh_logs":
                self.answer_callback_query(cb_id, "Loglar yangilandi! ⚡")
                self.send_live_console_log(chat_id, edit_msg_id=msg_id)
                return

            if data.startswith("approve_check_"):
                uid = int(data.split("_")[2])
                self.answer_callback_query(cb_id, "To'lov cheki tasdiqlandi! ✅", show_alert=True)
                self.send_message(uid, "✅ <b>To'lovingiz tasdiqlandi!</b>\nBuyurtmangiz navbatga qabul qilindi. Tez orada sertifikatlar tayyor bo'ladi!")
                self.edit_message(chat_id, msg_id, f"✅ <b>To'lov cheki TASDIQLANDI!</b> (Foydalanuvchi: <code>{uid}</code>)")
                return

            if data.startswith("reject_check_"):
                uid = int(data.split("_")[2])
                self.answer_callback_query(cb_id, "To'lov cheki rad etildi ❌", show_alert=True)
                self.send_message(uid, "❌ <b>To'lov chekingiz tasdiqlanmadi.</b>\nIltimos, aniq va to'g'ri to'lov chekini qayta yuboring yoki Admin bilan bog'laning.")
                self.edit_message(chat_id, msg_id, f"❌ <b>To'lov cheki RAD ETILDI!</b> (Foydalanuvchi: <code>{uid}</code>)")
                return

            if data.startswith("send_cert_file_"):
                fname = data.replace("send_cert_file_", "")
                fpath = ORDERS_DIR / fname
                if fpath.exists():
                    self.answer_callback_query(cb_id, "Fayl yuborilmoqda...")
                    self.send_document(chat_id, str(fpath), caption=f"📄 {fname}")
                else:
                    self.answer_callback_query(cb_id, "Fayl topilmadi!", show_alert=True)
                return

            self.answer_callback_query(cb_id)
            return

        # 2. Oddiy xabarlar (Message)
        if "message" not in upd:
            return

        msg = upd["message"]
        chat_id = msg["chat"]["id"]
        user_name = msg["from"].get("first_name", "Foydalanuvchi")
        text = (msg.get("text") or "").strip()

        # Admin ID sini avtomatik aniqlash (birinchi /start bosganda)
        if not self.admin_id:
            self.admin_id = chat_id
            self.config["admin_id"] = chat_id
            save_config(self.config)

        # Foydalanuvchini bazaga qo'shish
        db = load_users_db()
        str_cid = str(chat_id)
        if str_cid not in db["users"]:
            db["users"][str_cid] = {
                "name": user_name,
                "username": msg["from"].get("username", ""),
                "joined": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            save_users_db(db)

        # ---------------------------------------------------------------------
        # HUJJAT (EXCEL FAYL) KELGANDA
        # ---------------------------------------------------------------------
        if "document" in msg:
            doc = msg["document"]
            orig_fname = (doc.get("file_name") or "").strip()
            fname_lower = orig_fname.lower()

            if fname_lower.endswith(".xlsx"):
                clean_base = re.sub(r'[\\/*?:"<>|]', "", os.path.splitext(orig_fname)[0]).strip() or "Buyurtma"
                dest_file = ORDERS_DIR / f"order_{chat_id}_{int(time.time())}_{clean_base}.xlsx"
                self.send_message(chat_id, f"📥 <b>{orig_fname}</b> fayli yuklab olinmoqda...")
                saved_path = self.download_file(doc["file_id"], str(dest_file))

                if saved_path:
                    # Agar admin yuborgan bo'lsa yoki 5million rejimida bo'lsa
                    is_admin = (self.admin_id and chat_id == self.admin_id)
                    admin_input_state.pop(chat_id, None)

                    threading.Thread(
                        target=self.run_5million_pipeline,
                        args=(chat_id, user_name, saved_path, orig_fname),
                        daemon=True
                    ).start()
                else:
                    self.send_message(chat_id, "❌ Faylni yuklab olishda xatolik yuz berdi. Qayta urinib ko'ring.")
                return
            else:
                self.send_message(chat_id, "⚠️ Iltimos, faqat Excel (.xlsx) formatidagi fayl yuboring!")
                return

        # ---------------------------------------------------------------------
        # RASM (TO'LOV CHEKI YOKI SKRINSHOT) KELGANDA
        # ---------------------------------------------------------------------
        if "photo" in msg:
            photo = msg["photo"][-1]
            file_id = photo["file_id"]

            st = admin_input_state.get(chat_id, {})
            if st.get("action") == "ai_dev_note":
                admin_input_state.pop(chat_id, None)
                # AI Dasturchiga rasm va taklif saqlash
                dest = BASE_DIR / f"ai_feedback_{int(time.time())}.png"
                self.download_file(file_id, str(dest))
                self.save_ai_feedback(chat_id, user_name, msg.get("caption", "[Skrinshot yuborildi]"), str(dest))
                self.send_message(chat_id, "✅ <b>Taklifingiz va skrinshotingiz AI Dasturchiga yetkazildi!</b> Katta rahmat.")
                return

            # Oddiy foydalanuvchining to'lov cheki
            caption = (
                f"💳 <b>YANGI TO'LOV CHEKI QABUL QILINDI!</b>\n\n"
                f"👤 Foydalanuvchi: <b>{user_name}</b> (ID: <code>{chat_id}</code>)\n"
                f"🕒 Vaqt: <code>{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</code>\n\n"
                f"To'lovni tekshirib, quyidagi tugmalar orqali tasdiqlang 👇"
            )
            markup = {
                "inline_keyboard": [
                    [
                        {"text": "✅ Tasdiqlash", "callback_data": f"approve_check_{chat_id}"},
                        {"text": "❌ Rad etish", "callback_data": f"reject_check_{chat_id}"}
                    ]
                ]
            }

            # Adminga yuborish
            if self.admin_id:
                data = {"chat_id": self.admin_id, "photo": file_id, "caption": caption, "parse_mode": "HTML", "reply_markup": json.dumps(markup)}
                self.api_call("sendPhoto", data)

            self.send_message(
                chat_id,
                "✅ <b>To'lov chekingiz adminga tekshirish uchun yuborildi!</b>\n"
                "Tez orada chek tasdiqlanadi va buyurtmangiz ishga tushadi.",
                reply_markup=self.get_reply_keyboard(chat_id)
            )
            return

        # ---------------------------------------------------------------------
        # ADMIN INPUT HOLATI (AGAR MATN KELGAN BO'LSA)
        # ---------------------------------------------------------------------
        st = admin_input_state.get(chat_id)
        if st and st.get("action") == "ai_dev_note":
            admin_input_state.pop(chat_id, None)
            self.save_ai_feedback(chat_id, user_name, text, None)
            self.send_message(chat_id, "✅ <b>Taklif va xabaringiz AI Dasturchiga saqlandi!</b>")
            return

        # ---------------------------------------------------------------------
        # MATNLI BUYRUQLAR VA MENYU TUGMALARI
        # ---------------------------------------------------------------------
        if not text:
            return

        # 1. /START
        if text.startswith("/start"):
            admin_input_state.pop(chat_id, None)
            is_adm = (self.admin_id and chat_id == self.admin_id)
            welcome_text = (
                f"Assalomu alaykum, <b>{user_name}</b>! 👋\n\n"
                f"🎓 <b>5 MILLION PROMPTER (omp.aistudy.uz) AVTOMAT TIZIMIGA XUSH KELIBSIZ!</b>\n\n"
                f"🤖 Ushbu bot orqali o'quvchilaringizning 5 Million Prompter sertifikatlarini "
                f"to'liq avtomatik, 100% testlarni yechgan holda olishingiz mumkin.\n\n"
                f"💰 <b>Tariflar:</b>\n"
                f"• 1 – 25 ta o'quvchi: <b>4 000 so'm</b> dan\n"
                f"• 26 – 50 ta o'quvchi: <b>3 500 so'm</b> dan\n"
                f"• 51 – 100 ta o'quvchi: <b>3 000 so'm</b> dan\n"
                f"• 100 tadan ortiq: <b>Kelishilgan narxda</b>\n\n"
                f"📥 Buyurtma berish uchun pastdagi <b>«📥 Excel Shablon olish»</b> tugmasini bosib, "
                f"shablonni to'ldirib yuboring!"
            )
            if is_adm:
                welcome_text += "\n\n👑 <b>Siz TIZIM ADMINISTRATORISIZ!</b> Barcha boshqaruv tugmalari pastda faol."

            self.send_message(chat_id, welcome_text, reply_markup=self.get_reply_keyboard(chat_id))
            return

        # 2. 🎓 5 Million Prompter (Besh Million)
        if text in ("🎓 5 Million Prompter (Besh Million)", "🎓 5 Million Prompter", "/5million", "5million", "5mln"):
            admin_input_state[chat_id] = {"action": "5million_order"}
            msg = (
                "🎓 <b>5 MILLION PROMPTER (omp.aistudy.uz) BUYURTMA REJIMI:</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "📌 Ushbu loyiha mustaqil Playwright brauzer dvigateli va Whisper AI orqali "
                "audio kapchalarni 100% yechib, barcha modullarni avtomat yopadi.\n\n"
                "📤 <b>Tayyor Excel (.xlsx) faylingizni shu yerga yuboring!</b>\n\n"
                "<i>(Fayl yuborilishi bilan avtomatik navbatga qo'yilib, har bir o'quvchi bo'yicha jonli hisobot beriladi)</i>"
            )
            self.send_message(chat_id, msg, reply_markup=self.get_reply_keyboard(chat_id))
            return

        # 3. ⏸ To'xtatish (Pauza)
        if text in ("⏸ To'xtatish (Pauza)", "⏸ To'xtatish", "/pause", "/stop"):
            self.is_paused = True
            try:
                with open(PAUSE_FILE, "w", encoding="utf-8") as f:
                    f.write("paused")
            except Exception:
                pass
            self.send_message(
                chat_id,
                "⏸ <b>Jarayonlar vaqtincha to'xtatildi (Pauza rejimida).</b>\n\n"
                "Hozirgi bajarilayotgan o'quvchi yakunlangach yangisi kutiladi.\n"
                "Davom ettirish uchun <b>▶️ Qolgan joyidan davom ettirish</b> tugmasini bosing.",
                reply_markup=self.get_reply_keyboard(chat_id)
            )
            return

        # 4. ▶️ Qolgan joyidan davom ettirish
        if text in ("▶️ Qolgan joyidan davom ettirish", "▶️ Davom ettirish", "/resume"):
            self.is_paused = False
            if PAUSE_FILE.exists():
                try:
                    PAUSE_FILE.unlink()
                except Exception:
                    pass
            self.send_message(
                chat_id,
                "▶️ <b>Jarayonlar muvaffaqiyatli davom ettirilmoqda!</b>\nNavbatdagi o'quvchilar avtomatik ishlanadi.",
                reply_markup=self.get_reply_keyboard(chat_id)
            )
            return

        # 5. 🤖 Robot Agentlar Dashboard
        if text in ("🤖 Robot Agentlar Dashboard", "🤖 Dashboard", "/dashboard", "/robots"):
            self.send_dashboard_view(chat_id)
            return

        # 6. 🌐 Web Any (Brauzerda)
        if text in ("🌐 Web Any (Brauzerda)", "🌐 Web Any", "/webany"):
            stats = self.get_system_stats()
            msg = (
                "🌐 <b>WEB ANY & BRAUZER MASOFAVIY MONITORINGI:</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🖥 Kompyuter: <b>{stats['hostname']}</b>\n"
                f"🌐 Mahalliy IP: <code>{stats['ip']}</code>\n"
                f"🔗 Veb interfeys: <code>http://{stats['ip']}:8766/</code>\n"
                f"⚡ Platforma: <b>omp.aistudy.uz</b>\n"
                f"🤖 Brauzer: <b>Chromium E2E (Playwright Headless)</b>\n"
                f"📌 Holat: <b>Faol va xizmatga tayyor</b>"
            )
            self.send_message(chat_id, msg, reply_markup=self.get_reply_keyboard(chat_id))
            return

        # 7. 🧹 Keshni tozalash (Yangi buyurtma)
        if text in ("🧹 Keshni tozalash (Yangi buyurtma)", "🧹 Keshni tozalash", "/clear", "/kesh"):
            cnt, mb = self.clean_cache()
            self.send_message(
                chat_id,
                f"🧹 <b>KESH VA VAQTINCHALIK FAYLLAR TOZALANDI!</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🗑 Tozalangan fayllar: <b>{cnt} ta</b>\n"
                f"💾 Bo'shatilgan joy: <b>{mb:.2f} MB</b>\n"
                f"✨ Tizim yangi buyurtmalarga 100% toza holatda tayyor!",
                reply_markup=self.get_reply_keyboard(chat_id)
            )
            return

        # 8. 🖥 Klaster (Kompyuterlar holati)
        if text in ("🖥 Klaster (Kompyuterlar holati)", "🖥 Klaster", "/klaster", "/cluster"):
            stats = self.get_system_stats()
            msg = (
                "🖥 <b>KLASTER VA KOMPYUTERLAR HOLATI:</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                f"👑 <b>Master Kompyuter (Asosiy):</b>\n"
                f"  • Host: <code>{stats['hostname']}</code>\n"
                f"  • IP: <code>{stats['ip']}</code>\n"
                f"  • CPU: <b>{stats['cpu']}%</b> | RAM: <b>{stats['ram']}% ({stats['ram_used']} / {stats['ram_total']})</b>\n"
                f"  • Holat: 🟢 <b>Online (Faol)</b>\n\n"
                f"⚡ <b>AI Solver:</b> OpenAI Whisper Tiny (Lokal)\n"
                f"⚙️ <b>Playwright:</b> Headless Chromium Workers\n"
                f"📊 <b>Barcha agentlar aloqada!</b>"
            )
            self.send_message(chat_id, msg, reply_markup=self.get_reply_keyboard(chat_id))
            return

        # 9. ⚡ Ishlarni bo'lish (Klasterga)
        if text in ("⚡ Ishlarni bo'lish (Klasterga)", "⚡ Ishlarni bo'lish", "/bolish"):
            msg = (
                "⚡ <b>ISHLARNI BO'LISH (KLASTERGA) REJIMI:</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "Ushbu rejim 100+ o'quvchidan iborat katta Excel jadvallarini avtomatik ravishda "
                "25 talik yoki 50 talik kichik qismlarga bo'lib, klasterdagi bir nechta parallel oqimlarga taqsimlaydi.\n\n"
                "📂 <i>Katta hajmdagi Excel faylingizni yuboring, tizim uni avtomatik taqsimlaydi.</i>"
            )
            self.send_message(chat_id, msg, reply_markup=self.get_reply_keyboard(chat_id))
            return

        # 10. 📊 Tahlil va Jarayon
        if text in ("📊 Tahlil va Jarayon", "/tahlil", "/jarayon", "/stat"):
            order_name = order_progress_state["current_order"] or "Yo'q"
            total = order_progress_state["total"]
            done = order_progress_state["done"]
            succ = order_progress_state["success"]
            fail = order_progress_state["failed"]
            pct = int((done / total * 100)) if total > 0 else (100 if succ > 0 else 0)

            # Progress bar
            filled = int(pct / 10)
            bar = "█" * filled + "░" * (10 - filled)

            msg = (
                "📊 <b>BUYURTMA TAHLILI VA JONLI JARAYON:</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                f"📁 Hozirgi fayl: <b>{order_name}</b>\n"
                f"📌 Holat: <b>{order_progress_state['status']}</b>\n"
                f"📈 Jarayon: <code>[{bar}] {pct}%</code>\n\n"
                f"👥 Jami o'quvchilar: <b>{total} ta</b>\n"
                f"✅ Sertifikat olinganlar: <b>{succ} ta</b>\n"
                f"⚠️ Olinmagan/Qayta urinish: <b>{fail} ta</b>\n"
                f"⏳ Qolgan: <b>{max(0, total - done)} ta</b>"
            )
            self.send_message(chat_id, msg, reply_markup=self.get_reply_keyboard(chat_id))
            return

        # 11. ⚡ Jonli Log (Console)
        if text in ("⚡ Jonli Log (Console)", "/log", "/console"):
            self.send_live_console_log(chat_id)
            return

        # 12. 📥 Tayyor Sertifikatlar (Excel)
        if text in ("📥 Tayyor Sertifikatlar (Excel)", "/sertifikatlar"):
            self.send_completed_excel_menu(chat_id)
            return

        # 13. 💰 Foyda va Kassa
        if text in ("💰 Foyda va Kassa", "/foyda", "/kassa"):
            db = load_users_db()
            kassa = db.get("kassa", {"total_revenue": 0, "total_certs": 0})
            orders_cnt = len(db.get("orders", []))
            total_rev = kassa.get("total_revenue", 0)
            total_cert = kassa.get("total_certs", 0)

            msg = (
                "💰 <b>KASSA VA FOYDA HISOBOTI:</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🎓 Jami chiqarilgan sertifikatlar: <b>{total_cert} ta</b>\n"
                f"📦 Yakunlangan buyurtmalar: <b>{orders_cnt} ta</b>\n"
                f"💵 O'rtacha tarif: <b>{self.config.get('cert_price', 3500):,} so'm</b>\n"
                f"💎 <b>Jami tushum (Kassa):</b> <b>{total_rev:,} so'm</b>\n\n"
                f"🏦 <b>To'lov kartasi:</b> <code>{self.config.get('card_info')}</code>"
            )
            self.send_message(chat_id, msg, reply_markup=self.get_reply_keyboard(chat_id))
            return

        # 14. 📸 Kompyuterdan Skrinshot
        if text in ("📸 Kompyuterdan Skrinshot", "/screen", "/skrin"):
            self.send_message(chat_id, "📸 Skrinshot olinmoqda...")
            screen_bytes = self.capture_screenshot()
            if screen_bytes:
                markup = {"inline_keyboard": [[{"text": "🔄 Yangilash", "callback_data": "refresh_screen"}]]}
                self.send_photo(
                    chat_id,
                    screen_bytes,
                    caption=f"📸 <b>Kompyuter ekrani</b>\nVaqt: <code>{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</code>",
                    reply_markup=markup
                )
            else:
                self.send_message(chat_id, "❌ Skrinshot olishning imkoni bo'lmadi.")
            return

        # 15. 🖥 AnyDesk Jonli Ulanish
        if text in ("🖥 AnyDesk Jonli Ulanish", "/anydesk", "/any"):
            aid = self.get_anydesk_id()
            pwd = self.config.get("anydesk_pwd", "UzbekCoders2026!")
            msg = (
                "🖥 <b>ANYDESK JONLI MASOFAVIY ULANISH:</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🆔 <b>AnyDesk ID:</b> <code>{aid}</code>\n"
                f"🔑 <b>Parol:</b> <code>{pwd}</code>\n\n"
                f"⚡ <i>Ulanish uchun AnyDesk dasturiga yuqoridagi ID raqamni kiriting.</i>"
            )
            self.send_message(chat_id, msg, reply_markup=self.get_reply_keyboard(chat_id))
            return

        # 16. 📄 Bo'sh Shablon (.xlsx) va 📥 Excel Shablon olish
        if text in ("📄 Bo'sh Shablon (.xlsx)", "📥 Excel Shablon olish", "/shablon", "/excel"):
            if not self.template_path.exists():
                create_excel_template(str(self.template_path))
            self.send_document(
                chat_id,
                str(self.template_path),
                caption="📄 <b>5 Million Prompter (omp.aistudy.uz) Rasmiy Excel Shablon</b>\n\n"
                        "Ushbu faylga o'quvchilaringiz ma'lumotlarini kiritib, botga qayta yuboring."
            )
            return

        # 17. 🛠 AI Dasturchiga yozish (Skrinshot / Taklif)
        if text in ("🛠 AI Dasturchiga yozish (Skrinshot / Taklif)", "/ai", "/dev"):
            admin_input_state[chat_id] = {"action": "ai_dev_note"}
            msg = (
                "🛠 <b>AI DASTURCHIGA YOZISH (TAKLIF / SKRINSHOT):</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "✍️ Tizimga qanday yangi funksiya, o'zgartirish yoki taklifingiz bo'lsa, "
                "shu yerga matn shaklida yozing yoki skrinshot yuboring.\n\n"
                "<i>Xabaringiz to'g'ridan-to'g'ri AI Dasturchi jurnali va inboxiga saqlanadi.</i>"
            )
            self.send_message(chat_id, msg, reply_markup=self.get_reply_keyboard(chat_id))
            return

        # 18. 📸 To'lov chekini yuborish
        if text == "📸 To'lov chekini yuborish":
            card = self.config.get("card_info")
            msg = (
                "📸 <b>TO'LOV CHEKINI YUBORISH:</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🏦 <b>Karta:</b> <code>{card}</code>\n\n"
                "👇 To'lovni amalga oshirgach, chekning skrinshotini (rasmini) shu yerga chatga yuboring!\n"
                "<i>Chek adminga tasdiqlash uchun boradi va tasdiqlangach sertifikatlar chiqariladi.</i>"
            )
            self.send_message(chat_id, msg, reply_markup=self.get_reply_keyboard(chat_id))
            return

        # 19. 💰 Narxlar va 50% Avans
        if text in ("💰 Narxlar va 50% Avans", "/narxlar"):
            card = self.config.get("card_info")
            msg = (
                "💰 <b>TARIFLAR VA 50% AVANS TIZIMI:</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "• 1 – 25 ta o'quvchi: <b>4 000 so'm</b> dan\n"
                "• 26 – 50 ta o'quvchi: <b>3 500 so'm</b> dan\n"
                "• 51 – 100 ta o'quvchi: <b>3 000 so'm</b> dan\n"
                "• 100 tadan ortiq: <b>Kelishilgan arzon narxda</b>\n\n"
                "🌗 <b>50% Avans Imkoniyati:</b>\n"
                "Buyurtma berayotganda summaning <b>50% qismini</b> avans sifatida to'lab ishni boshlashingiz mumkin. "
                "Qolgan 50% qismini barcha sertifikatlar tayyor bo'lgach to'laysiz!\n\n"
                f"🏦 <b>Karta:</b> <code>{card}</code>\n\n"
                "🔄 <b>100% Kafolat:</b> Tizim o'quvchilarni to'liq sertifikat bilan ta'minlaydi!"
            )
            self.send_message(chat_id, msg, reply_markup=self.get_reply_keyboard(chat_id))
            return

        # 20. 👨‍💼 Admin bilan aloqa
        if text in ("👨‍💼 Admin bilan aloqa", "/admin"):
            admin_u = self.config.get("admin_username", "@OBIDBEK1988")
            admin_url = self.config.get("admin_tg_url", "https://t.me/OBIDBEK1988")
            markup = {"inline_keyboard": [[{"text": f"👨‍💼 Adminga yozish ({admin_u})", "url": admin_url}]]}
            self.send_message(
                chat_id,
                f"👨‍💼 <b>ADMIN BILAN BOG'LANISH:</b>\n\nSavol, taklif va katta buyurtmalar uchun: {admin_u}",
                reply_markup=markup
            )
            return

        # Standart javob
        self.send_message(
            chat_id,
            f"Tushunarsiz buyruq: <i>{text}</i>\nIltimos, pastdagi menyu tugmalaridan foydalaning 👇",
            reply_markup=self.get_reply_keyboard(chat_id)
        )

    # =========================================================================
    # YORDAMCHI MENYULAR
    # =========================================================================
    def send_dashboard_view(self, chat_id, edit_msg_id=None):
        stats = self.get_system_stats()
        db = load_users_db()
        users_cnt = len(db.get("users", {}))
        certs_cnt = db.get("kassa", {}).get("total_certs", 0)

        pause_status = "HA ⏸" if self.is_paused else "YO'Q ▶️"
        txt = (
            "🤖 <b>ROBOT AGENTLAR DASHBOARD (omp.aistudy.uz):</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🖥 Server: <b>{stats['hostname']}</b>\n"
            f"⚡ CPU Yuklama: <b>{stats['cpu']}%</b>\n"
            f"🧠 Tezkor Xotira (RAM): <b>{stats['ram']}% ({stats['ram_used']} / {stats['ram_total']})</b>\n"
            f"💾 Qattiq disk: <b>{stats['disk']}% band</b>\n\n"
            f"👥 Bot foydalanuvchilari: <b>{users_cnt} nafar</b>\n"
            f"🎓 Jami sertifikatlar: <b>{certs_cnt} ta</b>\n"
            f"⏸ Pauza holati: <b>{pause_status}</b>\n"
            f"🕒 Tizim vaqti: <code>{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</code>"
        )
        markup = {"inline_keyboard": [[{"text": "🔄 Yangilash", "callback_data": "refresh_dash"}]]}
        if edit_msg_id:
            self.edit_message(chat_id, edit_msg_id, txt, reply_markup=markup)
        else:
            self.send_message(chat_id, txt, reply_markup=markup)

    def send_live_console_log(self, chat_id, edit_msg_id=None):
        logs = list(LOG_BUFFER)[-25:]
        log_text = "\n".join(logs) if logs else "Hozircha hech qanday log yozuvi yo'q."
        if len(log_text) > 3500:
            log_text = log_text[-3500:]

        msg = (
            "⚡ <b>JONLI LOG (CONSOLE):</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<pre>{log_text}</pre>"
        )
        markup = {"inline_keyboard": [[{"text": "🔄 Loglarni yangilash", "callback_data": "refresh_logs"}]]}
        if edit_msg_id:
            self.edit_message(chat_id, edit_msg_id, msg, reply_markup=markup)
        else:
            self.send_message(chat_id, msg, reply_markup=markup)

    def send_completed_excel_menu(self, chat_id):
        files = list(ORDERS_DIR.glob("*.xlsx"))
        if not files:
            self.send_message(chat_id, "ℹ️ Hozircha tayyorlangan Excel fayllar mavjud emas.")
            return

        files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        recent_files = files[:6]

        buttons = []
        for f in recent_files:
            dt = datetime.datetime.fromtimestamp(f.stat().st_mtime).strftime("%d.%m %H:%M")
            buttons.append([{"text": f"📥 {f.name[:30]} ({dt})", "callback_data": f"send_cert_file_{f.name}"}])

        markup = {"inline_keyboard": buttons}
        self.send_message(
            chat_id,
            "📥 <b>TAYYOR SERTIFIKATLAR (SO'NGGI BUYURTMALAR):</b>\n"
            "Yuklab olmoqchi bo'lgan Excel faylingizni tanlang 👇",
            reply_markup=markup
        )

    def save_ai_feedback(self, chat_id, user_name, note, photo_path):
        feedbacks = []
        if AI_INBOX_FILE.exists():
            try:
                with open(AI_INBOX_FILE, "r", encoding="utf-8") as f:
                    feedbacks = json.load(f)
            except Exception:
                pass
        feedbacks.append({
            "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "chat_id": chat_id,
            "user": user_name,
            "note": note,
            "photo": photo_path
        })
        try:
            with open(AI_INBOX_FILE, "w", encoding="utf-8") as f:
                json.dump(feedbacks, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    # =========================================================================
    # ASOSIY POLLING SIKLI VA BULUT TAYMERI (24/7 CLOUD SELF-RELOAD)
    # =========================================================================
    def start_polling(self):
        print(f"============================================================")
        print(f"5 MILLION PROMPTER TELEGRAM BOT ISHGA TUSHDI! (@Beshmillionagentbot)")
        print(f"Admin ID: {self.admin_id} | Kompyuter: {socket.gethostname()}")
        print(f"============================================================")

        cloud_start_time = time.time()
        cloud_max_sec = 4.5 * 3600  # 4.5 soat
        is_cloud = os.environ.get("CLOUD_MODE") == "1" or os.environ.get("GITHUB_ACTIONS") == "true"

        while self.is_running:
            # Bulut taymerini tekshirish (o'chishdan 30 daqiqa oldin xavfsiz push va qayta yoqish)
            if is_cloud and (time.time() - cloud_start_time >= cloud_max_sec):
                print("[CLOUD DRAIN] 4.5 soat to'ldi. Yangi buyurtma qabul qilinmaydi!")
                self.send_message(self.admin_id, "⏳ <b>Bulutli bot: 4.5 soat ishladi.</b> Ma'lumotlar saqlanmoqda va yangi zanjirli oqim ishga tushirilmoqda...")
                
                # Faqat yangi ish bo'lsa push qilish
                try:
                    status = subprocess.check_output(["git", "status", "--porcelain"], text=True).strip()
                    if status:
                        print("[CLOUD PUSH] O'zgarishlar mavjud, saqlanmoqda...")
                        subprocess.run(["git", "config", "user.name", "obidbek1988"], check=True)
                        subprocess.run(["git", "config", "user.email", "obidbek1988@gmail.com"], check=True)
                        subprocess.run(["git", "add", "students_db.json", "orders/"], check=True)
                        subprocess.run(["git", "commit", "-m", "Auto-save: Cloud completed certificates"], check=True)
                        subprocess.run(["git", "push", "origin", "main"], check=True)
                        print("[CLOUD PUSH] Muvaffaqiyatli PUSH qilindi!")
                    else:
                        print("[CLOUD PUSH] Yangi ish bo'lmadi, push qilinmadi.")
                except Exception as ep:
                    print(f"[CLOUD PUSH ERROR] {ep}")

                # Keyingi yangi bulutli runni ishga tushirish (Auto-restart)
                try:
                    gh_tok = os.environ.get("GH_TOKEN", "")
                    if gh_tok:
                        requests.post(
                            "https://api.github.com/repos/obidbek1988/5millionbot/actions/workflows/cloud_bot.yml/dispatches",
                            headers={"Authorization": f"token {gh_tok}", "Accept": "application/vnd.github+json"},
                            json={"ref": "main"},
                            timeout=15
                        )
                        print("[CLOUD RESTART] Keyingi 5 soatlik bulutli ishchi ishga tushirildi!")
                except Exception as er:
                    print(f"[CLOUD RESTART ERROR] {er}")

                break

            try:
                url = f"{self.base_url}/getUpdates?offset={self.offset}&timeout=25"
                resp = self.session.get(url, timeout=30)
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("ok"):
                        for upd in data.get("result", []):
                            self.offset = upd["update_id"] + 1
                            try:
                                self.process_update(upd)
                            except Exception as eu:
                                print(f"[PROCESS UPDATE ERROR] {eu}")
                                traceback.print_exc()
                elif resp.status_code == 409:
                    print("[CONFLICT] Boshqa bot sessiyasi bor, 5 soniya kutilmoqda...")
                    time.sleep(5)
                else:
                    time.sleep(2)
            except requests.exceptions.RequestException as re_err:
                time.sleep(3)
            except Exception as e:
                print(f"[POLLING ERROR] {e}")
                time.sleep(3)


if __name__ == "__main__":
    bot = TelegramBotServer()
    bot.start_polling()
