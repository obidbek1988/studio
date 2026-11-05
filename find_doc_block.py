with open(r"d:\uzbekcodersbot\telegram_bot.py", "r", encoding="utf-8", errors="ignore") as f:
    text = f.read()

pos = text.find('if "document" in msg:')
print(text[pos-100:pos+800])
