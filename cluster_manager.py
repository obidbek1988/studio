# -*- coding: utf-8 -*-
"""
5 MILLION CLUSTER MANAGER (Master Server)
1 ta Asosiy Boshqaruvchi Server va 3 ta Virtual Agentni boshqarish moduli.

Vazifalari:
1. Buyurtmadagi o'quvchilarni ro'yxatga olib, navbatga (cluster_queue) joylash.
2. 3 ta Virtual Agentga vazifalarni 1 tadan adolatli taqsimlash.
3. Har bir agentning 5 soat 30 daqiqalik ish vaqtini nazorat qilish (Graceful Restart).
4. Qotib qolgan (3 daqiqadan oshgan) agentlardan vazifani qaytarib olib, sog'lom agentga berish.
5. O'quvchi yakunlangach, uning I-FR metrikasiga bog'langan rasmiy sertifikat havolasini Excelga yozish.
6. Butun buyurtma bitgandagina yoki server yangilangandagina 1 marta xavfsiz Git Push qilish.
"""

import os
import sys
import time
import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import openpyxl

QUEUE_FILE = "cluster_queue.json"
MAX_AGENT_LEASE_SEC = 240       # Agent 4 daqiqada topshirmasa, vazifa navbatga qaytadi
DRAIN_TIME_SEC = 5.5 * 3600     # 5 soat 30 daqiqa (Limitga 30 daqiqa qolganda yangi vazifa berilmaydi)

