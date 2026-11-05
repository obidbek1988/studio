import re

with open("5millionsertifikat/main.js", "r", encoding="utf-8") as f:
    text = f.read()

idx = text.find("loginOrRegister")
if idx != -1:
    print("Found loginOrRegister at:", idx)
    print(text[max(0, idx-500):idx+1000])

# Also search for sitekey or grecaptcha
for kw in ["grecaptcha", "sitekey", "6L", "Enterprise", "captcha"]:
    matches = [m.start() for m in re.finditer(kw, text, re.IGNORECASE)]
    print(f"Keyword '{kw}': found {len(matches)} times")
    for pos in matches[:3]:
        print("  Context:", text[max(0, pos-100):pos+150])
