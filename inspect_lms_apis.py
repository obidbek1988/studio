with open(r'd:\uzbekcodersbot\5millionsertifikat\lesson-component.js', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

for term in ['CheckQuizAndSaveResult', 'CreateOrUpdateLessonWatch']:
    idx = text.find(term)
    print(f"=== {term} ===")
    while idx != -1:
        print(text[max(0, idx-100):min(len(text), idx+300)])
        idx = text.find(term, idx + 1)
