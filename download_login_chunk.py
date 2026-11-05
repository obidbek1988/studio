import requests
import re

r = requests.get("https://omp.aistudy.uz/chunk-U6IGTMOT.js")
print("login chunk len:", len(r.text))
with open("5millionsertifikat/login-component.js", "w", encoding="utf-8") as f:
    f.write(r.text)

pos = r.text.find("loginForm")
print(r.text[max(0, pos-100):pos+400])
