import requests
import re

r = requests.get("https://omp.aistudy.uz/chunk-HA5DQJKH.js")
print("chunk-HA5DQJKH len:", len(r.text))
with open("5millionsertifikat/chunk-base-api.js", "w", encoding="utf-8") as f:
    f.write(r.text)

print(r.text[:1500])
