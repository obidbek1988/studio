import requests
import re

base_url = "https://omp.aistudy.uz/"
main_js_url = base_url + "main-LUDXZMP5.js"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

r = requests.get(main_js_url, headers=headers)
print("Main JS size:", len(r.text))
with open("5millionsertifikat/main.js", "w", encoding="utf-8") as f:
    f.write(r.text)

# Search for API URLs
apis = set(re.findall(r'["\'](/api/[^"\']+|https?://[^"\']+)["\']', r.text))
print("Sample APIs found:")
for a in list(apis)[:20]:
    if "api" in a or "auth" in a:
        print(" ->", a)

# Search for recaptcha
recaptcha_matches = re.findall(r'(recaptcha[a-zA-Z0-9_\-:="\'\s]{1,100})', r.text, re.IGNORECASE)
print("Recaptcha matches:", recaptcha_matches[:10])

# Search for register or pasport / metrika
register_matches = re.findall(r'([a-zA-Z0-9_/]+register[a-zA-Z0-9_/]*)', r.text, re.IGNORECASE)
print("Register matches:", set(register_matches))
