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

for c_id in range(1, 5):
    print(f"\n==================== COURSE {c_id} ====================")
    # Start course
    r_start = requests.post(f"{BASE}/Progress/StartCourseProgress?courseId={c_id}", headers=headers, json={})
    print(f"Start Course {c_id}:", r_start.status_code, r_start.text[:200])
    
    # Get Tree
    r_tree = requests.get(f"{BASE}/Progress/GetPrivateCourseContentTree?courseId={c_id}", headers=headers)
    print(f"Tree {c_id} Status:", r_tree.status_code)
    if r_tree.status_code == 200:
        data = r_tree.json().get("result", {})
        print("Course Name:", data.get("name"))
        print("Progress:", data.get("finishLessonCount"), "/", data.get("lessonCount"))
        modules = data.get("children", [])
        for m in modules:
            print(f"  Module {m.get('order')}: ID={m.get('id')}, Name={m.get('name')}")
            for l in m.get("children", []):
                print(f"    Lesson: ID={l.get('id')}, Order={l.get('order')}, Type={l.get('type')}, Status={l.get('status')}, Name={l.get('name')}")
