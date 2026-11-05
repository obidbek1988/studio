import sys

def main():
    path = r"d:\uzbekcodersbot\5millionsertifikat\run_visual_test.py"
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    old_target = """    # Yakuniy tekshiruv
    final_tree = page.evaluate(f\"\"\"async () => {
        const token = localStorage.getItem('accessToken');
        const r = await fetch('https://api.aistudy.uz/api/StudyAILms/Progress/GetPrivateCourseContentTree?courseId={course_id}', {
            headers: { 'Authorization': 'Bearer ' + token }
        });
        return await r.json();
    }\"\"\").get("result", {})
    finish_cnt = final_tree.get('finishLessonCount', 0)
    total_cnt = final_tree.get('lessonCount', 0)
    print(f"Kurs {course_id} yakuni: {finish_cnt} / {total_cnt} dars to'liq yakunlandi!", flush=True)
    return True"""

    new_replacement = """    # Yakuniy tekshiruv va to'liq 100% galichkalar kafolati
    for verify_cycle in range(3):
        final_tree = page.evaluate(f\"\"\"async () => {{
            const token = localStorage.getItem('accessToken');
            const r = await fetch('https://api.aistudy.uz/api/StudyAILms/Progress/GetPrivateCourseContentTree?courseId={course_id}', {{
                headers: {{ 'Authorization': 'Bearer ' + token }}
            }});
            return await r.json();
        }}\"\"\").get("result", {})
        finish_cnt = final_tree.get('finishLessonCount', 0)
        total_cnt = final_tree.get('lessonCount', 0)
        print(f"Kurs {course_id} tekshiruv ({verify_cycle+1}): {finish_cnt} / {total_cnt} dars yakunlandi!", flush=True)
        if finish_cnt >= total_cnt:
            return True
        # Agar qolib ketgan dars bo'lsa qayta yuborish
        for m in final_tree.get("children", []):
            for l in m.get("children", []):
                if l.get("type") == 2 and l.get("status") != 2:
                    l_id = l.get("id")
                    print(f"  Qayta yuborilmoqda: Video {l_id}...")
                    page.evaluate(f\"\"\"async () => {{
                        const token = localStorage.getItem('accessToken');
                        await fetch('https://api.aistudy.uz/api/StudyAILms/UserWatchStory/CreateOrUpdateLessonWatch', {{
                            method: 'POST',
                            headers: {{ 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token }},
                            body: JSON.stringify({{
                                lessonId: {l_id},
                                language: 'uz',
                                percentJson: {{ uz: '100.00', ru: '100.00', en: '100.00' }},
                                usedTime: 300
                            }})
                        }});
                    }}\"\"\")
                    time.sleep(4)
    return finish_cnt >= total_cnt"""

    if old_target in text:
        text = text.replace(old_target, new_replacement)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        print("SUCCESS: Enhanced verify loop added!")
    else:
        print("WARNING: old_target not exact match, let's locate and replace.")
        idx = text.find("# Yakuniy tekshiruv")
        idx2 = text.find("def save_cert_to_excel")
        if idx != -1 and idx2 != -1:
            text = text[:idx] + new_replacement + "\n\n" + text[idx2:]
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
            print("SUCCESS: Enhanced verify loop replaced via markers!")

if __name__ == "__main__":
    main()
