import requests
import re

r = requests.get("https://omp.aistudy.uz/chunk-7YXVMTRO.js")
print("chunk-7YXVMTRO len:", len(r.text))
with open("5millionsertifikat/certificate-component.js", "w", encoding="utf-8") as f:
    f.write(r.text)

for m in re.finditer(r'["\']([a-zA-Z0-9_\-/]+Certificate[a-zA-Z0-9_\-/]*)["\']', r.text, re.IGNORECASE):
    print("Certificate API:", m.group(0))
