with open("5millionsertifikat/login-component.js", "r", encoding="utf-8") as f:
    text = f.read()

pos = text.find('const _c')
if pos == -1:
    pos = text.find('var _c')
if pos == -1:
    pos = text.find('const ')
print("Constants/attributes in login component:")
print(text[:2000])
