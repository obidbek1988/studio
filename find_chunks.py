import re

with open("5millionsertifikat/main.js", "r", encoding="utf-8") as f:
    text = f.read()

# Look for chunk paths or loadComponent
chunks = re.findall(r'["\']([a-zA-Z0-9_\-]+\.js)["\']', text)
print("Referenced JS files in main.js:")
for c in set(chunks):
    print(" -", c)

# Look for router paths
routes = re.findall(r'path:\s*["\']([^"\']+)["\']', text)
print("Routes:", routes)
