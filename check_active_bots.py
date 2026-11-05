import psutil
import datetime

print("=== FAOL PYTHON JARAYONLARI ===")
for p in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time']):
    try:
        name = p.info['name'].lower()
        if 'python' in name:
            cmd = " ".join(p.info.get('cmdline') or [])
            ct = datetime.datetime.fromtimestamp(p.info['create_time']).strftime('%Y-%m-%d %H:%M:%S')
            print(f"PID: {p.info['pid']} | Ishga tushgan vaqti: {ct} | Buyruq: {cmd[:140]}")
    except Exception:
        pass
