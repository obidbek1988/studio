import requests
import re

for chunk in ["chunk-XMXPFVQ2.js", "chunk-2L4VB2S5.js"]:
    r = requests.get("https://omp.aistudy.uz/" + chunk)
    print(chunk, r.status_code, len(r.text))
    with open("5millionsertifikat/" + chunk, "w", encoding="utf-8") as f:
        f.write(r.text)
    
    # search endpoints
    for m in re.finditer(r'["\'](Courses/[^"\']+|Module/[^"\']+|Quiz/[^"\']+|Lesson/[^"\']+|Certificate/[^"\']+)["\']', r.text, re.IGNORECASE):
        print(f"[{chunk}] API:", m.group(0))
