import re

with open("5millionsertifikat/page_sample.html", "r", encoding="utf-8") as f:
    text = f.read()

scripts = re.findall(r'src=["\']([^"\']+)["\']', text)
print("Scripts found:")
for s in scripts:
    print(" -", s)

# Look for api endpoints or recaptcha
for m in re.finditer(r'(https?://[^\s"\'<>]+|/api/[^\s"\'<>]+)', text):
    print("Link/endpoint:", m.group(0)[:100])
