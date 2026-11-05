import requests
import re

for chunk in ["chunk-V3EZNMNH.js", "chunk-GAL4ENT6.js"]:
    r = requests.get("https://omp.aistudy.uz/" + chunk)
    print(chunk, r.status_code, len(r.text))
    with open("5millionsertifikat/" + chunk, "w", encoding="utf-8") as f:
        f.write(r.text)
    for m in re.finditer(r'fetchPersonDataFromGCP|siteKey|recaptcha|https?://[a-zA-Z0-9_\-\./]+', r.text):
        if "w3.org" not in m.group(0):
            print(f"[{chunk}] match:", m.group(0))
