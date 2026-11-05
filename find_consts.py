with open("5millionsertifikat/login-component.js", "r", encoding="utf-8") as f:
    text = f.read()

pos = text.find('consts:')
if pos == -1:
    pos = text.find('consts')
print("consts in login component:")
print(text[pos:pos+1500])
