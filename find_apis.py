import re

with open(r'd:\uzbekcodersbot\5millionsertifikat\lesson-component.js', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

apis = re.findall(r'[\'"]([A-Za-z0-9_]+/[A-Za-z0-9_]+)[\'"]', text)
print("Unique APIs in lesson-component:")
for a in sorted(set(apis)):
    print(" -", a)
