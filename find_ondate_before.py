with open("5millionsertifikat/chunk-register.js", "r", encoding="utf-8") as f:
    text = f.read()

pos = text.find("onDateInput")
print(text[pos-400:pos])
