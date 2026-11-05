import requests

# Test fetching Course 1 details
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

# In environment.js: baseUrl = "https://api.aistudy.uz/api/StudyAILms"
for endpoint in [
    "Course/GetCourseById?id=1",
    "Course/GetAllCourses",
    "Module/GetModulesByCourseId?courseId=1",
    "Lesson/GetLessonsByModuleId?moduleId=1",
    "Quiz/GetQuizById?id=1"
]:
    try:
        r = requests.get(f"https://api.aistudy.uz/api/StudyAILms/{endpoint}", headers=headers, timeout=10)
        print(f"[{endpoint}] Status: {r.status_code}, Len: {len(r.text)}")
        if r.status_code == 200 and len(r.text) < 1000:
            print("  Response:", r.text)
    except Exception as e:
        print(f"[{endpoint}] Error: {e}")
