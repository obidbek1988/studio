with open("5millionsertifikat/lesson-component.js", "r", encoding="utf-8") as f:
    text = f.read()

pos = text.find("CheckQuizAndSaveResult")
print("CheckQuizAndSaveResult snippet:")
print(text[max(0, pos-200):pos+600])
