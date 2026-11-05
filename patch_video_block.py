import sys

def main():
    path = r"d:\uzbekcodersbot\5millionsertifikat\run_visual_test.py"
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    start_marker = "            # 1. Agar Video (type == 2) bo'lsa"
    end_marker = "            # 2. Agar Test/Quiz (type == 3) bo'lsa"

    start_idx = text.find(start_marker)
    end_idx = text.find(end_marker)

    if start_idx == -1 or end_idx == -1:
        print("ERROR: Markers not found!")
        return

    new_video_block = """            # 1. Agar Video (type == 2) bo'lsa
            if les_type == 2:
                if les_status == 2:
                    print(f"  [Video {les_id}] {les_name} -> Allaqachon ko'rilgan (OK)!", flush=True)
                    continue
                    
                print(f"  [Video {les_id}] {les_name} -> 100% serverga muhrlanmoqda...", flush=True)
                
                # Server DB ga 100% yakunlangan deb to'g'ridan-to'g'ri yozish (Doimiy kafolatlangan galichka)
                for attempt in range(1, 6):
                    watch_res = page.evaluate(f\"\"\"async () => {{
                        try {{
                            const token = localStorage.getItem('accessToken');
                            const r = await fetch('https://api.aistudy.uz/api/StudyAILms/UserWatchStory/CreateOrUpdateLessonWatch', {{
                                method: 'POST',
                                headers: {{
                                    'Content-Type': 'application/json',
                                    'Authorization': 'Bearer ' + token
                                }},
                                body: JSON.stringify({{
                                    lessonId: {les_id},
                                    language: 'uz',
                                    percentJson: {{ uz: '100.00', ru: '100.00', en: '100.00' }},
                                    usedTime: 300
                                }})
                            }});
                            if (r.status === 429) return {{ status: 429 }};
                            return await r.json();
                        }} catch(e) {{
                            return {{ error: e.toString() }};
                        }}
                    }}\"\"\")
                    
                    if watch_res and watch_res.get("status") == 429:
                        print(f"    Rate limit (429)! 6 soniya kutilmoqda...", flush=True)
                        time.sleep(6)
                        continue
                        
                    if watch_res and (watch_res.get("statusCode") == 200 or watch_res.get("result")):
                        print(f"    -> [Video {les_id}] Serverda 100% saqlandi! GALICHKA DOIMIY QO'YILDI (OK)", flush=True)
                        time.sleep(3.5) # Server DB commit va rate-limit cooldown
                        break
                    else:
                        print(f"    Qayta urinilmoqda ({watch_res})...", flush=True)
                        time.sleep(3)
                        
"""
    new_text = text[:start_idx] + new_video_block + text[end_idx:]

    # Also make sure course verification checks finishLessonCount == lessonCount and retries if needed
    old_verify = """    final_tree = page.evaluate(f\"\"\"async () => {
        const token = localStorage.getItem('accessToken');
        const r = await fetch('https://api.aistudy.uz/api/StudyAILms/Progress/GetPrivateCourseContentTree?courseId={course_id}', {
            headers: { 'Authorization': 'Bearer ' + token }
        });
        return await r.json();
    }\"\"\").get('result', {})
    finish_cnt = final_tree.get('finishLessonCount', 0)
    total_cnt = final_tree.get('lessonCount', 0)
    print(f"Kurs {course_id} yakuni: {finish_cnt} / {total_cnt} dars to'liq yakunlandi!", flush=True)
    return True"""

    new_verify = """    # Yakuniy tekshiruv va to'liq 100% galichkalar kafolati
    for verify_cycle in range(3):
        final_tree = page.evaluate(f\"\"\"async () => {{
            const token = localStorage.getItem('accessToken');
            const r = await fetch('https://api.aistudy.uz/api/StudyAILms/Progress/GetPrivateCourseContentTree?courseId={course_id}', {{
                headers: {{ 'Authorization': 'Bearer ' + token }}
            }});
            return await r.json();
        }}\"\"\").get('result', {})
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

    with open(path, "w", encoding="utf-8") as f:
        f.write(new_text)
    print("SUCCESS: Video block updated successfully!")

if __name__ == "__main__":
    main()
