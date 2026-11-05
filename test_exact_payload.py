import requests
import json

with open("5millionsertifikat/token.txt") as f:
    token = f.read().strip()

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json",
    "Accept": "application/json, text/plain, */*"
}

# Modul 3, Dars 4 (Uzluksiz ta'lim haqida muhim eslatma)
# Dars davomiyligi 56 soniya (usedTime: 50)
payload = {
    "lessonId": 4,
    "language": "uz",
    "percentJson": {
        "uz": "100.00",
        "ru": "100.00",
        "en": "100.00"
    },
    "usedTime": 50
}

r = requests.post("https://api.aistudy.uz/api/StudyAILms/UserWatchStory/CreateOrUpdateLessonWatch", headers=headers, json=payload)
print("Status:", r.status_code)
print("Resp:", r.text)

# Tekshirish
r_tree = requests.get("https://api.aistudy.uz/api/StudyAILms/Progress/GetPrivateCourseContentTree?courseId=1", headers=headers)
tree = r_tree.json().get("result", {})
print("Progress:", tree.get("finishLessonCount"), "/", tree.get("lessonCount"))
for m in tree.get("children", []):
    for l in m.get("children", []):
        if l.get("id") == 4:
            print("Lesson 4 status:", l.get("status"))
