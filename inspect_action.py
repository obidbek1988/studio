import sys
sys.stdout.reconfigure(encoding="utf-8")

with open(r"d:\uzbekcodersbot\telegram_bot.py", "r", encoding="utf-8", errors="ignore") as f:
    text = f.read()

pos = text.find('admin_input_state[chat_id] = {"action": "5million_order"}')
print(text[pos-200:pos+800])
