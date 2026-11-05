import requests
import re

r = requests.get("https://omp.aistudy.uz/chunk-YMQMNBNH.js")
print("register chunk len:", len(r.text))
with open("5millionsertifikat/chunk-register.js", "w", encoding="utf-8") as f:
    f.write(r.text)

# Search for captcha and API endpoints
text = r.text
for kw in ["captcha", "recaptcha", "sitekey", "http", "api", "pasport", "metrika", "token"]:
    matches = [m.start() for m in re.finditer(kw, text, re.IGNORECASE)]
    print(f"Keyword '{kw}': {len(matches)}")
    for pos in matches[:5]:
        print(" ->", text[max(0, pos-80):pos+120])
