import sys, re
sys.stdout.reconfigure(encoding="utf-8")

with open(r"d:\uzbekcodersbot\telegram_bot.py", "r", encoding="utf-8", errors="ignore") as f:
    text = f.read()

pos = text.find("def get_reply_keyboard")
if pos != -1:
    print(text[pos:pos+1500])
