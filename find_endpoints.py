import requests
import re

url = "https://omp.aistudy.uz/main-LUDXZMP5.js"
text = requests.get(url).text
chunks = set(re.findall(r"chunk-[A-Za-z0-9]+\.js", text))

for ch in chunks:
    try:
        t = requests.get(f"https://omp.aistudy.uz/{ch}").text
        idx = t.find("UserRegisteration")
        if idx != -1:
            print(f"=== FOUND in {ch} ===")
            print(t[max(0, idx - 100):idx + 300])
        idx2 = t.find("verificationCode")
        if idx2 != -1:
            print(f"=== verificationCode in {ch} ===")
            print(t[max(0, idx2 - 100):idx2 + 300])
    except Exception:
        pass
