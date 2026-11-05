with open("5millionsertifikat/main.js", "r", encoding="utf-8") as f:
    text = f.read()

import re
matches = [m.start() for m in re.finditer(r'devtools|Dasturchi\s+asboblari|debugger', text, re.IGNORECASE)]
for pos in matches:
    print("--- MATCH AT", pos, "---")
    print(text[max(0, pos-200):pos+400])
