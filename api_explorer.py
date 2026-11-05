import json
import requests

with open("5millionsertifikat/token.txt") as f:
    token = f.read().strip()

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json",
    "Accept": "application/json, text/plain, */*"
}

BASE = "https://api.aistudy.uz/api/StudyAILms"

# 1. Barcha 4 ta kurs ma'lumotini olish
for course_id in range(1, 5):
    r = requests.get(f"{BASE}/Course/GetCourseById?id={course_id}", headers=headers)
    print(f"\n=================== COURSE {course_id} (Status: {r.status_code}) ===================")
    if r.status_code == 200:
        c_data = r.json().get("result", {})
        print("Course Name:", c_data.get("courseName", {}).get("uz"))
        modules = c_data.get("courseModules", [])
        print(f"Modules count: {len(modules)}")
        for m in modules:
            print(f"  Modul {m.get('order')}: ID={m.get('id')}, Name={m.get('name')}")
            lessons = m.get("lessons", [])
            print(f"    Darslar soni: {len(lessons)}")
            for l in lessons:
                print(f"      Dars {l.get('order')}: ID={l.get('id')}, Type={l.get('type')}, Name={l.get('name')}")
