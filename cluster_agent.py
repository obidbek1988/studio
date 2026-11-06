# -*- coding: utf-8 -*-
"""
5 MILLION VIRTUAL AGENT (Ishchi Agent)
Virtual kompyuterda ishlaydigan agent dasturi.

Xususiyatlari:
1. Master Serverdan navbatdagi 1 ta bolani oladi.
2. Saytga login qiladi, 4 ta modulni 100% yopadi (har bir darsda galichka ✔ tekshiriladi).
3. O'quvchining rasmiy sertifikat havolasini oladi va Masterga topshiradi.
4. Har 30 soniyada Masterga tiriklik xabari (Heartbeat) yuboradi.
5. 5 soat 30 daqiqa (limitga 30 daqiqa qolganda):
   - Yangi bola olmaydi;
   - Qo'lidagi bolani xotirjam bitiradi;
   - Toza limit bilan yangidan ishga tushish uchun chiqadi (Graceful Restart).
"""

import os
import sys
import time
import requests
import json
import threading
from playwright.sync_api import sync_playwright

MASTER_URL = os.environ.get("MASTER_URL", "http://127.0.0.1:8080").rstrip("/")
AGENT_ID = os.environ.get("AGENT_ID", f"agent_{os.environ.get('COMPUTERNAME', 'cloud_vm')}")
DRAIN_TIME_SEC = 5.5 * 3600 # 5 soat 30 daqiqa

# Asosiy dvigateldan funksiyalarni yuklash
try:
    from process_5million_excel import (
        perform_safe_login,
        complete_course,
        handle_recaptcha,
        switch_to_login_tab
    )
except ImportError:
    print("[ERROR] 'process_5million_excel.py' topilmadi! Asosiy modul kerak.")
    sys.exit(1)

def heartbeat_worker(agent_id, stop_event):
    while not stop_event.is_set():
        try:
            requests.post(f"{MASTER_URL}/task/heartbeat", json={"agent_id": agent_id}, timeout=5)
        except Exception:
            pass
        time.sleep(30)

def solve_student_task(task):
    """Bitta o'quvchini saytda to'liq yopish va sertifikat havolasini olish"""
    name = task.get("name", "Noma'lum")
    login = task.get("login")
    password = task.get("password")
    seria = task.get("seria")
    number = task.get("number")

    print(f"\n==================================================")
    print(f"🚀 [{AGENT_ID}] BOSHLANDI: {name} ({seria} {number})")
    print(f"🔑 Login: {login}")
    print(f"==================================================")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            channel="chrome",
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-popup-blocking"
            ]
        )
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            locale="en-US",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        context.add_init_script("""
            window._sys_dt_bypass = true;
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            window.navigator.chrome = { runtime: {} };
            Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en', 'uz'] });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
            const style = document.createElement('style');
            style.innerHTML = '.telegram-popup-overlay, .devtools-overlay, .p-dialog-mask { display: none !important; pointer-events: none !important; }';
            if (document.head) {
                document.head.appendChild(style);
            } else {
                document.addEventListener('DOMContentLoaded', () => document.head.appendChild(style));
            }
        """)
        context.route("**/chunk-4VTC4MLB.js", lambda route: route.abort())
        page = context.new_page()

        # 1-BOSQICH: Tizimga kirish
        token = perform_safe_login(page, login, password, name=name)
        if not token:
            browser.close()
            print(f"❌ [{AGENT_ID}] {name} tizimga kirib bo'lmadi!")
            return False, None

        print(f"✅ [{AGENT_ID}] {name} tizimga muvaffaqiyatli kirdi! Darslar boshlanmoqda...")

        # 2-BOSQICH: 4 ta modulni yopish
        for c_id in range(1, 5):
            ok = complete_course(page, c_id)
            if not ok:
                print(f"⚠️ [{AGENT_ID}] Modul {c_id} to'liq yopilmadi, qayta tekshirilmoqda...")
                complete_course(page, c_id)
            time.sleep(1)

        # 3-BOSQICH: Sertifikat havolasini olish
        cert_link = None
        for attempt in range(1, 6):
            try:
                cert_res = page.evaluate("""async () => {
                    const token = localStorage.getItem('accessToken');
                    const r = await fetch('https://api.aistudy.uz/api/StudyAILms/Certificate/GetCertificateByUser', {
                        headers: { 'Authorization': 'Bearer ' + token }
                    });
                    return await r.json();
                }""")
                cid = cert_res.get("result", {}).get("id") or cert_res.get("result", {}).get("certificateId")
                if cid:
                    cert_link = f"https://omp.aistudy.uz/certificate?id={cid}"
                    break
            except Exception as e_c:
                print(f"[CERT GET ERROR] {e_c}")
            time.sleep(2)

        browser.close()

        if cert_link:
            print(f"🎉 [{AGENT_ID}] SERTIFIKAT TAYYOR! {name} -> {cert_link}")
            return True, cert_link
        else:
            print(f"⚠️ [{AGENT_ID}] {name} barcha darslar yopildi, lekin sertifikat havolasi olinmadi.")
            return False, None

