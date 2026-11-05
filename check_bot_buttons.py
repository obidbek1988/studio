import re

with open(r"d:\uzbekcodersbot\bot.py", "r", encoding="utf-8", errors="ignore") as f:
    text = f.read()

buttons = re.findall(r"KeyboardButton\(['\"](.*?)['\"]\)", text)
print("Reply Keyboard Buttons:", set(buttons))

inline = re.findall(r"InlineKeyboardButton\(['\"](.*?)['\"]", text)
print("Inline Buttons:", set(inline))
