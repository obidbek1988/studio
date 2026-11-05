import json
import requests

with open("5millionsertifikat/token.txt") as f:
    token = f.read().strip()

headers = {"Authorization": f"Bearer {token}"}

for c in range(1, 5):
    # Ensure course is started
    requests.post(f"https://api.aistudy.uz/api/StudyAILms/Progress/StartCourseProgress?courseId={c}", headers=headers, json={})
    
    r = requests.get(f"https://api.aistudy.uz/api/StudyAILms/Progress/GetPrivateCourseContentTree?courseId={c}", headers=headers)
    tree = r.json().get("result") or {}
    print(f"\n================ COURSE {c} ================")
    print("Finish:", tree.get("finishLessonCount"), "/", tree.get("lessonCount"))
    for m in tree.get("children", []):
        for l in m.get("children", []):
            if l.get("type") == 3:
                print(f"QUIZ: Course {c}, Module {m.get('id')}, Quiz/Lesson ID={l.get('id')}, Status={l.get('status')}")
