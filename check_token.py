with open(r"d:\uzbekcodersbot\telegram_bot.py", "r", encoding="utf-8", errors="ignore") as f:
    text = f.read()

import re
m = re.search(r'BOT_TOKEN\s*=\s*[\'"](.*?)[\'"]', text)
print("BOT_TOKEN in telegram_bot.py:", m.group(1) if m else "Not found")
