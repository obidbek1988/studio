import requests
import re

for s in ["scripts-IA5QKANT.js", "polyfills-FFHMD2TL.js"]:
    r = requests.get("https://omp.aistudy.uz/" + s)
    print(s, len(r.text))
    with open("5millionsertifikat/" + s, "w", encoding="utf-8") as f:
        f.write(r.text)

# Search for baseUrl or environment or api
with open("5millionsertifikat/main.js", "r", encoding="utf-8") as f:
    text = f.read()

# search environment config
print("Search environment/backend:")
for m in re.finditer(r'(apiUrl|baseUrl|backend|endpoint|host|domain)[":\s]+["\']([^"\']+)["\']', text, re.IGNORECASE):
    print("Env match:", m.group(0))

for m in re.finditer(r'https?://[a-zA-Z0-9\.\-_/]+', text):
    u = m.group(0)
    if "w3.org" not in u and "google" not in u and "github" not in u:
        print("URL found:", u)
