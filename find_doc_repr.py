with open(r"d:\uzbekcodersbot\telegram_bot.py", "r", encoding="utf-8", errors="ignore") as f:
    text = f.read()

pos = text.find('if "document" in msg:')
print(repr(text[pos:pos+400]))
