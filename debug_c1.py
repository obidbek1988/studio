import requests
import json
import sys

if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

token = open('5millionsertifikat/token.txt').read().strip()
h = {'Authorization': f'Bearer {token}'}
tree = requests.get('https://api.aistudy.uz/api/StudyAILms/Progress/GetPrivateCourseContentTree?courseId=1', headers=h).json().get('result', {})
print(f"Jami darslar: {tree.get('lessonCount')}, Bajarilgan: {tree.get('finishLessonCount')}")

for m in tree.get('children', []):
    print(f"\nMODUL: {m.get('name', {}).get('uz')}")
    for l in m.get('children', []):
        st = "✔ BAJARILGAN" if l.get('status') == 2 else f"❌ QOLGAN (status={l.get('status')})"
        tp = "VIDEO" if l.get('type') == 2 else "QUIZ"
        print(f"  [{tp}] ID={l.get('id')} | {l.get('name', {}).get('uz')} | {st}")
