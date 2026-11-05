import requests

r = requests.get("https://omp.aistudy.uz/chunk-4KYXDVQJ.js")
print("Environment chunk content:")
print(r.text)
with open("5millionsertifikat/environment.js", "w", encoding="utf-8") as f:
    f.write(r.text)
