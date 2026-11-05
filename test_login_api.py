import requests

url = "https://api.aistudy.uz/api/StudyAILms/Account/Login"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Content-Type": "application/json",
    "Origin": "https://omp.aistudy.uz",
    "Referer": "https://omp.aistudy.uz/"
}
payload = {
    "username": "maktabin.f.orm.ati.k1@gmail.com",
    "password": "Maktab29"
}

r = requests.post(url, json=payload, headers=headers)
print("Login status:", r.status_code)
print("Login response:", r.text[:300])
