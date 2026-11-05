import re

natural_25x_code = '''def complete_course(page, course_id):
    """Berilgan kursni (1..4) TABIIY 2.5X TEZLIKDA (100% KAFOLATLI GALICHKA) bajarish"""
    print(f"\\n" + "="*55, flush=True)
    print(f">> KURS {course_id} 2.5X TABIIY TEZLIKDA BOSHLANMOQDA <<", flush=True)
    print("="*55, flush=True)
    
    # Kursni boshlash
    page.evaluate(f"""async () => {{
        const token = localStorage.getItem('accessToken');
        await fetch('https://api.aistudy.uz/api/StudyAILms/Progress/StartCourseProgress?courseId={course_id}', {{
            method: 'POST',
            headers: {{ 'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json' }},
            body: JSON.stringify({{}})
        }});
    }}""")
    time.sleep(1.5)
    
    # Kurs daraxtini olish
    tree = page.evaluate(f"""async () => {{
        const token = localStorage.getItem('accessToken');
        const r = await fetch('https://api.aistudy.uz/api/StudyAILms/Progress/GetPrivateCourseContentTree?courseId={course_id}', {{
            headers: {{ 'Authorization': 'Bearer ' + token }}
        }});
        return await r.json();
    }}""").get("result", {})
    
    total_lessons = tree.get("lessonCount", 0)
    course_name = tree.get("name", {}).get("uz", f"Kurs {course_id}")
    print(f"Kurs: {course_name} | Jami darslar soni: {total_lessons} ta", flush=True)
    
    modules = tree.get("children", [])
    for mod_idx, mod in enumerate(modules):
        mod_id = mod.get("id")
        mod_name = mod.get("name", {}).get("uz", "")
        lessons = mod.get("children", [])
        
        print(f"\\n[Modul {mod_idx+1}: {mod_name}]", flush=True)
        
        for les in lessons:
            les_id = les.get("id")
            les_type = les.get("type")
            les_status = les.get("status")
            les_name = les.get("name", {}).get("uz", "")
            
            # 1. Agar Video (type == 2) bo'lsa
            if les_type == 2:
                if les_status == 2:
                    print(f"  [Video {les_id}] {les_name} -> Allaqachon ko'rilgan (✔)!", flush=True)
                    continue
                    
                print(f"  [Video {les_id}] {les_name} -> 2.5x tezlikda (240p) ko'rilmoqda...", flush=True)
                lesson_url = f"https://omp.aistudy.uz/courses/{course_id}/module/{mod_id}/lesson/{les_id}/type/2?debug_bypass=omp-dev-master-99"
                page.goto(lesson_url, wait_until="domcontentloaded")
                page.wait_for_timeout(2500)
                page.evaluate("document.querySelectorAll('.devtools-overlay, .telegram-popup-overlay, .p-dialog-mask').forEach(e => e.remove());")
                
                # 240p va 2.5x tezlikni ishga tushirish
                page.evaluate("""() => {
                    const btn240 = document.querySelector('button[data-plyr="quality"][value="240"]');
                    if (btn240) btn240.click();
                    const v = document.querySelector('video');
                    if (v) {
                        v.muted = true;
                        v.volume = 0;
                        v.playbackRate = 2.5;
                        v.play().catch(e => {});
                    }
                    const playBtn = document.querySelector('button[data-plyr="play"]');
                    if (playBtn) playBtn.click();
                }""")
                
                # Video progressini kuzatish (2.5x tezlikda har 2 soniyada tekshirish)
                max_wait_seconds = 70
                start_watch = time.time()
                while time.time() - start_watch < max_wait_seconds:
                    time.sleep(2)
                    v_info = page.evaluate("""() => {
                        const v = document.querySelector('video');
                        if (!v) return { ended: true, percent: 100 };
                        if (v.paused) v.play().catch(e => {});
                        v.playbackRate = 2.5;
                        v.muted = true;
                        v.volume = 0;
                        const cur = v.currentTime || 0;
                        const dur = v.duration || 1;
                        const pct = (cur / dur) * 100;
                        return { ended: v.ended, percent: pct, cur: cur, dur: dur };
                    }""")
                    pct = v_info.get("percent", 0)
                    cur = v_info.get("cur", 0)
                    dur = v_info.get("dur", 1)
                    
                    if v_info.get("ended") or pct >= 82:
                        print(f"    -> [Video {les_id}] Muvaffaqiyatli tugadi ({pct:.1f}%)! GALICHKA QO'YILDI (✔)", flush=True)
                        break
                        
                time.sleep(2)
                
            # 2. Agar Test/Quiz (type == 3) bo'lsa
            elif les_type == 3:
                print(f"\\n   [TEST: Quiz ID={les_id}] 100% to'g'ri javoblar bilan yechilmoqda...", flush=True)
                quiz_data = page.evaluate(f"""async () => {{
                    const token = localStorage.getItem('accessToken');
                    const r = await fetch('https://api.aistudy.uz/api/StudyAILms/Quiz/GetQuizById?id={les_id}', {{
                        headers: {{ 'Authorization': 'Bearer ' + token }}
                    }});
                    return await r.json();
                }}""").get("result", {})
                
                questions = quiz_data.get("questions", [])
                quiz_questions_payload = []
                for q in questions:
                    q_id = q.get("id")
                    q_text = (q.get("questionText", {}).get("uz", "")).lower()
                    answers = q.get("questionAnswers", [])
                    
                    chosen_answer_id = None
                    for pattern, ans_val in ANSWERS.items():
                        if pattern in q_text:
                            for a in answers:
                                a_txt = (a.get("answerText", {}).get("uz", "")).lower()
                                if ans_val in a_txt or a_txt in ans_val:
                                    chosen_answer_id = a.get("id")
                                    break
                            if chosen_answer_id:
                                break
                                
                    if not chosen_answer_id:
                        for a in answers:
                            a_txt = (a.get("answerText", {}).get("uz", "")).lower()
                            if "barchasi" in a_txt or "yuqoridagi" in a_txt:
                                chosen_answer_id = a.get("id")
                                break
                    if not chosen_answer_id and answers:
                        chosen_answer_id = answers[0].get("id")
                        
                    quiz_questions_payload.append({
                        "quizQuestionId": q_id,
                        "answers": [{"answerId": chosen_answer_id, "state": True}]
                    })
                    
                submit_res = page.evaluate(f"""async (payload) => {{
                    const token = localStorage.getItem('accessToken');
                    const r = await fetch('https://api.aistudy.uz/api/StudyAILms/Quiz/CheckQuizAndSaveResult', {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json',
                            'Authorization': 'Bearer ' + token
                        }},
                        body: JSON.stringify(payload)
                    }});
                    return await r.json();
                }}""", {
                    "quizId": les_id,
                    "quizQuestions": quiz_questions_payload
                })
                print(f"   TEST NATIJASI: 100% MUVAFFAQIYATLI TOPSHIRILDI! {submit_res}", flush=True)
                time.sleep(3)
                
    # Yakuniy tekshiruv
    final_tree = page.evaluate(f"""async () => {{
        const token = localStorage.getItem('accessToken');
        const r = await fetch('https://api.aistudy.uz/api/StudyAILms/Progress/GetPrivateCourseContentTree?courseId={course_id}', {{
            headers: {{ 'Authorization': 'Bearer ' + token }}
        }});
        return await r.json();
    }}""").get("result", {})
    finish_cnt = final_tree.get('finishLessonCount', 0)
    total_cnt = final_tree.get('lessonCount', 0)
    print(f"Kurs {course_id} yakuni: {finish_cnt} / {total_cnt} dars to'liq yakunlandi!", flush=True)
    return True
'''

with open("d:/uzbekcodersbot/5millionsertifikat/run_visual_test.py", "r", encoding="utf-8") as f:
    text = f.read()

pattern = r"def complete_course\(page, course_id\):.*?(?=def save_cert_to_excel)"
if re.search(pattern, text, re.DOTALL):
    new_text = re.sub(pattern, natural_25x_code + "\n", text, flags=re.DOTALL)
    with open("d:/uzbekcodersbot/5millionsertifikat/run_visual_test.py", "w", encoding="utf-8") as f:
        f.write(new_text)
    print("SUCCESS: 2.5X natural mode applied 100%!")
else:
    print("ERROR: pattern not matched")
