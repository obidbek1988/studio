with open("5millionsertifikat/chunk-register.js", "r", encoding="utf-8") as f:
    text = f.read()

import re
pos = text.find("checkUserForm")
while pos != -1:
    print("--- checkUserForm snippet ---")
    print(text[max(0, pos-100):pos+400])
    pos = text.find("checkUserForm", pos+1)