def main():
    print(f"============================================================")
    print(f"🤖 5 MILLION VIRTUAL AGENT ISHGA TUSHMOQDA...")
    print(f"🆔 Agent ID: {AGENT_ID}")
    print(f"🌐 Master Server: {MASTER_URL}")
    print(f"⏱ Limit: 5 soat 30 daqiqada toza qayta yoqilish (Graceful Drain)")
    print(f"============================================================")

    start_time = time.time()
    stop_event = threading.Event()
    hb_thread = threading.Thread(target=heartbeat_worker, args=(AGENT_ID, stop_event), daemon=True)
    hb_thread.start()

    while True:
        elapsed = time.time() - start_time
        # 5 soat 30 daqiqa qoidasi
        if elapsed >= DRAIN_TIME_SEC:
            print(f"\n[AGENT DRAIN] 5 soat 30 daqiqa ishladi ({int(elapsed/60)} daqiqa).")
            print(f"[AGENT DRAIN] Yangi vazifalar to'xtatildi. Virtual kompyuter limitni yangilash uchun chiqmoqda...")
            stop_event.set()
            sys.exit(0)

        # Masterdan navbatdagi bolani so'rash
        try:
            resp = requests.get(f"{MASTER_URL}/task/next?agent_id={AGENT_ID}", timeout=10)
            data = resp.json()
        except Exception as e:
            print(f"[CONNECT ERROR] Master serverga ulanib bo'lmadi ({e}). 5 soniyadan so'ng qayta uriniladi...")
            time.sleep(5)
            continue

        status = data.get("status")
        if status == "DRAIN":
            print(f"[DRAIN NOTIFIED] Master server limit yaqinlashganini bildirdi. Virtual kompyuter yangilanmoqda...")
            stop_event.set()
            sys.exit(0)
        elif status == "EMPTY":
            time.sleep(3)
            continue
        elif status == "OK":
            task = data.get("task")
            if not task:
                time.sleep(3)
                continue

            task_id = task["id"]
            ok, cert_link = solve_student_task(task)

            if ok and cert_link:
                # Masterga topshirish
                try:
                    res_done = requests.post(f"{MASTER_URL}/task/done", json={
                        "agent_id": AGENT_ID,
                        "task_id": task_id,
                        "cert_link": cert_link
                    }, timeout=10)
                    print(f"[TASK SUBMITTED] Master tasdiqladi: {res_done.json().get('message')}")
                except Exception as e_done:
                    print(f"[SUBMIT ERROR] {e_done}")
            else:
                print(f"[TASK FAILED] {task.get('name')} muvaffaqiyatsiz bo'ldi. Master navbatga qaytaradi.")
                time.sleep(2)

if __name__ == "__main__":
    main()
