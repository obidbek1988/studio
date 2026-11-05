import re

with open(r"d:\uzbekcodersbot\telegram_bot.py", "r", encoding="utf-8", errors="ignore") as f:
    text = f.read()

funcs = re.findall(r"def (\w+)\(", text)
print("Total functions:", len(funcs))
print("Sample functions:", funcs[:20])

# Check how updates are received (getUpdates vs webhook)
if "getUpdates" in text:
    print("Uses getUpdates polling!")

# Search for main menu buttons / reply markup
menus = re.findall(r"keyboard.*?=.*?\[(.*?)\]", text, re.DOTALL)
print("Menus count:", len(menus))

# Find /start handler
start_pos = text.find("text == '/start'")
if start_pos == -1:
    start_pos = text.find("'/start'")
print("Start position:", start_pos)
if start_pos != -1:
    print("Around /start:")
    print(text[start_pos-100:start_pos+400])
