import requests
import json

# Let's query public API of aistudy.uz for course 1
try:
    r = requests.get("https://api.aistudy.uz/api/StudyAILms/Course/GetCourseById?id=1", timeout=5)
    print("Status:", r.status_code)
    if r.status_code == 200:
        data = r.json()
        print("Course 1 title:", data.get("result", {}).get("name"))
        modules = data.get("result", {}).get("courseModules", [])
        print("Modules count:", len(modules))
        for m in modules:
            print(f"Module {m.get('order')}: {m.get('name')} (Lessons: {len(m.get('lessons', []))})")
            for l in m.get('lessons', []):
                print(f"   - Lesson {l.get('order')}: {l.get('name')} (Type: {l.get('type')}, ID: {l.get('id')})")
except Exception as e:
    print("Error:", e)
