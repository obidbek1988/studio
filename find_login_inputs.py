with open("5millionsertifikat/login-component.js", "r", encoding="utf-8") as f:
    text = f.read()

import re
inputs = re.findall(r'<input[^>]*>', text)
print("Inputs in login template:")
for inp in inputs:
    print(" -", inp)

# Also check formControlName
fcns = re.findall(r'formControlName["\']?\s*[:=]\s*["\']?([^"\'\s>]+)', text)
print("formControlNames:", fcns)

# Search for placeholder or labels
print("Template snippets around input:")
for m in re.finditer(r'input', text):
    pos = m.start()
    print(" ->", text[max(0, pos-50):pos+100])
    if m.start() > 5000:
        break
