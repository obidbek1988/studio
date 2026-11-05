import re

with open(r"d:\uzbekcodersbot\telegram_bot.py", "r", encoding="utf-8", errors="ignore") as f:
    text = f.read()

matches = re.findall(r"def handle_\w+\(.*?\):", text)
print("Handlers found:", matches)
