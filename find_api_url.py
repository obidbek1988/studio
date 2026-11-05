import re

with open("5millionsertifikat/main.js", "r", encoding="utf-8") as f:
    text = f.read()

pos = text.find("API_BASE_URL")
while pos != -1:
    print(text[max(0, pos-100):pos+250])
    pos = text.find("API_BASE_URL", pos+1)
