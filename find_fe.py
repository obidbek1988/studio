with open("5millionsertifikat/main.js", "r", encoding="utf-8") as f:
    text = f.read()

pos = text.find("Fe.baseUrl")
if pos != -1:
    print(text[max(0, pos-400):pos+400])

import re
pos2 = text.find("var Fe=")
if pos2 == -1:
    pos2 = text.find("Fe=")
print("Fe definition:", text[max(0, pos2-50):pos2+300])
