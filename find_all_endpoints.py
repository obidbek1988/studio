import os
import re

for f in os.listdir(r'd:\uzbekcodersbot\5millionsertifikat'):
    if f.endswith('.js'):
        p = os.path.join(r'd:\uzbekcodersbot\5millionsertifikat', f)
        with open(p, 'r', encoding='utf-8', errors='ignore') as fp:
            text = fp.read()
            m = re.findall(r'[\'"]([A-Z][A-Za-z0-9_]+/[A-Z][A-Za-z0-9_]+)[\'"]', text)
            if m:
                print(f"File {f}:", set(m))
