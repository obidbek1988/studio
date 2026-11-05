with open("5millionsertifikat/main.js", "r", encoding="utf-8") as f:
    text = f.read()

import re
matches = re.findall(r'import\s*\{[^}]*Fe[^}]*\}\s*from\s*["\']([^"\']+)["\']', text)
print("Fe imported from:", matches)
if not matches:
    # maybe alias as Fe
    matches2 = re.findall(r'import\s*\{[^}]*\bas\s+Fe\b[^}]*\}\s*from\s*["\']([^"\']+)["\']', text)
    print("as Fe imported from:", matches2)
