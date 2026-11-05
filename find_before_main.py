with open(r"d:\uzbekcodersbot\telegram_bot.py", "r", encoding="utf-8", errors="ignore") as f:
    text = f.read()

pos = text.find('if __name__ == "__main__":')
print("Before __main__:")
print(text[pos-600:pos])
