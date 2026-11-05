with open(r"d:\uzbekcodersbot\telegram_bot.py", "r", encoding="utf-8", errors="ignore") as f:
    text = f.read()

pos = text.find('def process_update(self, upd):')
print(text[pos-200:pos+50])
