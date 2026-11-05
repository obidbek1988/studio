with open("5millionsertifikat/chunk-register.js", "r", encoding="utf-8") as f:
    text = f.read()

import re
imports = re.findall(r'import\s*\{([^}]+)\}\s*from\s*["\']([^"\']+)["\']', text)
for names, path in imports:
    if "Te" in names or "fetch" in names:
        print("Import:", names, "from", path)

# Look for Te definition if it's in the same file
pos = text.find("Te=")
if pos != -1:
    print("Te= found at", pos, text[pos:pos+300])

# Check all imports in chunk-register.js
print("All imports in register chunk:")
for names, path in imports:
    print(" -> from", path, ":", names[:80])
