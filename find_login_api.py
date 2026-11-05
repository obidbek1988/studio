with open("5millionsertifikat/chunk-auth-service.js", "r", encoding="utf-8") as f:
    text = f.read()

pos = text.find("login(")
if pos == -1:
    pos = text.find("login")
print("Login snippet:")
print(text[max(0, pos-100):pos+400])
