with open(r'd:\uzbekcodersbot\5millionsertifikat\lesson-component.js', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

idx = text.find('omp-course-modules-accordion')
print("=== template ===")
print(text[idx+500:idx+3000])
