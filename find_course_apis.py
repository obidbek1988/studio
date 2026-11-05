with open("5millionsertifikat/chunk-2L4VB2S5.js", "r", encoding="utf-8") as f:
    text = f.read()

import re
print("Strings in course chunk:")
for s in re.findall(r'["\']([a-zA-Z0-9_\-\./:]+)["\']', text):
    if any(k in s.lower() for k in ["api", "module", "lesson", "quiz", "test", "course", "cert", "user"]):
        print(" -", s)
