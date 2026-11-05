with open("5millionsertifikat/chunk-register.js", "r", encoding="utf-8") as f:
    text = f.read()

pos = text.find("fetchPersonDataFromGCP")
if pos != -1:
    print("Full flow around fetchPersonDataFromGCP:")
    print(text[pos:pos+1500])
