import requests

r = requests.get("https://omp.aistudy.uz/chunk-LYFEPOK3.js")
print("chunk-LYFEPOK3.js status:", r.status_code, "len:", len(r.text))
with open("5millionsertifikat/chunk-LYFEPOK3.js", "w", encoding="utf-8") as f:
    f.write(r.text)
print("Content:\n", r.text)
