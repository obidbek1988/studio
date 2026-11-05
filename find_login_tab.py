with open("5millionsertifikat/login-component.js", "r", encoding="utf-8") as f:
    text = f.read()

import re
pos = text.find("Login - Parol")
if pos == -1:
    pos = text.find("Login")
print("Login tab snippet:")
print(text[max(0, pos-100):pos+400])

# Search for tab or active
for m in re.finditer(r'["\']([^"\']*(?:OneID|Login\s*-\s*Parol|tab|active)[^"\']*)["\']', text):
    if len(m.group(1)) < 50:
        print("Tab string:", m.group(1))
