with open(r"d:\uzbekcodersbot\telegram_bot.py", "r", encoding="utf-8", errors="ignore") as f:
    text = f.read()

pos = text.find('self.handle_smart_question(chat_id, user_name, text)')
# Find the def before this
prev_def = text.rfind('def ', 0, pos)
print("Enclosing method:", text[prev_def:prev_def+100])
