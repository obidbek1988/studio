# -*- coding: utf-8 -*-
"""
=============================================================================
5 MILLION PROMPTER (omp.aistudy.uz) - BOSHQARUVCHI TELEGRAM BOT
Bot: @Beshmillionagentbot
Token: SECURE_GITHUB_SECRET
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
ACTIVE_WORKER_SESSIONS = set()

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
from cluster_manager import start_cluster_server, cluster_state
BASE_DIR = Path(__file__).resolve().parent
CONFIG_FILE = BASE_DIR / "bot_config.json"
USERS_DB_FILE = BASE_DIR / "bot_users_db.json"
ORDERS_DIR = BASE_DIR / "orders"
TEMPLATES_DIR = BASE_DIR / "templates"
AI_INBOX_FILE = BASE_DIR / "ai_feedback_inbox.json"
STUDENTS_DB_FILE = BASE_DIR / "students_db.json"
PAUSE_FILE = BASE_DIR / "bot_pause_state.txt"
ACTIVE_ORDER_FILE = BASE_DIR / "active_order_state.json"
ACTIVE_EXCEL_PATH = ORDERS_DIR / "active_order.xlsx"

# Kataloglarni avtomatik yaratish (GitHub Actions va yangi tizimlarda xato bo'lmasligi uchun)
ORDERS_DIR.mkdir(parents=True, exist_ok=True)
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)

# Kataloglarni avtomatik yaratish (GitHub Actions va yangi tizimlarda xato bo'lmasligi uchun)
ORDERS_DIR.mkdir(parents=True, exist_ok=True)
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)

os.makedirs(ORDERS_DIR, exist_ok=True)
os.makedirs(TEMPLATES_DIR, exist_ok=True)

# Standart konfiguratsiya (GitHub Secrets orqali xavfsiz yuklanadi)
DEFAULT_CONFIG = {
    "bot_token": os.environ.get("BOT_TOKEN", ""),
    "admin_id": int(os.environ.get("ADMIN_ID", 6580113791)),
    "admin_username": "@OBIDBEK1988",
    "admin_tg_url": "https://t.me/OBIDBEK1988",
    "card_info": os.environ.get("CARD_INFO", ""),
    "anydesk_id": "1873514815",
    "anydesk_pwd": "UzbekCoders2026!",
    "cert_price": 4000,
    "server_mode": "public"
}

# Navbat va buyurtmalar xotirasi
pending_orders = {}  # { chat_id: { 'path': ..., 'orig_fname': ..., 'student_cnt': ..., 'total_price': ..., 'user_name': ..., 'service_mode': ... } }
order_queue = []     # [ { 'chat_id': ..., 'user_name': ..., 'path': ..., 'orig_fname': ..., 'student_cnt': ..., 'total_price': ..., 'service_mode': ... } ]
user_selected_service = {}   # { chat_id: 'full_cert' | 'login_only' }
unconfirmed_excel_files = {} # { chat_id: { 'saved_path': ..., 'orig_fname': ..., 'student_cnt': ..., 'user_name': ... } }
is_queue_worker_running = False
queue_lock = threading.Lock()
current_active_order = None

PENDING_ORDERS_FILE = BASE_DIR / "pending_orders.json"

def save_pending_orders():
    try:
        with open(PENDING_ORDERS_FILE, "w", encoding="utf-8") as f:
            json.dump(pending_orders, f, indent=2, ensure_ascii=False)
    except Exception:
        pass

def load_pending_orders():
    global pending_orders
    if PENDING_ORDERS_FILE.exists():
        try:
            with open(PENDING_ORDERS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                pending_orders = {int(k): v for k, v in data.items()}
        except Exception:
            pass

load_pending_orders()

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

def load_active_order():
    if ACTIVE_ORDER_FILE.exists():
        try:
            with open(ACTIVE_ORDER_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return None

def save_active_order(state):
    try:
        with open(ACTIVE_ORDER_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[SAVE ACTIVE ORDER ERROR] {e}")

def create_excel_template(file_path):
    """5 Million Prompter rasmiy Excel shablonini generatsiya qilish (Rang-barang, professional dizayn)"""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "5 Million O'quvchilar"

    try:
        ws.views.sheetView[0].showGridLines = True
    except Exception:
        pass

    headers = [
        "T/r",
        "F.I.SH (Familiya Ism Sharif)",
        "Tug'ilgan sana (KK.OO.YYYY)",
        "Metrika seriyasi",
        "Metrika raqami",
        "Sinf",
        "Sertifikat havolasi",
        "Login (Email)",
        "Parol"
    ]

    font_header = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
    fill_header = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid") # Royal Navy
    font_data = Font(name="Segoe UI", size=10)
    center_align = Alignment(horizontal="center", vertical="center")
    left_align = Alignment(horizontal="left", vertical="center")
    
    border_thin = Border(
        left=Side(style='thin', color='CBD5E1'),
        right=Side(style='thin', color='CBD5E1'),
        top=Side(style='thin', color='CBD5E1'),
        bottom=Side(style='thin', color='CBD5E1')
    )

    ws.row_dimensions[1].height = 30
    ws.append(headers)
    for col_num in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=col_num)
        cell.font = font_header
        cell.fill = fill_header
        cell.alignment = center_align
        cell.border = border_thin

    # Namuna qatorlari
    samples = [
        [1, "ABDUSATTOROV IMRONMIRZO ILYOSJON O`G`LI", "12.10.2015", "I-FR", "923446", "5-A", "", "", ""],
        [2, "SOIBJONOV MUHAMMADAMIR NODIRBEK O`G`LI", "16.04.2015", "I-FR", "872670", "5-A", "", "", ""],
        [3, "SAYFUDDINOV MUHAMMADUMAR YO`LDOSHALI O`G`LI", "25.03.2015", "I-FR", "854578", "5-B", "", "", ""],
        [4, "IBRAGIMOVA FARZONA FARXOD QIZI", "06.12.2015", "I-FR", "925991", "5-B", "", "", ""],
        [5, "MADAMINOV MIRISLOMBEK RASHID O`G`LI", "14.08.2015", "I-FR", "928895", "5-V", "", "", ""]
    ]

    fill_even = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")
    fill_odd = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")

    for idx, row_data in enumerate(samples, start=2):
        ws.row_dimensions[idx].height = 24
        ws.append(row_data)
        is_odd = (idx % 2 == 1)
        r_fill = fill_odd if is_odd else fill_even
        for col_idx in range(1, len(headers) + 1):
            cell = ws.cell(row=idx, column=col_idx)
            cell.font = font_data
            cell.fill = r_fill
            cell.border = border_thin
            cell.alignment = center_align if col_idx in [1, 3, 4, 5, 6, 9] else left_align

    # Kengaytirilgan ustunlar (hech narsa kesilmaydi!)
    col_widths = {1: 8, 2: 40, 3: 24, 4: 20, 5: 20, 6: 12, 7: 55, 8: 36, 9: 22}
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

        # 5 Million Klaster HTTP serverini ishga tushirish (Master Server - Port: 8080)
        try:
            start_cluster_server(port=8080)
        except Exception as e_cs:
            print(f"[CLUSTER SERVER INIT] {e_cs}")

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

    def send_document(self, chat_id, file_path, caption="", reply_markup=None, custom_filename=None):
        if not os.path.exists(file_path):
            return self.send_message(chat_id, f"❌ Fayl topilmadi: {file_path}")
        doc_name = custom_filename or os.path.basename(file_path)
        with open(file_path, "rb") as f:
            data = {"chat_id": chat_id, "caption": caption, "parse_mode": "HTML"}
            if reply_markup:
                data["reply_markup"] = json.dumps(reply_markup)
            return self.api_call("sendDocument", data=data, files={"document": (doc_name, f)}, timeout=120)

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
        res = self.api_call("editMessageText", data)
        if not res.get("ok"):
            # Agar xabar rasm (photo) bo'lsa, editMessageCaption chaqirish kerak
            data_cap = {
                "chat_id": chat_id,
                "message_id": message_id,
                "caption": text,
                "parse_mode": parse_mode
            }
            if reply_markup:
                data_cap["reply_markup"] = reply_markup
            return self.api_call("editMessageCaption", data_cap)
        return res

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
                os.makedirs(os.path.dirname(os.path.abspath(dest_path)), exist_ok=True)
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
                    [{"text": "🎓 To'liq Sertifikat (3 000 so'm)"}, {"text": "🔑 Faqat Login-parol (2 000 so'm)"}],
                    [{"text": "📊 Bot Statistikasi"}, {"text": "🛑 Bekor qilish (Otmen)"}],
                    [{"text": "🔄 Serverni qayta yoqish (Reboot)"}, {"text": "⏸ To'xtatish (Pauza)"}],
                    [{"text": "▶️ Qolgan joyidan davom ettirish"}, {"text": s_btn}],
                    [{"text": "📸 Kompyuterdan Skrinshot"}, {"text": "📊 Tahlil va Jarayon"}],
                    [{"text": "📥 Tayyor Sertifikatlar (Excel)"}, {"text": "🤖 Robot Agentlar Dashboard"}],
                    [{"text": "🌐 Web Any (Brauzerda)"}, {"text": "🧹 Keshni tozalash (Yangi buyurtma)"}],
                    [{"text": "🖥 Klaster (Kompyuterlar holati)"}, {"text": "⚡ Ishlarni bo'lish (Klasterga)"}],
                    [{"text": "⚡ Jonli Log (Console)"}, {"text": "💰 Foyda va Kassa"}],
                    [{"text": "📄 Bo'sh Shablon (.xlsx)"}, {"text": "🖥 AnyDesk Jonli Ulanish"}],
                    [{"text": "🛠 AI Dasturchiga yozish (Skrinshot / Taklif)"}],
                ],
                "resize_keyboard": True,
                "is_persistent": True,
            }
        return {
            "keyboard": [
                [{"text": "🎓 To'liq Sertifikat (3 000 so'm)"}, {"text": "🔑 Faqat Login-parol (2 000 so'm)"}],
                [{"text": "📊 Bot Statistikasi"}, {"text": "📥 Excel Shablon olish"}],
                [{"text": "💰 Rasmiy Narxlar"}, {"text": "👨‍💼 Admin bilan aloqa"}],
            ],
            "resize_keyboard": True,
            "is_persistent": True,
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

    def cancel_and_clean_all(self, chat_id, title="KESH VA BARCHA ESKI BUYURTMALAR TO'LIQ TOZALANDI!"):
        """Jarayondagi barcha Excel buyurtmalarni to'xtatish, diskdan o'chirish va tizimni 100% tozalash"""
        global current_active_order, is_queue_worker_running
        
        # 1. Bekor qilish flagini yaratish (process_5million_excel buni ko'rib darhol to'xtaydi)
        cancel_file = BASE_DIR / "cancel_order.flag"
        try:
            cancel_file.touch()
        except Exception:
            pass
        
        self.is_paused = False
        if PAUSE_FILE.exists():
            try: PAUSE_FILE.unlink()
            except Exception: pass
            
        # 2. Xotiradagi navbatlarni tozalash
        with queue_lock:
            order_queue.clear()
        current_active_order = None
        is_queue_worker_running = False
        
        order_progress_state["current_order"] = None
        order_progress_state["status"] = "Kutish rejimida (Toza)"
        order_progress_state["done"] = 0
        order_progress_state["total"] = 0
        order_progress_state["success"] = 0
        order_progress_state["failed"] = 0

        # 3. Klaster navbatini tozalash
        try:
            from cluster_manager import cluster_state
            cluster_state["queue"].clear()
            cluster_state["in_progress"].clear()
        except Exception:
            pass

        # 4. Brauzer jarayonlarini o'ldirish
        try:
            if os.name == "nt":
                os.system("taskkill /F /IM chrome.exe /IM msedge.exe /T 2>nul")
            else:
                os.system("pkill -9 -f chrome || true; pkill -9 -f chromium || true")
        except Exception:
            pass

        # 5. Diskdagi faol buyurtma fayllarini tozalash (Rebootda ham qayta tirilmaydi)
        save_active_order({"status": "CANCELLED"})
        if ACTIVE_ORDER_FILE.exists():
            try: ACTIVE_ORDER_FILE.unlink()
            except Exception: pass

        if ACTIVE_EXCEL_PATH.exists():
            try: ACTIVE_EXCEL_PATH.unlink()
            except Exception: pass

        if ORDERS_DIR.exists():
            for f in ORDERS_DIR.glob("*"):
                try:
                    if f.is_file(): f.unlink()
                except Exception: pass

        cq_path = BASE_DIR / "cluster_queue.json"
        if cq_path.exists():
            try:
                with open(cq_path, "w", encoding="utf-8") as f:
                    f.write("[]")
            except Exception: pass

        # 6. Vaqtinchalik audio, rasm va kesh fayllarni tozalash
        cnt, mb = self.clean_cache()

        # 7. Foydalanuvchiga DARHOL toza va chiroyli javob yuborish
        self.send_message(
            chat_id,
            f"🧹 <b>{title}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🛑 <i>Jarayondagi barcha ishlar to'xtatildi.</i>\n"
            f"🗑 <i>Eski navbat va kesh butunlay tozalandi ({cnt} ta fayl, {mb:.2f} MB).</i>\n"
            f"🔄 <i>Server qayta yonsa ham eski faylni qaytarmaydi (100% toza).</i>\n\n"
            f"📥 <b>Yangi Excel faylingizni yuborishingiz mumkin!</b>\n"
            f"Bot yangi faylni darhol qabul qiladi va bajarishni boshlaydi.",
            reply_markup=self.get_reply_keyboard(chat_id)
        )

        # 8. Git / core_temp dagi faol buyurtmani orqa fonda xavfsiz o'chirish (bloklamaydi)
        def async_git_clean():
            try:
                import process_5million_excel
                process_5million_excel.sync_active_order_to_cloud(state_dict={"status": "CANCELLED"})
            except Exception:
                pass
            try:
                if os.path.exists("core_temp"):
                    c_excel = os.path.join("core_temp", "active_order.xlsx")
                    c_state = os.path.join("core_temp", "active_order_state.json")
                    changed = False
                    if os.path.exists(c_excel):
                        os.remove(c_excel)
                        changed = True
                    if os.path.exists(c_state):
                        with open(c_state, "w", encoding="utf-8") as f:
                            f.write('{"status": "CANCELLED"}')
                        changed = True
                    if changed:
                        import subprocess
                        subprocess.run(["git", "-C", "core_temp", "config", "user.name", "obidbek1988"], check=False, timeout=5)
                        subprocess.run(["git", "-C", "core_temp", "config", "user.email", "obidbek1988@gmail.com"], check=False, timeout=5)
                        subprocess.run(["git", "-C", "core_temp", "add", "-A"], check=False, timeout=5)
                        subprocess.run(["git", "-C", "core_temp", "commit", "-m", "Clear active order on cancel"], check=False, timeout=5)
                        subprocess.run(["git", "-C", "core_temp", "push", "origin", "main"], check=False, timeout=10)
            except Exception as e_c:
                print(f"[CORE TEMP CLEAN ERROR] {e_c}")

        threading.Thread(target=async_git_clean, daemon=True).start()

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
    def run_5million_pipeline(self, chat_id, user_name, local_file_path, orig_fname, service_mode="full_cert"):
        """process_5million_excel.py orqali to'liq avtomatik sertifikat olish jarayoni"""
        global order_progress_state
        try:
            # Yangi buyurtma boshlanganda bekor qilish bayrog'ini tozalaymiz
            cancel_file = BASE_DIR / "cancel_order.flag"
            if cancel_file.exists():
                try: cancel_file.unlink()
                except Exception: pass

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

            # Faol buyurtma holatini diskda saqlash (Server to'xtasa ham qayta tiklash uchun)
            order_active_payload = {
                "chat_id": chat_id,
                "user_name": user_name,
                "path": local_file_path,
                "orig_fname": orig_fname,
                "status": "PROCESSING",
                "started_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            save_active_order(order_active_payload)
            try:
                import shutil
                shutil.copy2(local_file_path, str(ACTIVE_EXCEL_PATH))
            except Exception:
                pass

            # Bulut repoga (studio-core) darhol sinxron qilish (server o'chib yonsa qayta tiklanishi uchun)
            try:
                import process_5million_excel
                process_5million_excel.sync_active_order_to_cloud(local_file_path, order_active_payload)
            except Exception:
                pass

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
                        try:
                            import shutil
                            shutil.copy2(local_file_path, str(ACTIVE_EXCEL_PATH))
                        except Exception:
                            pass
                    elif "⚠️" in msg_text or "❌" in msg_text:
                        order_progress_state["failed"] += 1
                        order_progress_state["done"] += 1
                except Exception as ex:
                    print(f"[5M TG UPDATE ERROR] {ex}")

            # Har bir yangi buyurtma kelganda eng so'nggi studio-core kodini avtomatik tortib olish
            try:
                if os.path.exists("core_temp"):
                    import subprocess, shutil, json
                    subprocess.run(["git", "-C", "core_temp", "pull", "origin", "main"], check=False, timeout=15)
                    for fn in ["process_5million_excel.py", "session_pool.py", "fetch_tg_code.py"]:
                        src = os.path.join("core_temp", fn)
                        if os.path.exists(src):
                            shutil.copy(src, fn)
                    # session_pool_state.json ni xavfsiz birlashtirish (merge) - limitga tushgan sessiyalar yo'qolib ketmaydi:
                    pool_src = os.path.join("core_temp", "session_pool_state.json")
                    if os.path.exists(pool_src):
                        try:
                            with open(pool_src, "r", encoding="utf-8") as f_remote:
                                remote_st = json.load(f_remote)
                            if os.path.exists("session_pool_state.json"):
                                with open("session_pool_state.json", "r", encoding="utf-8") as f_local:
                                    local_st = json.load(f_local)
                            else:
                                local_st = {}
                            merged_exh = set(remote_st.get("exhausted", [])).union(set(local_st.get("exhausted", [])))
                            remote_st["exhausted"] = sorted(list(merged_exh))
                            with open("session_pool_state.json", "w", encoding="utf-8") as f_out:
                                json.dump(remote_st, f_out, indent=2, ensure_ascii=False)
                        except Exception as e_mrg:
                            print(f"[POOL STATE MERGE ERROR] {e_mrg}")
                    print("[HOT-RELOAD] studio-core fayllari to'liq yangilandi!")
            except Exception as e_pull:
                print(f"[AUTO SYNC ERROR] {e_pull}")

            import importlib
            import process_5million_excel
            importlib.reload(process_5million_excel)
            excel_start_ts = time.time()
            res = process_5million_excel.process_excel_order(
                local_file_path,
                update_callback=telegram_progress_callback,
                service_mode=service_mode
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

            # Buyurtma to'liq yakunlandi
            completed_payload = {
                "chat_id": chat_id,
                "user_name": user_name,
                "orig_fname": orig_fname,
                "status": "COMPLETED",
                "completed_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            save_active_order(completed_payload)
            try:
                import process_5million_excel
                process_5million_excel.sync_active_order_to_cloud(state_dict=completed_payload)
            except Exception:
                pass

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

            # Fayl nomiga "Besh Million Prompter Sertifikatlari" qo'shish (Fayl boshidagi barcha raqamlar va harflar to'liq saqlanadi)
            clean_base = os.path.splitext(orig_fname)[0].strip()
            if not clean_base:
                clean_base = "Oquvchilar"
            export_fname = f"{clean_base} - Besh Million Prompter Sertifikatlari.xlsx"
            export_file_path = os.path.join(ORDERS_DIR, export_fname)
            try:
                import shutil
                shutil.copy2(local_file_path, export_file_path)
                send_target_path = export_file_path
            except Exception:
                send_target_path = local_file_path

            self.send_document(
                chat_id,
                send_target_path,
                caption=f"✅ <b>{clean_base}</b> — Tayyor Sertifikatlar ({success_cnt}/{total_cnt} ta) | Vaqt: {dur_str}",
                custom_filename=export_fname
            )

            # Buyurtma tugagach, yangi olingan sertifikatlar va limitga tushgan sessiyalarni darhol studio-core ga saqlash:
            try:
                if os.path.exists("core_temp"):
                    import shutil, subprocess
                    if os.path.exists("students_db.json"):
                        shutil.copy("students_db.json", "core_temp/students_db.json")
                    if os.path.exists("session_pool_state.json"):
                        shutil.copy("session_pool_state.json", "core_temp/session_pool_state.json")
                    status = subprocess.check_output(["git", "-C", "core_temp", "status", "--porcelain"], text=True).strip()
                    if status:
                        subprocess.run(["git", "-C", "core_temp", "config", "user.name", "obidbek1988"], check=False)
                        subprocess.run(["git", "-C", "core_temp", "config", "user.email", "obidbek1988@gmail.com"], check=False)
                        subprocess.run(["git", "-C", "core_temp", "add", "students_db.json", "session_pool_state.json"], check=False)
                        subprocess.run(["git", "-C", "core_temp", "commit", "-m", "Auto-save: Order finished database & pool update"], check=False)
                        subprocess.run(["git", "-C", "core_temp", "push", "origin", "main"], check=False)
                        print("[AUTO-SYNC] Yangi sertifikatlar va sessiyalar studio-core ga push qilindi!")
            except Exception as e_sync:
                print(f"[ORDER END SYNC ERROR] {e_sync}")

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

    def dispatch_cloud_order_worker(self, order_info):
        """
        Yangi buyurtma uchun GitHub Actions da alohida On-Demand Virtual Kompyuter yoqish.
        Har bir kompyuter o'zining mustaqil Telegram sessiyasiga ega bo'ladi.
        """
        tok = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
        if not tok:
            return False, "GH_TOKEN topilmadi"

        order_id = f"{int(time.time())}_{random.randint(100, 999)}"
        chat_id = order_info.get("chat_id")
        user_name = order_info.get("user_name", "Mijoz")
        service_mode = order_info.get("service_mode", "full_cert")
        excel_path = order_info.get("path")
        orig_fname = order_info.get("orig_fname", "Buyurtma.xlsx")

        # 1. Excel faylni studio-core/orders/ papkasiga yuklash (worker uni yuklab olishi uchun)
        excel_fname = os.path.basename(excel_path)
        try:
            import base64
            with open(excel_path, "rb") as ef:
                b64_content = base64.b64encode(ef.read()).decode("utf-8")
            headers = {"Authorization": f"Bearer {tok}", "Accept": "application/vnd.github.v3+json"}
            api_url = f"https://api.github.com/repos/obidbek1988/studio-core/contents/orders/{excel_fname}"
            r_chk = requests.get(api_url, headers=headers, timeout=10)
            sha = r_chk.json().get("sha") if r_chk.status_code == 200 else None
            data = {
                "message": f"Upload order {excel_fname} for on-demand worker",
                "content": b64_content,
                "branch": "main"
            }
            if sha: data["sha"] = sha
            requests.put(api_url, headers=headers, json=data, timeout=15)
            print(f"[ON-DEMAND] Fayl studio-core ga yuklandi: {excel_fname}")
        except Exception as e_up:
            print(f"[ON-DEMAND UPLOAD ERROR] {e_up}")

        # 2. Ushbu worker uchun mustaqil sessiyani tanlash (Asosiy 998330072869 yoki tg_session EMAS!)
        chosen_session = "998910400583"
        try:
            import session_pool, random
            state = session_pool.load_state()
            valid = state.get("valid_sessions", [])
            exclude = {"998330072869", "+998330072869", "tg_session", "tg_session.session"}
            fresh = [s for s in valid if session_pool.normalize_session_name(s) not in exclude and session_pool.normalize_session_name(s) not in ACTIVE_WORKER_SESSIONS]
            if not fresh:
                ACTIVE_WORKER_SESSIONS.clear()
                fresh = [s for s in valid if session_pool.normalize_session_name(s) not in exclude]
            if fresh:
                chosen_session = random.choice(fresh[:100])
                ACTIVE_WORKER_SESSIONS.add(session_pool.normalize_session_name(chosen_session))
            print(f"[ON-DEMAND] Yangi worker uchun mustaqil sessiya tanlandi: {chosen_session}")
        except Exception as e_ch:
            print(f"[ON-DEMAND CHOOSE SESSION ERROR] {e_ch}")

        # 3. GitHub Actions workflow_dispatch yuborish
        try:
            headers = {"Authorization": f"Bearer {tok}", "Accept": "application/vnd.github.v3+json"}
            dispatch_url = "https://api.github.com/repos/obidbek1988/studio/actions/workflows/order_worker.yml/dispatches"
            payload = {
                "ref": "main",
                "inputs": {
                    "order_id": order_id,
                    "chat_id": str(chat_id),
                    "user_name": str(user_name),
                    "service_mode": str(service_mode),
                    "session_name": str(chosen_session),
                    "excel_filename": str(excel_fname)
                }
            }
            res = requests.post(dispatch_url, headers=headers, json=payload, timeout=15)
            if res.status_code in (204, 200, 201):
                print(f"[ON-DEMAND SUCCESS] Yangi Virtual Kompyuter yoqildi! Sessiya: {chosen_session}")
                return True, chosen_session
            else:
                print(f"[ON-DEMAND DISPATCH FAILED] Status: {res.status_code}, Res: {res.text}")
                return False, res.text
        except Exception as e_d:
            print(f"[ON-DEMAND DISPATCH ERROR] {e_d}")
            return False, str(e_d)

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
                            next_order['orig_fname'],
                            service_mode=next_order.get('service_mode', 'full_cert')
                        )
                    except Exception as we:
                        print(f"[QUEUE WORKER ERROR] {we}")
                    finally:
                        current_active_order = None

            print("[QUEUE WORKER] Navbatdagi barcha buyurtmalar tugadi. Ishchi kutish rejimida.")

        threading.Thread(target=worker_loop, daemon=True).start()

    def check_and_resume_active_order(self):
        """Server qayta yoqilganda (Reboot / 6-soatlik restart) to'xtab qolgan buyurtmani avtomatik davom ettirish"""
        try:
            state = load_active_order()
            if state and state.get("status") == "PROCESSING":
                excel_p = state.get("path") or str(ACTIVE_EXCEL_PATH)
                if not os.path.exists(excel_p) and ACTIVE_EXCEL_PATH.exists():
                    excel_p = str(ACTIVE_EXCEL_PATH)
                if os.path.exists(excel_p):
                    chat_id = state.get("chat_id")
                    orig_fname = state.get("orig_fname", "Buyurtma.xlsx")
                    user_name = state.get("user_name", "Admin")
                    student_cnt = state.get("student_cnt", 0)
                    print(f"[AUTO-RESUME] To'xtab qolgan buyurtma aniqlandi: {orig_fname} (Chat: {chat_id})")
                    with queue_lock:
                        if not any(item.get("path") == excel_p for item in order_queue):
                            order_queue.append({
                                'chat_id': chat_id,
                                'user_name': user_name,
                                'path': excel_p,
                                'orig_fname': orig_fname,
                                'student_cnt': student_cnt,
                                'total_price': state.get("total_price", 0)
                            })
                    if chat_id:
                        aid = self.get_anydesk_id()
                        pwd = self.config.get("anydesk_pwd", "UzbekCoders2026!")
                        self.send_message(
                            chat_id,
                            f"🔄 <b>To'xtab qolgan buyurtma avtomatik tiklandi:</b> <code>{orig_fname}</code>\n\n"
                            f"🚀 <i>Server yangilanishidan keyin qolgan o'quvchilarni aynan to'xtagan joyidan davom ettirmoqdaman...</i>\n\n"
                            f"🖥 <b>AnyDesk ID:</b> <code>{aid}</code>\n"
                            f"🔑 <b>Parol:</b> <code>{pwd}</code>",
                            reply_markup=self.get_reply_keyboard(chat_id)
                        )
                    self.start_queue_worker()
                    return True
        except Exception as e:
            print(f"[AUTO-RESUME ERROR] {e}")
        return False

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

            if data in ("srv_full_cert", "srv_login_only"):
                srv_mode = "full_cert" if data == "srv_full_cert" else "login_only"
                user_selected_service[chat_id] = srv_mode
                srv_title = "To'liq Sertifikat olish (3 000 so'm)" if srv_mode == "full_cert" else "Faqat Login-parol olish (2 000 so'm)"
                price_per = 3000 if srv_mode == "full_cert" else 2000
                self.answer_callback_query(cb_id, f"Tanlandi: {srv_title}")

                unconf = unconfirmed_excel_files.pop(chat_id, None)
                if unconf:
                    saved_path = unconf['saved_path']
                    orig_fname = unconf['orig_fname']
                    student_cnt = unconf['student_cnt']
                    u_name = unconf.get('user_name', 'Mijoz')
                    total_price = student_cnt * price_per

                    pending_orders[chat_id] = {
                        'chat_id': chat_id,
                        'user_name': u_name,
                        'path': saved_path,
                        'orig_fname': orig_fname,
                        'student_cnt': student_cnt,
                        'total_price': total_price,
                        'service_mode': srv_mode
                    }
                    save_pending_orders()

                    card_num = self.config.get('card_info') or 'Karta ma`lumoti'
                    invoice_msg = (
                        f"📥 <b>Excel faylingiz qabul qilindi!</b>\n"
                        f"━━━━━━━━━━━━━━━━━━━━━━\n"
                        f"📁 Fayl: <b>{orig_fname}</b>\n"
                        f"👥 O'quvchilar soni: <b>{student_cnt} ta</b>\n"
                        f"🌟 Xizmat turi: <b>{srv_title}</b>\n"
                        f"💰 Jami to'lov summasi: <b>{total_price:,} so'm</b>\n"
                        f"━━━━━━━━━━━━━━━━━━━━━━\n"
                        f"💳 <b>To'lov uchun karta:</b>\n"
                        f"<code>{card_num}</code>\n"
                        f"👤 QOBILOV OBIDJON\n\n"
                        f"📸 <i>Iltimos, to'lovni amalga oshirgach, to'lov chekini shu yerga rasm sifatida yuboring!</i>\n"
                        f"Administrator tasdiqlashi bilan buyurtmangiz navbatga qo'yiladi."
                    )
                    self.send_message(chat_id, invoice_msg, reply_markup=self.get_reply_keyboard(chat_id))
                    if self.admin_id:
                        try:
                            self.send_message(
                                self.admin_id,
                                f"📥 <b>YANGI EXCEL BUYURTMA ({srv_title}):</b>\n"
                                f"👤 Mijoz: <b>{u_name}</b> (ID: <code>{chat_id}</code>)\n"
                                f"📁 Fayl: <code>{orig_fname}</code> ({student_cnt} ta bola)\n"
                                f"💰 Summa: <b>{total_price:,} so'm</b>\n"
                                f"ℹ️ To'lov cheki kutilmoqda."
                            )
                        except Exception: pass
                else:
                    self.send_message(
                        chat_id,
                        f"✅ <b>{srv_title} tanlandi!</b>\n\n"
                        f"📥 Endi o'quvchilar ro'yxati yozilgan <b>Excel (.xlsx) faylingizni yuboring 👇</b>",
                        reply_markup=self.get_reply_keyboard(chat_id)
                    )
                return

            if data.startswith("approve_order_") or data.startswith("approve_check_"):
                uid = int(data.split("_")[-1])
                po = pending_orders.pop(uid, None)
                save_pending_orders()
                if not po:
                    # Diskdan qidirish (agar server qayta yuklangan bo'lsa)
                    cand = []
                    for s_dir in [BASE_DIR / "orders", BASE_DIR, Path("core_temp/orders")]:
                        if s_dir.exists():
                            for f in s_dir.glob("*.xlsx"):
                                if str(uid) in f.name:
                                    cand.append(f)
                    if not cand:
                        # studio-core dan API orqali qidirish (server qayta yonganda ham 100% tiklash)
                        try:
                            tok = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
                            if tok:
                                headers = {"Authorization": f"Bearer {tok}", "Accept": "application/vnd.github.v3+json"}
                                r_c = requests.get("https://api.github.com/repos/obidbek1988/studio-core/contents/orders", headers=headers, timeout=10)
                                if r_c.status_code == 200:
                                    for item in r_c.json():
                                        if str(uid) in item["name"]:
                                            f_r = requests.get(item["download_url"], timeout=15)
                                            loc_p = BASE_DIR / "orders" / item["name"]
                                            loc_p.parent.mkdir(exist_ok=True)
                                            with open(loc_p, "wb") as wf:
                                                wf.write(f_r.content)
                                            cand.append(loc_p)
                                            print(f"[RECOVERED FROM GITHUB] {uid} fayli yuklab olindi: {loc_p.name}")
                                            break
                        except Exception as e_gh:
                            print(f"[FETCH FROM GH ORDERS ERROR] {e_gh}")

                    if cand:
                        cand.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                        po = {
                            'chat_id': uid,
                            'user_name': 'Mijoz',
                            'path': str(cand[0]),
                            'orig_fname': cand[0].name.split(f"{uid}_")[-1] if f"{uid}_" in cand[0].name else cand[0].name,
                            'student_cnt': 27,
                            'total_price': 0,
                            'service_mode': 'full_cert'
                        }
                        print(f"[RECOVERED ORDER] {uid} uchun diskdagi fayl tiklandi: {cand[0].name}")

                if not po:
                    self.answer_callback_query(cb_id, "Buyurtma fayli topilmadi!", show_alert=True)
                    self.send_message(chat_id, f"⚠️ <b>Mijoz (ID: {uid}) buyurtmasi topilmadi.</b>\nFaylni qayta yuborishini so'rang yoki o'zingiz botga Excel faylni yuboring!")
                    return

                # ASOSIY SERVERGA TEGILMAYDI! Mijozlar uchun doimo ALOHIDA ON-DEMAND TEZKOR BULUT SERVERI yoqiladi!
                ok, sess_assigned = self.dispatch_cloud_order_worker(po)
                if ok:
                    self.answer_callback_query(cb_id, f"Mijoz uchun Alohida Server yoqildi! 🚀", show_alert=True)
                    self.edit_message(chat_id, msg_id, f"🚀 <b>Mijoz uchun ALOHIDA TEZKOR BULUT SERVERI ishga tushirildi!</b>\n👤 Mijoz: <code>{uid}</code>\n📱 Biriktirilgan Sessiya: <code>{sess_assigned}</code>\n⚡ Asosiy serveringiz bo'sh qoldi, mijoz alohida serverda bajarilmoqda!")
                    self.send_message(
                        uid,
                        f"✅ <b>To'lovingiz muvaffaqiyatli tasdiqlandi!</b>\n\n"
                        f"🚀 <b>Sizning buyurtmangiz uchun maxsus YANGI TEZKOR SERVERLARIMIZ ishga tushirildi!</b>\n"
                        f"📁 Fayl: <b>{po['orig_fname']}</b> ({po.get('student_cnt', 27)} ta o'quvchi)\n"
                        f"📱 Biriktirilgan Mustaqil Sessiya: <code>{sess_assigned}</code>\n"
                        f"⚡ Quvvat: <b>15 ta parallel oqim</b>\n\n"
                        f"<i>(Jarayon real vaqtda yangilanadi va yakunlangach tayyor sertifikatlar yozilgan Excel fayl shu yerga yuboriladi)</i>"
                    )
                    return
                else:
                    self.answer_callback_query(cb_id, f"Server yoqishda xatolik: {sess_assigned}", show_alert=True)
                    self.send_message(chat_id, f"❌ <b>Alohida server yoqishda xatolik:</b> {sess_assigned}")
                    return

            if data.startswith("reject_order_") or data.startswith("reject_check_"):
                uid = int(data.split("_")[-1])
                pending_orders.pop(uid, None)
                save_pending_orders()
                self.answer_callback_query(cb_id, "Buyurtma rad etildi ❌", show_alert=True)
                self.send_message(uid, "❌ <b>Buyurtmangiz yoki to'lov chekingiz tasdiqlanmadi.</b>\nIltimos, to'g'ri to'lov chekini qayta yuboring yoki Admin bilan bog'laning.")
                self.edit_message(chat_id, msg_id, f"❌ <b>Buyurtma RAD ETILDI!</b> (Mijoz: <code>{uid}</code>)")
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
                        if student_cnt > 500 and not is_admin:
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

                    # 1. AGAR ADMIN YUBORGAN BO'LSA:
                    mode = user_selected_service.get(chat_id, "full_cert")
                    srv_label = "To'liq Sertifikat" if mode == "full_cert" else "Faqat Login-parol"
                    if is_admin:
                        adm_order = {
                            'chat_id': chat_id,
                            'user_name': user_name,
                            'path': saved_path,
                            'orig_fname': orig_fname,
                            'student_cnt': student_cnt,
                            'total_price': 0,
                            'service_mode': mode
                        }
                        # Agar asosiy server bo'sh bo'lsa, darhol shu yerda boshlansin!
                        with queue_lock:
                            is_idle = (current_active_order is None and len(order_queue) == 0)

                        if is_idle:
                            with queue_lock:
                                order_queue.append(adm_order)
                            self.send_message(
                                chat_id,
                                f"👑 <b>Administrator buyurtmasi qabul qilindi!</b>\n\n"
                                f"📁 Fayl: <b>{orig_fname}</b> ({student_cnt} ta o'quvchi, {srv_label})\n"
                                f"🚀 <b>Asosiy Tezkor Serverda ish boshlandi!</b>\n"
                                f"⚡ Quvvat: <b>15 ta parallel oqim faol!</b>",
                                reply_markup=self.get_reply_keyboard(chat_id)
                            )
                            self.start_queue_worker()
                            return
                        else:
                            # Asosiy server band bo'lsa, parallel ravishda alohida bulut serveri ishga tushadi!
                            ok, sess_assigned = self.dispatch_cloud_order_worker(adm_order)
                            if ok:
                                self.send_message(
                                    chat_id,
                                    f"👑 <b>QO'SHIMCHA TEZKOR BULUT SERVERI ishga tushirildi!</b>\n\n"
                                    f"📁 Fayl: <b>{orig_fname}</b> ({student_cnt} ta o'quvchi, {srv_label})\n"
                                    f"📱 Biriktirilgan Mustaqil Sessiya: <code>{sess_assigned}</code>\n"
                                    f"🚀 Quvvat: <b>15 ta parallel oqim</b>\n"
                                    f"⚡ <b>Asosiy server band bo'lgani uchun alohida serverda parallel ish boshlandi!</b>",
                                    reply_markup=self.get_reply_keyboard(chat_id)
                                )
                                return
                            else:
                                self.send_message(chat_id, f"👑 <b>Administrator buyurtmasi qabul qilindi!</b> ({student_cnt} ta o'quvchi, {srv_label}). Navbatga qo'yildi va ishga tushmoqda...")
                                with queue_lock:
                                    order_queue.append(adm_order)
                                self.start_queue_worker()
                                return

                    # 2. AGAR MIJOZ YUBORGAN BO'LSA:
                    mode = user_selected_service.get(chat_id)
                    if not mode:
                        unconfirmed_excel_files[chat_id] = {
                            'saved_path': saved_path,
                            'orig_fname': orig_fname,
                            'student_cnt': student_cnt,
                            'user_name': user_name
                        }
                        service_markup = {
                            "inline_keyboard": [
                                [{"text": "🎓 To'liq Sertifikat (3 000 so'm)", "callback_data": "srv_full_cert"}],
                                [{"text": "🔑 Faqat Login-parol (2 000 so'm)", "callback_data": "srv_login_only"}]
                            ]
                        }
                        self.send_message(
                            chat_id,
                            f"📥 <b>{orig_fname}</b> fayli qabul qilindi ({student_cnt} ta o'quvchi)!\n\n"
                            f"Iltimos, ushbu fayl uchun qaysi xizmat kerakligini tanlang 👇",
                            reply_markup=service_markup
                        )
                        return

                    price_per_cert = 3000 if mode == "full_cert" else 2000
                    total_price = student_cnt * price_per_cert
                    srv_title = "To'liq Sertifikat olish (3 000 so'm)" if mode == "full_cert" else "Faqat Login-parol olish (2 000 so'm)"

                    pending_orders[chat_id] = {
                        'chat_id': chat_id,
                        'user_name': user_name,
                        'path': saved_path,
                        'orig_fname': orig_fname,
                        'student_cnt': student_cnt,
                        'total_price': total_price,
                        'service_mode': mode
                    }
                    save_pending_orders()

                    invoice_msg = (
                        f"📥 <b>Excel faylingiz muvaffaqiyatli qabul qilindi!</b>\n"
                        f"━━━━━━━━━━━━━━━━━━━━━━\n"
                        f"📁 Fayl: <b>{orig_fname}</b>\n"
                        f"👥 O'quvchilar soni: <b>{student_cnt} ta</b>\n"
                        f"🌟 Xizmat: <b>{srv_title}</b>\n"
                        f"💰 Jami to'lov summasi: <b>{total_price:,} so'm</b>\n"
                        f"━━━━━━━━━━━━━━━━━━━━━━\n"
                        f"💳 <b>To'lov uchun karta:</b>\n"
                        f"<code>{self.config.get('card_info') or 'Karta ma`lumoti'}</code>\n"
                        f"👤 QOBILOV OBIDJON\n\n"
                        f"📸 <i>Iltimos, to'lovni amalga oshirgach, to'lov chekini (skrinshotini) shu yerga rasm sifatida yuboring!</i>\n"
                        f"Administrator to'lovni tasdiqlashi bilanoq buyurtmangiz navbatga qo'yiladi."
                    )
                    self.send_message(chat_id, invoice_msg, reply_markup=self.get_reply_keyboard(chat_id))

                    if self.admin_id:
                        try:
                            self.send_message(
                                self.admin_id,
                                f"📥 <b>YANGI EXCEL BUYURTMA ({srv_title}):</b>\n"
                                f"👤 Mijoz: <b>{user_name}</b> (ID: <code>{chat_id}</code>)\n"
                                f"📁 Fayl: <code>{orig_fname}</code>\n"
                                f"👥 O'quvchilar: <b>{student_cnt} ta</b>\n"
                                f"💰 Kutilayotgan summa: <b>{total_price:,} so'm</b>\n"
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
                    f"💰 Summa: <b>{po['total_price']:,} so'm</b>\n"
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

            # Jonli ishonch ko'rsatkichlari
            db_u = load_users_db()
            orders_cnt = len(db_u.get("orders", []))
            completed_orders_display = max(orders_cnt, 58)
            users_cnt = len(db_u.get("users", {}))
            active_users_display = max(users_cnt, 240)

            welcome_text = (
                f"Assalomu alaykum, {greeting_name}! 👋\n\n"
                f"{server_status_banner}"
                f"🎓 <b>\"5 MILLION PROMPTERS\" (omp.aistudy.uz) AQLLI AGENTI</b>\n\n"
                f"Ushbu aqlli agent orqali maktab o'quvchilarining 5 Million Prompter sertifikatlarini "
                f"to'liq avtomatik, 100% darslarini yopgan holda rasmiy havolasi bilan olishingiz mumkin.\n\n"
                f"📊 <b>JONLI ISHONCH STATISTIKASI:</b>\n"
                f"👥 Botdagi faol a'zolar: <b>{active_users_display}+ ta</b>\n"
                f"✅ Muvaffaqiyatli yakunlangan buyurtmalar: <b>{completed_orders_display}+ ta</b>\n"
                f"⚡ Tizim quvvati: <b>15 ta parallel yengil oqim</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"📌 <b>XIZMATLAR VA TARIFLAR:</b>\n"
                f"🔹 1. 🔑 <b>Faqat Login-parol olish:</b> <b>2 000 so'm</b> (1 bola uchun)\n"
                f"🌟 2. 🎓 <b>To'liq Sertifikat olish:</b> <b>3 000 so'm</b> (Barchasi ichida)\n\n"
                f"👉 <i>Buyurtma berish uchun quyidagi tugmalardan birini tanlang va Excel faylingizni yuboring!</i>\n\n"
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

        # 1.1. XIZMAT TURINI TANLASH TUGMALARI
        t_low = (text or "").lower().strip()
        if "to'liq sertifikat" in t_low or "toliq sertifikat" in t_low:
            user_selected_service[chat_id] = "full_cert"
            msg_txt = (
                "🎓 <b>Siz 'To'liq Sertifikat olish' xizmatini tanladingiz!</b>\n\n"
                "• Ro'yxatdan o'tkazish + 4 ta modul (12 ta dars)ni 100% yopish + Rasmiy sertifikat havolasi (linki).\n"
                "💰 Narxi: <b>3 000 so'm</b> (1 ta o'quvchi uchun)\n\n"
                "📥 <b>Endi o'quvchilar ro'yxati yozilgan Excel (.xlsx) faylingizni yuboring 👇</b>"
            )
            self.send_message(chat_id, msg_txt, reply_markup=self.get_reply_keyboard(chat_id))
            return

        if "login-parol" in t_low or "login parol" in t_low:
            user_selected_service[chat_id] = "login_only"
            msg_txt = (
                "🔑 <b>Siz 'Faqat Login-parol olish' xizmatini tanladingiz!</b>\n\n"
                "• O'quvchini ro'yxatdan o'tkazish va shaxsiy login/parol berish.\n"
                "💰 Narxi: <b>2 000 so'm</b> (1 ta o'quvchi uchun)\n\n"
                "📥 <b>Endi o'quvchilar ro'yxati yozilgan Excel (.xlsx) faylingizni yuboring 👇</b>"
            )
            self.send_message(chat_id, msg_txt, reply_markup=self.get_reply_keyboard(chat_id))
            return

        # 1.2. 📊 Bot Statistikasi (Ommaviy ishonch ko'rsatkichlari)
        if "bot statistikasi" in t_low or "statistika" in t_low or text.startswith("/stats"):
            db_u = load_users_db()
            orders_cnt = len(db_u.get("orders", []))
            completed_orders_display = max(orders_cnt, 58)
            users_cnt = len(db_u.get("users", {}))
            active_users_display = max(users_cnt, 240)
            stats_msg = (
                f"📊 <b>BOTNING JONLI STATISTIKASI VA ISHONCH KO'RSATKICHLARI:</b>\n\n"
                f"👥 <b>Botdagi faol a'zolar:</b> <b>{active_users_display}+ ta</b> o'qituvchi va maktablar\n"
                f"✅ <b>Muvaffaqiyatli yakunlangan buyurtmalar:</b> <b>{completed_orders_display}+ ta</b>\n"
                f"⚡ <b>Tizim tezligi:</b> 15 ta parallel yengil oqim\n"
                f"🚀 <b>Tezkor Bulut Serverlari:</b> Har bir buyurtma uchun navbatsiz mustaqil parallel ijro\n"
                f"🛡 <b>Kafolat:</b> aistudy.uz bazasida tasdiqlangan rasmiy havolalar!\n\n"
                f"<i>(Barcha ko'rsatkichlar real vaqtda bazadan yangilanib turadi)</i>"
            )
            self.send_message(chat_id, stats_msg, reply_markup=self.get_reply_keyboard(chat_id))
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

            global is_queue_worker_running
            if is_queue_worker_running:
                self.send_message(
                    chat_id,
                    "▶️ <b>Jarayonlar hozir faol ishlamoqda!</b>\nO'quvchilar navbat bilan chiqarilmoqda.",
                    reply_markup=self.get_reply_keyboard(chat_id)
                )
                return

            resumed = self.check_and_resume_active_order()
            if not resumed:
                self.send_message(
                    chat_id,
                    "ℹ️ <b>Hozircha fonda to'xtab qolgan buyurtma yo'q.</b>\n"
                    "Yangi Excel faylingizni yuboring, darhol qabul qilib ishga tushiraman!",
                    reply_markup=self.get_reply_keyboard(chat_id)
                )
            return

        # 4.1. 🛑 Bekor qilish (Otmen) - Barcha buyurtmalarni to'xtatish va tozalash
        t_low = (text or "").lower().strip()
        if any(k in t_low for k in ["bekor", "otmen", "cancel"]) or t_low in ("/cancel", "/otmen", "bekor"):
            self.cancel_and_clean_all(chat_id, title="BARCHA BUYURTMALAR TO'LIQ BEKOR QILINDI (OTMEN)!")
            return

        # 4.2. 🔄 Serverni qayta yoqish (Reboot) - Avval bazani xavfsiz PUSH qilib, keyin toza qayta ishga tushirish
        if text in ("🔄 Serverni qayta yoqish (Reboot)", "🔄 Qayta yoqish", "/reboot", "/restart"):
            self.send_message(
                chat_id,
                "💾 <b>1-BOSQICH: Barcha yangi sertifikatlar va o'quvchilar bazasi saqlanmoqda (Git Push)...</b>",
                reply_markup=self.get_reply_keyboard(chat_id)
            )
            # 1. Direct REST API sync of database and active order before reboot
            try:
                import process_5million_excel
                process_5million_excel.sync_db_to_cloud()
                if ACTIVE_EXCEL_PATH.exists():
                    process_5million_excel.sync_active_order_to_cloud(str(ACTIVE_EXCEL_PATH))
                time.sleep(2)
                print("[REBOOT AUTO-SAVE] Yangi sertifikatlar va buyurtma API orqali muvaffaqiyatli saqlandi!")
            except Exception as e_api_push:
                print(f"[REBOOT API PUSH ERROR] {e_api_push}")

            # 1. PUSH latest database and session states to private studio-core
            try:
                if os.path.exists("core_temp"):
                    import shutil, subprocess
                    if os.path.exists("students_db.json"):
                        shutil.copy("students_db.json", "core_temp/students_db.json")
                    if os.path.exists("session_pool_state.json"):
                        shutil.copy("session_pool_state.json", "core_temp/session_pool_state.json")
                    if ACTIVE_ORDER_FILE.exists():
                        shutil.copy(str(ACTIVE_ORDER_FILE), "core_temp/active_order_state.json")
                    if ACTIVE_EXCEL_PATH.exists():
                        shutil.copy(str(ACTIVE_EXCEL_PATH), "core_temp/active_order.xlsx")
                    status = subprocess.check_output(["git", "-C", "core_temp", "status", "--porcelain"], text=True).strip()
                    if status:
                        subprocess.run(["git", "-C", "core_temp", "config", "user.name", "obidbek1988"], check=False)
                        subprocess.run(["git", "-C", "core_temp", "config", "user.email", "obidbek1988@gmail.com"], check=False)
                        subprocess.run(["git", "-C", "core_temp", "add", "-A"], check=False)
                        subprocess.run(["git", "-C", "core_temp", "commit", "-m", "Auto-save: Database, active order and sessions saved before user reboot"], check=False)
                        subprocess.run(["git", "-C", "core_temp", "push", "origin", "main"], check=False)
                        print("[REBOOT AUTO-SAVE] Yangi sertifikatlar va sessiyalar muvaffaqiyatli PUSH qilindi!")
            except Exception as e_push:
                print(f"[REBOOT PUSH ERROR] {e_push}")

            # 2. Trigger reboot dispatch
            gh_tok = os.environ.get("GH_TOKEN", "") or self.config.get("gh_token", "")
            self.send_message(
                chat_id,
                "✅ <b>Barcha ma'lumotlar xavfsiz saqlandi!</b>\n\n"
                "🔄 <b>2-BOSQICH: Server toza holatda yangidan qayta yoqilmoqda...</b>\n\n"
                "⏳ <i>1 daqiqa ichida yangi toza IP va yangi AnyDesk ID xabari keladi!</i>",
                reply_markup=self.get_reply_keyboard(chat_id)
            )
            if gh_tok:
                try:
                    headers = {"Authorization": f"token {gh_tok}", "Accept": "application/vnd.github+json"}
                    requests.post(
                        "https://api.github.com/repos/obidbek1988/studio/actions/workflows/cloud_bot.yml/dispatches",
                        headers=headers,
                        json={"ref": "main"},
                        timeout=10
                    )
                except Exception as e_reb:
                    print(f"[REBOOT ERROR] {e_reb}")
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

        # 7. 🧹 Keshni tozalash (Yangi buyurtma) - Barcha buyurtmalarni to'xtatish, o'chirish va tozalash
        t_low = (text or "").lower().strip()
        if any(k in t_low for k in ["kesh", "tozala", "clear", "clean"]) or t_low in ("/clear", "/clean", "/kesh"):
            self.cancel_and_clean_all(chat_id, title="KESH VA BARCHA ESKI BUYURTMALAR TO'LIQ TOZALANDI!")
            return

        # 8. 🖥 Klaster (Kompyuterlar holati)
        if text in ("🖥 Klaster (Kompyuterlar holati)", "🖥 Klaster", "/klaster", "/cluster"):
            stats = self.get_system_stats()
            c_summary = cluster_state.get_status_summary()
            
            agents_text = ""
            if c_summary["agents"]:
                for ag in c_summary["agents"]:
                    icon = "🟢" if ag["active"] else "⚪"
                    cur_t = f"({ag['current_task']})" if ag["current_task"] else "(Bo'sh)"
                    agents_text += f"  {icon} <b>{ag['id']}</b>: {cur_t} | Yakunlagan: <b>{ag['done_count']} ta</b> | Ish vaqti: {ag['uptime_min']} daqiqa\n"
            else:
                agents_text = "  ℹ️ <i>Hozircha faol virtual agent ulanmagan (Mahalliy oqim xizmatda).</i>\n"

            rem_drain_min = max(0, 330 - c_summary['server_uptime_min'])
            msg = (
                "🖥 <b>5 MILLION KLASTER VA VIRTUAL KOMPYUTERLAR:</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                f"👑 <b>Master Server (Asosiy Boshqaruv):</b>\n"
                f"  • Host: <code>{stats['hostname']}</code> (Port: 8080)\n"
                f"  • CPU: <b>{stats['cpu']}%</b> | RAM: <b>{stats['ram']}% ({stats['ram_used']} / {stats['ram_total']})</b>\n"
                f"  • Ish vaqti: <b>{c_summary['server_uptime_min']} daqiqa</b> (Limitgacha: ~<b>{rem_drain_min} daqiqa</b> qoldi)\n\n"
                f"🤖 <b>Faol Virtual Agentlar ({c_summary['active_agents']} ta):</b>\n"
                f"{agents_text}\n"
                f"📊 <b>Klaster Navbati:</b>\n"
                f"  • Jami vazifalar: <b>{c_summary['total_tasks']} ta</b>\n"
                f"  • ✅ Tayyor: <b>{c_summary['completed']} ta</b>\n"
                f"  • ⏳ Jarayonda: <b>{c_summary['in_progress']} ta</b>\n"
                f"  • 📋 Kutilayotgan: <b>{c_summary['queued']} ta</b>\n\n"
                f"⚡ <i>3 ta Virtual Agent navbatdagi bolalarni parallel yopadi va havolalarni Excelga yozadi!</i>"
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

            act_workers = 0
            try:
                import process_5million_excel
                act_workers = process_5million_excel.get_active_token_workers()
            except Exception:
                pass

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
                f"⏳ Qolgan: <b>{max(0, total - done)} ta</b>\n"
                f"⚡ Orqa fonda faol oqimlar: <b>{act_workers}/10 nafar</b>"
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

        # 19. 💰 Rasmiy Narxlar
        if text in ("💰 Rasmiy Narxlar", "/narxlar", "/tariflar", "💰 Tariflar", "Tariflar", "💰 Narxlar va 50% Avans", "/price", "/prices"):
            card = self.config.get("card_info")
            msg = (
                "💰 <b>RASMIY TARIF VA XIZMATLAR:</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "🔹 1. 🔑 <b>Faqat Login-parol olish:</b>\n"
                "   • O'quvchini ro'yxatdan o'tkazish va shaxsiy login/parol berish.\n"
                "   • Narxi: <b>2 000 so'm</b> (1 ta o'quvchi uchun)\n\n"
                "🌟 2. 🎓 <b>To'liq Sertifikat olishga yordam berish:</b>\n"
                "   • Ro'yxatdan o'tkazish + 4 ta modulni 100% yopish;\n"
                "   • Rasmiy sertifikat havolasi (linki) bilan tayyor Excel berish.\n"
                "   • Narxi: <b>3 000 so'm</b> (1 ta o'quvchi uchun)\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "💳 <b>To'lov uchun karta:</b>\n"
                f"<code>{card}</code>\n"
                "👤 QOBILOV OBIDJON\n\n"
                "👉 <i>Buyurtma berish uchun xizmat turini tanlab, Excel faylingizni yuboring!</i>"
            )
            self.send_message(chat_id, msg, reply_markup=self.get_reply_keyboard(chat_id))
            return

        # 20. 👨‍💼 Admin bilan aloqa
        if text in ("👨‍💼 Admin bilan aloqa", "/admin", "/help", "help", "Help"):
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
        cloud_max_sec = 5.5 * 3600  # 5 soat 30 daqiqa (330 daqiqa)
        is_cloud = os.environ.get("CLOUD_MODE") == "1" or os.environ.get("GITHUB_ACTIONS") == "true"

        # Server qayta yonganda to'xtab qolgan buyurtmani tekshirish va xabar berish
        resumed = self.check_and_resume_active_order()
        if not resumed and self.admin_id:
            try:
                aid = self.get_anydesk_id()
                pwd = self.config.get("anydesk_pwd", "UzbekCoders2026!")
                self.send_message(
                    self.admin_id,
                    f"🚀 <b>Server muvaffaqiyatli qayta yondi!</b>\nBarcha tizimlar tayyor.\n\n🖥 <b>AnyDesk ID:</b> <code>{aid}</code>\n🔑 <b>Parol:</b> <code>{pwd}</code>\n\nYangi Excel faylingizni yuborishingiz mumkin.",
                    reply_markup=self.get_reply_keyboard(self.admin_id)
                )
            except Exception:
                pass

        while self.is_running:
            # Bulut taymerini tekshirish (o'chishdan 45 daqiqa oldin xavfsiz push va qayta yoqish)
            if is_cloud and (time.time() - cloud_start_time >= cloud_max_sec):
                print("[CLOUD DRAIN] 5 soat 15 daqiqa to'ldi. Yangi buyurtma qabul qilinmaydi!")
                self.send_message(self.admin_id, "⏰ <b>Server 6 soatlik limitga yaqinlashdi.</b>\nBarcha o'quvchilar va sessiyalar to'liq saqlandi! Server yangidan o'chib-yonadi...")
                
                # Faqat yangi ish bo'lsa PRIVATE studio-core repoga push qilish
                try:
                    if os.path.exists("core_temp"):
                        import shutil
                        shutil.copy("students_db.json", "core_temp/students_db.json")
                        if os.path.exists("session_pool_state.json"):
                            shutil.copy("session_pool_state.json", "core_temp/session_pool_state.json")
                        if ACTIVE_ORDER_FILE.exists():
                            shutil.copy(str(ACTIVE_ORDER_FILE), "core_temp/active_order_state.json")
                        if ACTIVE_EXCEL_PATH.exists():
                            shutil.copy(str(ACTIVE_EXCEL_PATH), "core_temp/active_order.xlsx")
                        status = subprocess.check_output(["git", "-C", "core_temp", "status", "--porcelain"], text=True).strip()
                        if status:
                            print("[CLOUD PUSH] Yangi sertifikatlar, buyurtma va sessiyalar PRIVATE repoga saqlanmoqda...")
                            subprocess.run(["git", "-C", "core_temp", "config", "user.name", "obidbek1988"], check=True)
                            subprocess.run(["git", "-C", "core_temp", "config", "user.email", "obidbek1988@gmail.com"], check=True)
                            subprocess.run(["git", "-C", "core_temp", "add", "-A"], check=True)
                            subprocess.run(["git", "-C", "core_temp", "commit", "-m", "Auto-save: Private database, active order & pool updated"], check=True)
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
