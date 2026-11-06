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

# Standart konfiguratsiya (GitHub Secrets orqali xavfsiz yuklanadi)
DEFAULT_CONFIG = {
    "bot_token": os.environ.get("BOT_TOKEN", ""),
    "admin_id": int(os.environ.get("ADMIN_ID", 6580113791)),
    "admin_username": "@OBIDBEK1988",
    "admin_tg_url": "https://t.me/OBIDBEK1988",
    "card_info": os.environ.get("CARD_INFO", "5614 6812 1100 2260 (QOBILOV OBIDJON)"),
    "anydesk_id": "1873514815",
    "anydesk_pwd": "UzbekCoders2026!",
    "cert_price": 4000,
    "server_mode": "public"
}

# Navbat va buyurtmalar xotirasi
pending_orders = {}  # { chat_id: { 'path': ..., 'orig_fname': ..., 'student_cnt': ..., 'total_price': ..., 'user_name': ... } }
order_queue = []     # [ { 'chat_id': ..., 'user_name': ..., 'path': ..., 'orig_fname': ..., 'student_cnt': ..., 'total_price': ... } ]
is_queue_worker_running = False
queue_lock = threading.Lock()
current_active_order = None

def load_config():
    cfg = DEFAULT_CONFIG.copy()
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                for k, v in loaded.items():
                    if v:
                        cfg[k] = v
        except Exception as e:
            print(f"[CONFIG ERROR] {e}")

    # Environment variables (GitHub Secrets) doimo ustuvor
    if os.environ.get("BOT_TOKEN"):
        cfg["bot_token"] = os.environ.get("BOT_TOKEN")
    if os.environ.get("ADMIN_ID"):
        try:
            cfg["admin_id"] = int(os.environ.get("ADMIN_ID"))
        except Exception:
            pass
    if os.environ.get("CARD_INFO"):
        cfg["card_info"] = os.environ.get("CARD_INFO")
    return cfg

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
            s_mode = self.config.get("server_mode", "admin_only")
            s_btn = "🔒 Server: Faqat Admin" if s_mode == "admin_only" else "🔓 Server: Barchaga Ochiq"
            return {
                "keyboard": [
                    [{"text": s_btn}, {"text": "📸 Kompyuterdan Skrinshot"}],
                    [{"text": "⏸ To'xtatish (Pauza)"}, {"text": "▶️ Qolgan joyidan davom ettirish"}],
                    [{"text": "🤖 Robot Agentlar Dashboard"}, {"text": "🌐 Web Any (Brauzerda)"}],
                    [{"text": "🧹 Keshni tozalash (Yangi buyurtma)"}, {"text": "🖥 Klaster (Kompyuterlar holati)"}],
                    [{"text": "⚡ Ishlarni bo'lish (Klasterga)"}, {"text": "📊 Tahlil va Jarayon"}],
                    [{"text": "⚡ Jonli Log (Console)"}, {"text": "📥 Tayyor Sertifikatlar (Excel)"}],
                    [{"text": "💰 Foyda va Kassa"}, {"text": "📄 Bo'sh Shablon (.xlsx)"}],
                    [{"text": "🖥 AnyDesk Jonli Ulanish"}, {"text": "🛠 AI Dasturchiga yozish (Skrinshot / Taklif)"}],
                ],
                "resize_keyboard": True,
                "is_persistent": False,
            }
        return {
            "keyboard": [
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

            import importlib
            import process_5million_excel
            importlib.reload(process_5million_excel)
            excel_start_ts = time.time()
            res = process_5million_excel.process_excel_order(
                local_file_path,
                update_callback=telegram_progress_callback
            )
            if len(res) == 3:
                success_cnt, total_cnt, duration_sec = res
            else:
                success_cnt, total_cnt = res
                duration_sec = time.time() - excel_start_ts

            def fmt_dur(sec):
                sec = int(round(sec))
                if sec < 60:
                    return f"{sec} soniya"
                mins = sec // 60
                r = sec % 60
                return f"{mins} daqiqa" if r == 0 else f"{mins} daqiqa {r} soniya"

            dur_str = fmt_dur(duration_sec)
            avg_str = fmt_dur(duration_sec / max(1, success_cnt)) if success_cnt > 0 else "0 soniya"

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
                "earned": earned,
                "duration": dur_str
            })
            save_users_db(db)

            self.send_message(
                chat_id,
                f"🎉 <b>5 MILLION PROMPTER BUYURTMASI YAKUNLANDI!</b>\n\n"
                f"📁 <b>Fayl:</b> {orig_fname}\n"
                f"📊 <b>Natija:</b> {success_cnt} ta o'quvchiga sertifikat olindi (Jami: {total_cnt} ta)!\n"
                f"⏱ <b>Umumiy sarflangan vaqt:</b> {dur_str}\n"
                f"⚡ <b>1 ta sertifikatga o'rtacha:</b> {avg_str}\n\n"
                f"📥 To'ldirilgan va barcha sertifikat havolalari yozilgan Excel fayl quyida yuborilmoqda 👇"
            )

            self.send_document(
                chat_id,
                local_file_path,
                caption=f"✅ 5 Million Prompter Tayyor Sertifikatlar ({success_cnt}/{total_cnt} ta) | Vaqt: {dur_str}"
            )

            # Agar bu mijoz bo'lsa va admin boshqa odam bo'lsa, adminga ham yakunlangani haqida xabar berish
            if self.admin_id and chat_id != self.admin_id:
                try:
                    self.send_message(
                        self.admin_id,
                        f"🎉 <b>Mijoz buyurtmasi yakunlandi:</b>\n"
                        f"👤 <b>{user_name}</b> (ID: <code>{chat_id}</code>)\n"
                        f"📁 Fayl: <code>{orig_fname}</code>\n"
                        f"📊 Natija: <b>{success_cnt}/{total_cnt} ta</b> sertifikat olindi!\n"
                        f"⏱ Vaqt: <b>{dur_str}</b>"
                    )
                except Exception:
                    pass

        except Exception as e:
            print(f"[5MILLION ENGINE ERROR] {e}")
            traceback.print_exc()
            order_progress_state["status"] = f"Xatolik: {str(e)[:50]}"
            self.send_message(
                chat_id,
                f"❌ <b>5 Million Prompter jarayonida xatolik yuz berdi:</b>\n"
                f"<code>{str(e)[:300]}</code>"
            )

    def start_queue_worker(self):
        """Umumiy navbat ishchisi (Navbatdagi buyurtmalarni ketma-ket bittalab bajaruvchi konveyer)"""
        global is_queue_worker_running, current_active_order
        with queue_lock:
            if is_queue_worker_running:
                return
            is_queue_worker_running = True

        def worker_loop():
            global is_queue_worker_running, current_active_order
            print("[QUEUE WORKER] Navbat ishchisi faollashdi.")
            while True:
                next_order = None
                with queue_lock:
                    if order_queue:
                        next_order = order_queue.pop(0)
                        current_active_order = next_order
                    else:
                        is_queue_worker_running = False
                        current_active_order = None
                        break

                if next_order:
                    try:
                        print(f"[QUEUE EXECUTE] Buyurtma boshlanmoqda: {next_order['orig_fname']} (Chat: {next_order['chat_id']})")
                        self.run_5million_pipeline(
                            next_order['chat_id'],
                            next_order['user_name'],
                            next_order['path'],
                            next_order['orig_fname']
                        )
                    except Exception as we:
                        print(f"[QUEUE WORKER ERROR] {we}")
                    finally:
                        current_active_order = None

            print("[QUEUE WORKER] Navbatdagi barcha buyurtmalar tugadi. Ishchi kutish rejimida.")

        threading.Thread(target=worker_loop, daemon=True).start()

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

            if data.startswith("approve_order_"):
                uid = int(data.split("_")[2])
                po = pending_orders.pop(uid, None)
                if not po:
                    self.answer_callback_query(cb_id, "Buyurtma topilmadi yoki allaqachon navbatga qo'yilgan!", show_alert=True)
                    return

                with queue_lock:
                    order_queue.append(po)
                    pos = len(order_queue)
                    ahead_students = sum(item.get('student_cnt', 0) for item in order_queue[:-1])
                    if current_active_order:
                        ahead_students += current_active_order.get('student_cnt', 0)
                    ahead_minutes = max(1, ahead_students * 1)

                self.answer_callback_query(cb_id, f"Buyurtma #{pos}-o'rinda navbatga qo'yildi! ✅", show_alert=True)
                self.edit_message(chat_id, msg_id, f"✅ <b>Buyurtma TASDIQLANDI va Navbatga qo'yildi!</b>\n👤 Mijoz: <code>{uid}</code>\n📋 Navbat raqami: <b>#{pos}</b> ({ahead_students} ta bola oldinda)")

                if pos == 1 and not current_active_order:
                    queue_msg = (
                        f"✅ <b>To'lovingiz muvaffaqiyatli tasdiqlandi!</b>\n\n"
                        f"🚀 <b>Buyurtmangiz bo'yicha ish boshlandi!</b>\n"
                        f"📁 Fayl: <b>{po['orig_fname']}</b> ({po['student_cnt']} ta o'quvchi)\n\n"
                        f"<i>(Har bir o'quvchining sertifikati tayyor bo'lishi bilan shu yerga jonli hisobot keladi)</i>"
                    )
                else:
                    queue_msg = (
                        f"✅ <b>To'lovingiz muvaffaqiyatli tasdiqlandi!</b>\n\n"
                        f"📋 <b>Siz navbatda #{pos}-o'rindasiz.</b>\n"
                        f"👥 Oldingizda: <b>{ahead_students} ta o'quvchi</b> (hozir bajarilmoqda)\n"
                        f"⏱ <b>Taxminiy navbat kelish vaqti:</b> ~<b>{ahead_minutes} daqiqa</b>\n\n"
                        f"🚀 <i>Navbatingiz kelishi bilanoq sertifikatlar chiqarish avtomatik boshlanadi!</i>"
                    )
                self.send_message(uid, queue_msg)
                self.start_queue_worker()
                return

            if data.startswith("reject_order_"):
                uid = int(data.split("_")[2])
                pending_orders.pop(uid, None)
                self.answer_callback_query(cb_id, "Buyurtma rad etildi ❌", show_alert=True)
                self.send_message(uid, "❌ <b>Buyurtmangiz yoki to'lov chekingiz tasdiqlanmadi.</b>\nIltimos, to'g'ri to'lov chekini qayta yuboring yoki Admin bilan bog'laning.")
                self.edit_message(chat_id, msg_id, f"❌ <b>Buyurtma RAD ETILDI!</b> (Mijoz: <code>{uid}</code>)")
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
            print(f"\n[HUJJAT KELDI] Yangi Excel fayl: '{orig_fname}' (Chat: {chat_id})")

            if fname_lower.endswith(".xlsx"):
                is_admin = (self.admin_id and chat_id == self.admin_id)
                server_mode = self.config.get("server_mode", "admin_only")

                # Agar server band bo'lsa va admindan boshqa odam Excel tashlasa
                if not is_admin and server_mode == "admin_only":
                    admin_user = self.config.get("admin_username", "@OBIDBEK1988")
                    admin_url = self.config.get("admin_tg_url", "https://t.me/OBIDBEK1988")
                    contact_markup = {
                        "inline_keyboard": [
                            [{"text": f"👨‍💼 Adminga yozish ({admin_user})", "url": admin_url}]
                        ]
                    }
                    self.send_message(
                        chat_id,
                        f"🚫 <b>SERVER HOZIRCHA BAND!</b>\n\n"
                        f"Hurmatli <b>{user_name}</b>, hozirda server navbat bilan band.\n"
                        f"Excel buyurtmalar hozirda faqat <b>Administrator</b> orqali qabul qilinmoqda.\n\n"
                        f"Buyurtmangizni tezkor navbatga qo'yish uchun Adminga murojaat qiling:\n"
                        f"👉 <b>Admin:</b> {admin_user}\n"
                        f"🔗 <b>Bog'lanish:</b> {admin_url}",
                        reply_markup=contact_markup
                    )
                    try:
                        self.send_message(
                            self.admin_id,
                            f"🔔 <b>Mijoz Excel yubordi (Server Band holatida):</b>\n"
                            f"👤 <b>{user_name}</b> (ID: <code>{chat_id}</code>)\n"
                            f"📁 Fayl: <code>{orig_fname}</code>\n"
                            f"ℹ️ Server 'Faqat Admin' rejimida bo'lgani sababli fayl olinmadi va Sizga yo'naltirildi."
                        )
                    except Exception:
                        pass
                    return

                # Har qanday pauzani avtomatik yechish
                self.is_paused = False
                if PAUSE_FILE.exists():
                    try:
                        PAUSE_FILE.unlink()
                    except Exception:
                        pass

                clean_base = re.sub(r'[\\/*?:"<>|]', "", os.path.splitext(orig_fname)[0]).strip() or "Buyurtma"
                dest_file = ORDERS_DIR / f"order_{chat_id}_{int(time.time())}_{clean_base}.xlsx"
                print(f"[YUKLANMOQDA] Telegramdan yuklab olinmoqda: {orig_fname}...")
                self.send_message(chat_id, f"📥 <b>{orig_fname}</b> fayli yuklab olinmoqda...")
                saved_path = self.download_file(doc["file_id"], str(dest_file))

                if saved_path:
                    print(f"[YUKLANDI] Fayl saqlandi: {saved_path}")
                    is_admin = (self.admin_id and chat_id == self.admin_id)
                    admin_input_state.pop(chat_id, None)

                    # 40 ta o'quvchi cheklovi tekshiruvi
                    student_cnt = 1
                    try:
                        import openpyxl
                        wb_chk = openpyxl.load_workbook(saved_path, read_only=True)
                        ws_chk = wb_chk.active
                        row_cnt = 0
                        for row in ws_chk.iter_rows(values_only=True):
                            if row and any(row):
                                row_cnt += 1
                        student_cnt = max(1, row_cnt - 1)
                        wb_chk.close()
                        if student_cnt > 40 and not is_admin:
                            self.send_message(
                                chat_id,
                                f"⚠️ <b>Buyurtma hajmi oshib ketdi!</b>\n\n"
                                f"Hozirda 1 ta buyurtma uchun maksimal <b>40 ta o'quvchi</b> qabul qilinadi.\n"
                                f"Siz yuborgan faylda: <b>{student_cnt} ta o'quvchi</b> mavjud.\n\n"
                                f"Iltimos, faylingizni 40 tadan qilib bo'lib yuboring!",
                                reply_markup=self.get_reply_keyboard(chat_id)
                            )
                            return
                    except Exception as ec:
                        print(f"[STUDENT COUNT CHECK ERROR] {ec}")

                    # 1. AGAR ADMIN YUBORGAN BO'LSA: Darhol navbatga qo'yilib ish boshlanadi!
                    if is_admin:
                        self.send_message(chat_id, f"👑 <b>Administrator buyurtmasi qabul qilindi!</b> ({student_cnt} ta o'quvchi). Navbatga qo'yildi va ishga tushmoqda...")
                        with queue_lock:
                            order_queue.append({
                                'chat_id': chat_id,
                                'user_name': user_name,
                                'path': saved_path,
                                'orig_fname': orig_fname,
                                'student_cnt': student_cnt,
                                'total_price': 0
                            })
                        self.start_queue_worker()
                        return

                    # 2. AGAR MIJOZ YUBORGAN BO'LSA: Hisob-kitob qilib, to'lov cheki so'raladi!
                    # Qat'iy tarif: 4 000 so'm (1 ta o'quvchi uchun)
                    price_per_cert = 4000
                    total_price = student_cnt * price_per_cert
                    advance_price = int(total_price * 0.5)

                    pending_orders[chat_id] = {
                        'chat_id': chat_id,
                        'user_name': user_name,
                        'path': saved_path,
                        'orig_fname': orig_fname,
                        'student_cnt': student_cnt,
                        'total_price': total_price,
                        'advance_price': advance_price
                    }

                    invoice_msg = (
                        f"📥 <b>Excel faylingiz muvaffaqiyatli qabul qilindi!</b>\n"
                        f"━━━━━━━━━━━━━━━━━━━━━━\n"
                        f"📁 Fayl: <b>{orig_fname}</b>\n"
                        f"👥 O'quvchilar soni: <b>{student_cnt} ta</b>\n"
                        f"💵 Tarif: <b>4 000 so'm</b> (1 ta sertifikat)\n"
                        f"💰 Jami to'lov summasi: <b>{total_price:,} so'm</b>\n"
                        f"⚡ <b>50% Boshlang'ich to'lov (Avans):</b> <b>{advance_price:,} so'm</b>\n"
                        f"━━━━━━━━━━━━━━━━━━━━━━\n"
                        f"💳 <b>To'lov uchun karta:</b>\n"
                        f"<code>5614 6812 1100 2260</code>\n"
                        f"👤 QOBILOV OBIDJON\n\n"
                        f"📸 <i>Iltimos, to'lovni amalga oshirgach, to'lov chekini (skrinshotini) shu yerga rasm sifatida yuboring!</i>\n"
                        f"Administrator to'lovni tasdiqlashi bilanoq buyurtmangiz navbatga qo'yiladi."
                    )
                    self.send_message(chat_id, invoice_msg, reply_markup=self.get_reply_keyboard(chat_id))

                    if self.admin_id:
                        try:
                            self.send_message(
                                self.admin_id,
                                f"📥 <b>YANGI EXCEL BUYURTMA KELDI (To'lov kutilmoqda):</b>\n"
                                f"👤 Mijoz: <b>{user_name}</b> (ID: <code>{chat_id}</code>)\n"
                                f"📁 Fayl: <code>{orig_fname}</code>\n"
                                f"👥 O'quvchilar: <b>{student_cnt} ta</b>\n"
                                f"💰 Kutilayotgan summa: <b>{total_price:,} so'm</b> (Avans: {advance_price:,} so'm)\n"
                                f"ℹ️ Mijozdan to'lov cheki kutilmoqda."
                            )
                        except Exception:
                            pass
                    return
                else:
                    print(f"[XATO] Faylni yuklab olib bo'lmadi!")
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
            po = pending_orders.get(chat_id)
            if po:
                caption = (
                    f"💳 <b>YANGI TO'LOV CHEKI VA BUYURTMA!</b>\n\n"
                    f"👤 Mijoz: <b>{user_name}</b> (ID: <code>{chat_id}</code>)\n"
                    f"📁 Fayl: <code>{po['orig_fname']}</code>\n"
                    f"👥 O'quvchilar: <b>{po['student_cnt']} ta</b>\n"
                    f"💰 Summa: <b>{po['total_price']:,} so'm</b> (Avans: {po['advance_price']:,} so'm)\n"
                    f"🕒 Vaqt: <code>{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</code>\n\n"
                    f"To'lovni tekshirib, quyidagi tugmalar orqali tasdiqlang 👇"
                )
                markup = {
                    "inline_keyboard": [
                        [
                            {"text": "✅ Tasdiqlash va Navbatga qo'yish", "callback_data": f"approve_order_{chat_id}"},
                            {"text": "❌ Rad etish", "callback_data": f"reject_order_{chat_id}"}
                        ]
                    ]
                }
            else:
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
                "Admin to'lovni tasdiqlashi bilanoq buyurtmangiz navbatga qo'yiladi va navbat raqamingiz xabar qilinadi.",
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
            greeting_name = f"👑OBIDBEK GARANT ADMIN👑ID:{chat_id}" if is_adm else f"<b>{user_name}</b>"
            server_mode = self.config.get("server_mode", "admin_only")
            admin_user = self.config.get("admin_username", "@OBIDBEK1988")
            admin_url = self.config.get("admin_tg_url", "https://t.me/OBIDBEK1988")

            if server_mode == "admin_only":
                server_status_banner = (
                    "🔴 <b>SERVER HOLATI: BAND (Faqat Administrator orqali)</b>\n"
                    "⚠️ <i>Hozirda server navbat bilan band. Buyurtma berish uchun Adminga murojaat qiling!</i>\n"
                    f"👉 <b>Admin:</b> {admin_user} ({admin_url})\n"
                    "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                )
            else:
                server_status_banner = (
                    "🟢 <b>SERVER HOLATI: OCHIQ</b>\n"
                    "📁 <i>Buyurtma berish uchun Excel (.xlsx) faylingizni botga yuborishingiz mumkin!</i>\n"
                    "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                )

            welcome_text = (
                f"Assalomu alaykum, {greeting_name}! 👋\n\n"
                f"{server_status_banner}"
                f"🎓 <b>5 MILLION PROMPTER (omp.aistudy.uz) AVTOMAT TIZIMI</b>\n\n"
                f"🤖 Ushbu bot orqali o'quvchilaringizning 5 Million Prompter sertifikatlarini "
                f"to'liq avtomatik, 100% testlarni yechgan holda olishingiz mumkin.\n\n"
                f"💰 <b>Tarif:</b> <b>4 000 so'm</b> (1 ta sertifikat uchun)\n"
                f"⚠️ <i>1 ta buyurtma uchun maksimal <b>40 ta o'quvchi</b> qabul qilinadi.</i>\n\n"
                f"👨‍💻 <b>Administrator:</b> {admin_user}"
            )
            if is_adm:
                welcome_text += f"\n\n👑 <b>Siz TIZIM ADMINISTRATORISIZ!</b> Hozir server holati: <b>{server_mode.upper()}</b>."

            banner_path = BASE_DIR / "bot_banner.jpg"
            if banner_path.exists():
                try:
                    with open(banner_path, "rb") as bf:
                        self.send_photo(chat_id, bf.read(), caption=welcome_text, reply_markup=self.get_reply_keyboard(chat_id))
                        return
                except Exception as eb:
                    print(f"[BANNER ERROR] {eb}")

            self.send_message(chat_id, welcome_text, reply_markup=self.get_reply_keyboard(chat_id))
            return

        # 1.5. 🔒/🔓 Server Holati (Faqat Admin boshqaradi)
        if text.startswith("🔒 Server: Faqat Admin") or text.startswith("🔓 Server: Barchaga Ochiq") or text in ("/server", "/servermode"):
            if not (self.admin_id and chat_id == self.admin_id):
                self.send_message(chat_id, "⚠️ Bu amal faqat Administrator uchun!")
                return

            cur_mode = self.config.get("server_mode", "admin_only")
            new_mode = "public" if cur_mode == "admin_only" else "admin_only"
            self.config["server_mode"] = new_mode
            save_config(self.config)

            if new_mode == "public":
                msg = (
                    "🔓 <b>SERVER BARCHA MIJOZLAR UCHUN OCHILDI!</b>\n\n"
                    "✅ Endi barcha foydalanuvchilar to'g'ridan-to'g'ri Excel (.xlsx) fayllarini botga yuborishlari mumkin.\n"
                    "Tizim barcha buyurtmalarni avtomatik navbatga qo'yadi."
                )
            else:
                msg = (
                    "🔒 <b>SERVER FAQAT ADMIN REJIMIGA O'TKAZILDI (BAND)!</b>\n\n"
                    "⛔️ Begona mijozlar Excel yuborishsa, ularga server bandligi va Adminga (@OBIDBEK1988) murojaat qilish xabari chiqadi.\n"
                    "👑 Siz (Admin) esa bemalol istalgan Excel faylni yuborib ishlatishingiz mumkin."
                )

            self.send_message(chat_id, msg, reply_markup=self.get_reply_keyboard(chat_id))
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
        if text in ("💰 Narxlar va 50% Avans", "/narxlar", "/tariflar", "💰 Tariflar", "Tariflar"):
            card = self.config.get("card_info")
            msg = (
                "💰 <b>RASMIY TARIF VA TO'LOV TIZIMI:</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "• 1 ta sertifikat narxi: <b>4 000 so'm</b> (Qat'iy narx)\n"
                "⚠️ <b>Cheklov:</b> 1 ta buyurtma uchun maksimal <b>40 ta o'quvchi</b> qabul qilinadi.\n\n"
                "🌗 <b>50% Avans Imkoniyati:</b>\n"
                "Buyurtma berayotganda summaning <b>50% qismini</b> avans sifatida to'lab ishni boshlashingiz mumkin. "
                "Qolgan 50% qismini barcha sertifikatlar tayyor bo'lgach to'laysiz!\n\n"
                f"🏦 <b>Karta:</b> <code>{card}</code>\n\n"
                "🔄 <b>100% Kafolat:</b> Tizim barcha o'quvchilarni to'liq sertifikat bilan ta'minlaydi!"
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

        import html
        safe_log = html.escape(log_text)

        msg = (
            "⚡ <b>JONLI LOG (CONSOLE):</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<pre>{safe_log}</pre>"
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
                
                # Faqat yangi ish bo'lsa PRIVATE studio-core repoga push qilish
                try:
                    if os.path.exists("core_temp"):
                        import shutil
                        shutil.copy("students_db.json", "core_temp/students_db.json")
                        status = subprocess.check_output(["git", "-C", "core_temp", "status", "--porcelain"], text=True).strip()
                        if status:
                            print("[CLOUD PUSH] Yangi sertifikatlar PRIVATE repoga saqlanmoqda...")
                            subprocess.run(["git", "-C", "core_temp", "config", "user.name", "obidbek1988"], check=True)
                            subprocess.run(["git", "-C", "core_temp", "config", "user.email", "obidbek1988@gmail.com"], check=True)
                            subprocess.run(["git", "-C", "core_temp", "add", "students_db.json"], check=True)
                            subprocess.run(["git", "-C", "core_temp", "commit", "-m", "Auto-save: Private database updated"], check=True)
                            subprocess.run(["git", "-C", "core_temp", "push", "origin", "main"], check=True)
                            print("[CLOUD PUSH] Muvaffaqiyatli PRIVATE repoga PUSH qilindi!")
                        else:
                            print("[CLOUD PUSH] Yangi ish bo'lmadi, push qilinmadi.")
                except Exception as ep:
                    print(f"[CLOUD PUSH ERROR] {ep}")

                # Keyingi yangi bulutli runni ishga tushirish (Auto-restart)
                try:
                    gh_tok = os.environ.get("GH_TOKEN", "")
                    if gh_tok:
                        requests.post(
                            "https://api.github.com/repos/obidbek1988/studio/actions/workflows/cloud_bot.yml/dispatches",
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
                                threading.Thread(target=self.process_update, args=(upd,), daemon=True).start()
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
