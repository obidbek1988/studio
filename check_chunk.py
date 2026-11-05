import requests

r = requests.get("https://omp.aistudy.uz/chunk-4VTC4MLB.js")
print("chunk-4VTC4MLB len:", len(r.text))
with open("5millionsertifikat/devtools-detector.js", "w", encoding="utf-8") as f:
    f.write(r.text)
print(r.text[:1000])
