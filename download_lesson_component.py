import requests
import re

r = requests.get("https://omp.aistudy.uz/chunk-GYCK2JMK.js")
print("chunk-GYCK2JMK status:", r.status_code, "len:", len(r.text))
with open("5millionsertifikat/lesson-component.js", "w", encoding="utf-8") as f:
    f.write(r.text)

# Search for API endpoints
for m in re.finditer(r'["\']([a-zA-Z0-9_\-/]+(?:Quiz|Test|Question|Answer|Lesson|Certificate|Submit)[a-zA-Z0-9_\-/]*)["\']', r.text, re.IGNORECASE):
    print("Endpoint:", m.group(0))
