import requests
import re

r = requests.get("https://omp.aistudy.uz/chunk-JDFH24T7.js")
print("chunk-JDFH24T7 len:", len(r.text))
with open("5millionsertifikat/chunk-auth-service.js", "w", encoding="utf-8") as f:
    f.write(r.text)

# Search for fetchPersonDataFromGCP
pos = r.text.find("fetchPersonDataFromGCP")
if pos != -1:
    print("Found fetchPersonDataFromGCP:")
    print(r.text[max(0, pos-100):pos+600])

# Search for all endpoints and apiUrl
for m in re.finditer(r'https?://[a-zA-Z0-9_\-\./:]+|/(api|v1|auth)[a-zA-Z0-9_\-\./:]*', r.text):
    print("Endpoint:", m.group(0))
