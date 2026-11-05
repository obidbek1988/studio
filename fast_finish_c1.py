import requests
import json
import time

with open("5millionsertifikat/token.txt") as f:
    token = f.read().strip()

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json",
    "Accept": "application/json, text/plain, */*"
}

time.sleep(5) # Cooldown

r = requests.get("https://api.aistudy.uz/api/StudyAILms/Progress/GetPrivateCourseContentTree?courseId=1", headers=headers)
tree = r.json().get("result", {})
print(f"Boshlang'ich progress: {tree.get('finishLessonCount')} / {tree.get('lessonCount')}")

for mod in tree.get("children", []):
    for les in mod.get("children", []):
        if les.get("type") == 2 and les.get("status") != 2:
            les_id = les.get("id")
            les_name = les.get("name", {}).get("uz", "")
            print(f">> [Video {les_id}] {les_name} -> yuborilmoqda...")
            payload = {
                "lessonId": les_id,
                "language": "uz",
                "percentJson": { "uz": "100.00", "ru": "100.00", "en": "100.00" },
                "usedTime": 300
            }
            while True:
                res = requests.post("https://api.aistudy.uz/api/StudyAILms/UserWatchStory/CreateOrUpdateLessonWatch", headers=headers, json=payload)
                if res.status_code == 429:
                    print("   Rate limit (429)! 6s kutilmoqda...")
                    time.sleep(6)
                    continue
                print(f"   Javob: {res.status_code} (Muvaffaqiyatli!)")
                time.sleep(6)
                break

r2 = requests.get("https://api.aistudy.uz/api/StudyAILms/Progress/GetPrivateCourseContentTree?courseId=1", headers=headers)
tree2 = r2.json().get("result", {})
print(f"\nYAKUNIY PROGRESS: {tree2.get('finishLessonCount')} / {tree2.get('lessonCount')}")
