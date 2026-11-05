with open(r'd:\uzbekcodersbot\5millionsertifikat\lesson-component.js', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

import re
# Find template elements or classes in lesson-component
idx = text.find('omp-course-video')
print(text[max(0, idx-500):min(len(text), idx+1000)])
