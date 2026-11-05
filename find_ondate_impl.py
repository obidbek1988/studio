with open("5millionsertifikat/chunk-register.js", "r", encoding="utf-8") as f:
    text = f.read()

pos = text.find("onDateInput(t)")
if pos == -1:
    pos = text.find("onDateInput")
print(text[pos:pos+300])
