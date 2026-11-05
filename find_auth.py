import re

with open("5millionsertifikat/main.js", "r", encoding="utf-8") as f:
    text = f.read()

pos = text.find("auth")
while pos != -1:
    snippet = text[max(0, pos-50):pos+300]
    if "loadChildren" in snippet or "loadComponent" in snippet or "children" in snippet:
        print("Auth route snippet:\n", snippet)
    pos = text.find("auth", pos+1)