class ClusterState:
    def __init__(self):
        self.lock = threading.Lock()
        self.tasks = []         # [{'id', 'order_id', 'seria', 'number', 'name', 'login', 'password', 'status', 'assigned_to', 'assigned_at', 'cert_link'}]
        self.agents = {}        # {agent_id: {'last_seen': ts, 'current_task': id, 'completed_count': n, 'started_at': ts}}
        self.orders = {}        # {order_id: {'excel_path': str, 'total': n, 'done': n, 'chat_id': id, 'created_at': ts}}
        self.server_start_time = time.time()
        self.is_draining = False
        self.load_state()

    def load_state(self):
        if os.path.exists(QUEUE_FILE):
            try:
                with open(QUEUE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.tasks = data.get("tasks", [])
                    self.orders = data.get("orders", {})
                print(f"[CLUSTER] Baza yuklandi: {len(self.tasks)} ta vazifa mavjud.")
            except Exception as e:
                print(f"[CLUSTER LOAD ERROR] {e}")

    def save_state(self):
        try:
            with open(QUEUE_FILE, "w", encoding="utf-8") as f:
                json.dump({
                    "tasks": self.tasks,
                    "orders": self.orders,
                    "updated_at": time.strftime("%Y-%m-%d %H:%M:%S")
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[CLUSTER SAVE ERROR] {e}")

    def add_order(self, order_id, students, excel_path, chat_id=None):
        with self.lock:
            self.orders[order_id] = {
                "excel_path": excel_path,
                "total": len(students),
                "done": 0,
                "chat_id": chat_id,
                "created_at": time.time(),
                "completed": False
            }
            for idx, st in enumerate(students):
                task_id = f"{order_id}_{st.get('seria')}_{st.get('number')}"
                # Agar oldin kiritilmagan bo'lsa
                if not any(t["id"] == task_id for t in self.tasks):
                    self.tasks.append({
                        "id": task_id,
                        "order_id": order_id,
                        "seria": st.get("seria"),
                        "number": st.get("number"),
                        "name": st.get("name"),
                        "login": st.get("login"),
                        "password": st.get("password"),
                        "status": "QUEUED" if st.get("login") else "NEED_REGISTRATION",
                        "assigned_to": None,
                        "assigned_at": 0,
                        "cert_link": None,
                        "updated_at": time.time()
                    })
            self.save_state()
            print(f"[CLUSTER] Yangi buyurtma navbatga qo'shildi: {order_id} ({len(students)} ta bola)")

    def get_next_task(self, agent_id):
        now = time.time()
        with self.lock:
            # Agentni ro'yxatga olish / yangilash
            if agent_id not in self.agents:
                self.agents[agent_id] = {
                    "last_seen": now,
                    "current_task": None,
                    "completed_count": 0,
                    "started_at": now
                }
            else:
                self.agents[agent_id]["last_seen"] = now

            # 5 soat 30 daqiqa qoidasi: Agar agent ishlash vaqti limitga 30 daqiqa qolgan bo'lsa, yangi vazifa bermaymiz!
            agent_elapsed = now - self.agents[agent_id].get("started_at", now)
            if agent_elapsed >= DRAIN_TIME_SEC or self.is_draining:
                print(f"[CLUSTER DRAIN] Agent {agent_id} limitga 30 daqiqa qoldi ({int(agent_elapsed/60)} daqiqa ishladi). Yangi vazifa to'xtatildi!")
                return {"status": "DRAIN", "message": "Limitga 30 daqiqa qoldi. Toza qayta yoqilishga o'ting."}

            # Agar agent allaqachon bitta vazifani olayotgan bo'lsa, o'shani qaytaramiz (qayta berish)
            cur_task_id = self.agents[agent_id].get("current_task")
            if cur_task_id:
                for t in self.tasks:
                    if t["id"] == cur_task_id and t["status"] == "IN_PROGRESS":
                        return {"status": "OK", "task": t}

            # Navbatdagi faol vazifani qidiramiz
            for t in self.tasks:
                if t["status"] == "QUEUED" and t.get("login") and t.get("password"):
                    t["status"] = "IN_PROGRESS"
                    t["assigned_to"] = agent_id
                    t["assigned_at"] = now
                    t["updated_at"] = now
                    self.agents[agent_id]["current_task"] = t["id"]
                    self.save_state()
                    print(f"[CLUSTER DISPATCH] {t['name']} ({t['seria']} {t['number']}) -> {agent_id} ga biriktirildi.")
                    return {"status": "OK", "task": t}

            return {"status": "EMPTY", "message": "Hozircha navbatda bo'sh vazifa yo'q"}

    def complete_task(self, agent_id, task_id, cert_link):
        now = time.time()
        with self.lock:
            if agent_id in self.agents:
                self.agents[agent_id]["last_seen"] = now
                self.agents[agent_id]["current_task"] = None
                self.agents[agent_id]["completed_count"] += 1

            for t in self.tasks:
                if t["id"] == task_id:
                    t["status"] = "COMPLETED"
                    t["cert_link"] = cert_link
                    t["completed_at"] = now
                    t["updated_at"] = now
                    print(f"[CLUSTER DONE] {t['name']} yakunlandi! Havola: {cert_link}")

                    # Excel faylga havolani yozish
                    order_id = t["order_id"]
                    if order_id in self.orders:
                        self.orders[order_id]["done"] += 1
                        self._write_cert_to_excel(self.orders[order_id]["excel_path"], t["seria"], t["number"], cert_link)

                        # Agar barcha bolalar tugagan bo'lsa
                        if self.orders[order_id]["done"] >= self.orders[order_id]["total"]:
                            self.orders[order_id]["completed"] = True
                            print(f"[CLUSTER ORDER COMPLETE] Buyurtma {order_id} to'liq 100% yakunlandi!")
                    break
            self.save_state()
            return {"status": "OK", "message": "Vazifa muvaffaqiyatli qabul qilindi"}

    def _write_cert_to_excel(self, excel_path, seria, number, cert_link):
        """Excel faylga o'quvchining I-FR metrikasi to'g'risiga sertifikat havolasini yozish"""
        if not excel_path or not os.path.exists(excel_path):
            return
        try:
            wb = openpyxl.load_workbook(excel_path)
            ws = wb.active
            clean_num = str(number).strip().lstrip('0')

            # Ustunlarni aniqlash
            cert_col = None
            for col in range(1, ws.max_column + 2):
                h = str(ws.cell(row=1, column=col).value or "").lower()
                if "sertifikat" in h or "havola" in h or "link" in h:
                    cert_col = col
                    break
            if not cert_col:
                cert_col = ws.max_column + 1
                ws.cell(row=1, column=cert_col, value="Sertifikat Havolasi")

            # Qatorni topib yozish
            for r in range(2, ws.max_row + 1):
                row_vals = [str(ws.cell(row=r, column=c).value or "").strip() for c in range(1, ws.max_column + 1)]
                row_text = " ".join(row_vals).lower()
                if seria.lower() in row_text and (clean_num in row_text or str(number) in row_text):
                    cell = ws.cell(row=r, column=cert_col, value=cert_link)
                    cell.hyperlink = cert_link
                    break
            wb.save(excel_path)
            print(f"[EXCEL UPDATED] {seria} {number} havolasi Excelga saqlandi.")
        except Exception as e:
            print(f"[EXCEL WRITE ERROR] {e}")

    def watchdog_check(self):
        """Qotib qolgan (4 daqiqa javob bermagan) agentlardan vazifani qaytarib olish"""
        now = time.time()
        with self.lock:
            for t in self.tasks:
                if t["status"] == "IN_PROGRESS":
                    elapsed = now - t.get("assigned_at", now)
                    if elapsed > MAX_AGENT_LEASE_SEC:
                        ag = t.get("assigned_to", "Unknown")
                        print(f"[WATCHDOG TIMEOUT] {t['name']} bo'yicha {ag} 4 daqiqada topshirmadi! Navbatga qaytarildi.")
                        t["status"] = "QUEUED"
                        t["assigned_to"] = None
                        t["assigned_at"] = 0
                        t["updated_at"] = now
                        if ag in self.agents:
                            self.agents[ag]["current_task"] = None
            self.save_state()

    def get_status_summary(self):
        now = time.time()
        with self.lock:
            total_tasks = len(self.tasks)
            completed_tasks = sum(1 for t in self.tasks if t["status"] == "COMPLETED")
            in_progress_tasks = sum(1 for t in self.tasks if t["status"] == "IN_PROGRESS")
            queued_tasks = sum(1 for t in self.tasks if t["status"] == "QUEUED")
            active_agents_count = sum(1 for a in self.agents.values() if now - a.get("last_seen", 0) < 120)

            agents_info = []
            for a_id, a_data in self.agents.items():
                is_active = (now - a_data.get("last_seen", 0)) < 120
                uptime_m = int((now - a_data.get("started_at", now)) / 60)
                cur_t = a_data.get("current_task")
                agents_info.append({
                    "id": a_id,
                    "active": is_active,
                    "uptime_min": uptime_m,
                    "current_task": cur_t,
                    "done_count": a_data.get("completed_count", 0)
                })

            return {
                "server_uptime_min": int((now - self.server_start_time) / 60),
                "total_tasks": total_tasks,
                "completed": completed_tasks,
                "in_progress": in_progress_tasks,
                "queued": queued_tasks,
                "active_agents": active_agents_count,
                "agents": agents_info
            }

cluster_state = ClusterState()

class ClusterHTTPHandler(BaseHTTPRequestHandler):
    def _send_json(self, data, code=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        if parsed.path == "/health":
            self._send_json({"status": "ok", "uptime_sec": int(time.time() - cluster_state.server_start_time)})
        elif parsed.path == "/task/next":
            agent_id = params.get("agent_id", ["agent_default"])[0]
            res = cluster_state.get_next_task(agent_id)
            self._send_json(res)
        elif parsed.path == "/status":
            self._send_json(cluster_state.get_status_summary())
        else:
            self._send_json({"error": "Not found"}, 404)

    def do_POST(self):
        parsed = urlparse(self.path)
        content_len = int(self.headers.get("Content-Length", 0))
        body_bytes = self.rfile.read(content_len) if content_len > 0 else b"{}"
        try:
            body = json.loads(body_bytes.decode("utf-8"))
        except Exception:
            body = {}

        if parsed.path == "/task/done":
            agent_id = body.get("agent_id", "agent_default")
            task_id = body.get("task_id")
            cert_link = body.get("cert_link")
            if not task_id or not cert_link:
                self._send_json({"error": "task_id va cert_link talab qilinadi"}, 400)
                return
            res = cluster_state.complete_task(agent_id, task_id, cert_link)
            self._send_json(res)
        elif parsed.path == "/task/heartbeat":
            agent_id = body.get("agent_id", "agent_default")
            with cluster_state.lock:
                if agent_id in cluster_state.agents:
                    cluster_state.agents[agent_id]["last_seen"] = time.time()
            self._send_json({"status": "ok"})
        else:
            self._send_json({"error": "Not found"}, 404)

    def log_message(self, format, *args):
        # Jim rejim (har bir HTTP so'rov konsolni to'ldirib tashlamasligi uchun)
        pass

def run_watchdog():
    while True:
        try:
            cluster_state.watchdog_check()
        except Exception as e:
            print(f"[WATCHDOG LOOP ERROR] {e}")
        time.sleep(15)

def start_cluster_server(port=8080):
    server = HTTPServer(("0.0.0.0", port), ClusterHTTPHandler)
    print(f"============================================================")
    print(f"🚀 5 MILLION CLUSTER MANAGER ISHGA TUSHDI! (Port: {port})")
    print(f"Boshqaruv: 1 ta Asosiy Server + 3 ta Virtual Agent")
    print(f"Limit qoidasi: 5 soat 30 daqiqada xavfsiz Drain & Restart")
    print(f"============================================================")
    
    t_wd = threading.Thread(target=run_watchdog, daemon=True)
    t_wd.start()

    t_srv = threading.Thread(target=server.serve_forever, daemon=True)
    t_srv.start()
    return server

if __name__ == "__main__":
    start_cluster_server(port=8080)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[CLUSTER] Server to'xtatildi.")
