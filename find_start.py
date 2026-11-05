import sys, re
sys.stdout.reconfigure(encoding="utf-8")

with open(r"d:\uzbekcodersbot\telegram_bot.py", "r", encoding="utf-8", errors="ignore") as f:
    text = f.read()

pos = text.find("/start")
while pos != -1:
    print(f"--- MATCH AT {pos} ---")
    print(text[max(0, pos-100):min(len(text), pos+300)])
    pos = text.find("/start", pos + 6)
