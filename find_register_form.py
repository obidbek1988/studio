with open("5millionsertifikat/chunk-register.js", "r", encoding="utf-8") as f:
    text = f.read()

pos = text.find("registerForm=")
if pos == -1:
    pos = text.find("registerForm =")
if pos == -1:
    pos = text.find("this.registerForm")
print("registerForm context:", text[max(0, pos-200):pos+600])
