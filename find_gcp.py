import re

with open("5millionsertifikat/main.js", "r", encoding="utf-8") as f:
    text = f.read()

# search fetchPersonDataFromGCP
for m in re.finditer(r'fetchPersonDataFromGCP[^{]+{([^}]+)}', text):
    print("fetchPersonDataFromGCP:", m.group(0))

# search for recaptcha sitekey
for m in re.finditer(r'(siteKey|site_key|v2|v3|recaptcha)[":\s]+["\']([^"\']+)["\']', text, re.IGNORECASE):
    print("Recaptcha config match:", m.group(0))

# search api endpoints
for m in re.finditer(r'/(api|v1|auth)/[a-zA-Z0-9_\-/]+', text):
    print("API endpoint in main:", m.group(0))
