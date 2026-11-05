with open("5millionsertifikat/chunk-auth-service.js", "r", encoding="utf-8") as f:
    text = f.read()

import re
imports = re.findall(r'import\s*\{([^}]+)\}\s*from\s*["\']([^"\']+)["\']', text)
for names, path in imports:
    print("AuthService import:", names, "from", path)

pos = text.find("baseApiService")
if pos != -1:
    print(text[max(0, pos-100):pos+300])
