with open("5millionsertifikat/certificate-component.js", "r", encoding="utf-8") as f:
    text = f.read()

import re
print("APIs in cert component:")
for s in re.findall(r'["\']([a-zA-Z0-9_\-\./:]+)["\']', text):
    if any(k in s.lower() for k in ["cert", "api", "pdf", "user"]):
        print(" -", s)
