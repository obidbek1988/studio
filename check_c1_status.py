import requests

with open("5millionsertifikat/token.txt") as f:
    token = f.read().strip()
headers = {"Authorization": f"Bearer {token}"}

r = requests.get("https://api.aistudy.uz/api/StudyAILms/Progress/GetPrivateCourseContentTree?courseId=1", headers=headers)
tree = r.json().get("result") or {}
for m in tree.get("children", []):
    print("Mod:", m.get("id"), m.get("name", {}).get("uz"))
    for l in m.get("children", []):
        print(f"  Lesson ID={l.get('id')}, Type={l.get('type')}, Status={l.get('status')}, Name={l.get('name', {}).get('uz')}")
