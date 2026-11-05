with open(r'd:\uzbekcodersbot\5millionsertifikat\lesson-component.js', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

import re
matches = re.findall(r'CourseModule/[A-Za-z0-9_]+|Lesson/[A-Za-z0-9_]+', text)
print("Endpoints:", set(matches))
