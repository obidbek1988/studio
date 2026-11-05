with open("5millionsertifikat/chunk-register.js", "r", encoding="utf-8") as f:
    text = f.read()

pos = text.find("onDateInput")
print("onDateInput snippet:")
print(text[pos:pos+400])
