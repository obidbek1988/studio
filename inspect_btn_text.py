import sys
sys.stdout.reconfigure(encoding="utf-8")

with open(r"d:\uzbekcodersbot\telegram_bot.py", "r", encoding="utf-8", errors="ignore") as f:
    text = f.read()

pos = text.find('🎓 5 Million Prompter (Besh Million)')
print(text[pos-100:pos+800])
