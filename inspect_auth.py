with open(r'd:\uzbekcodersbot\5millionsertifikat\chunk-auth-service.js', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

idx = text.find('accessToken')
while idx != -1:
    print(text[max(0, idx-50):min(len(text), idx+150)])
    idx = text.find('accessToken', idx + 1)
