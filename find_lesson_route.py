with open("5millionsertifikat/main.js", "r", encoding="utf-8") as f:
    text = f.read()

pos = text.find(":module/module/:moduleId/lesson/:lesson/type/:type")
print(text[pos:pos+300])
