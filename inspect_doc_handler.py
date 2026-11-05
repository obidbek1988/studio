import sys
sys.stdout.reconfigure(encoding="utf-8")

with open(r"d:\uzbekcodersbot\telegram_bot.py", "r", encoding="utf-8", errors="ignore") as f:
    text = f.read()

pos = 173309
print(text[pos:pos+2500])
