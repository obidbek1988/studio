with open(r'd:\uzbekcodersbot\5millionsertifikat\lesson-component.js', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

idx = text.find('setupPlayerEvents()')
print("=== setupPlayerEvents ===")
print(text[idx:idx+2500])
