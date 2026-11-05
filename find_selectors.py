with open(r'd:\uzbekcodersbot\5millionsertifikat\lesson-component.js', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

import re
selectors = re.findall(r'selectors:\s*\[\[([\"\'a-zA-Z0-9_\-]+)\]\]', text)
print("Selectors in lesson-component.js:", selectors)
