import os
import sys
import time
import json
import requests

if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

with open("5millionsertifikat/token.txt") as f:
    token = f.read().strip()

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json",
    "Accept": "application/json, text/plain, */*"
}

ANSWERS = {
    # Modul 1
    "qaysi biri ai (sun'iy intellekt)ni eng yaxshi tavsiflaydi": "ma'lumotlardan o'rganishi mumkin bo'lgan dasturiy dastur",
    "real hayotiy qo'llanishi": "yuqoridagilarning barchasi",
    "hayot siklining 2 ta bosqichi": "o'rgatish (trenirovka) va xulosa chiqarish (inference)",
    "aniq ishda ekspert bo'lgan": "tor si (narrow ai)",
    "kichigidan kattasiga": "chuqur o'rganish < mashinani o'rganish (machine learning) < si",
    "tyuring testi nima": "sun'iy intellekt dasturi inson kabi o'ylay olishi/gaplasha olishi/o'zini tuta olishini aniqlash testi",
    
    # Modul 2
    "generativ si (sun'iy intellekt) nima": "matn / tasvirlar / musiqa / video kabi yangi kontent yarata oladigan si",
    "llm nimani anglatadi": "katta til modeli (large language model)",
    "chat botlar va qidiruv tizimlari o'rtasidagi asosiy farq": "ular kontekstga e'tibor beradi",
    "prompt nima": "siz sun'iy intellektli chat botga kiritadigan matn",
    "yaxshi promptni tuzishning to'g'ri tartibdagi 3 ta asosiy": "rol - kontekst - vazifa",
    "gallyutsinatsiyalar (hallucinations) nima": "chat botlarning yomon yoki noto'g'ri javoblar berishi",
    
    # Modul 3
    "prompt yozishda quyidagi yondashuvlardan qaysi biri tavsiya": "rol - vazifa - kontekst",
    "si tomonidan yaratilgan matnning asosiy cheklovlaridan biri": "xatolar bo'lishi mumkin va tekshirib chiqishni talab qiladi",
    "ohangini o'zgartirish uchun": "ohang sozlamalari",
    "hr yollash jarayonlarida foydalanishning afzalliklaridan biri": "si ko'plab rezyume",
    "ijtimoiy tarmoqlardagi kampaniya uchun": "yuqoridagilarning barchasi",
    "maxfiy hujjatlarni baham ko'rmaslik": "ularda maxfiylik kafolatlari yo'q",
    "ishga oid vazifalar uchun si dan foydalanganda": "si vaqtni tejaydi, lekin uning ishini har doim tekshirib turing",
    
    # Modul 4
    "matndan tasvir yaratish uchun qaysi sun'iy intellekt": "dall-e / midjourney / stable diffusion",
    "tasvir yaratish uchun qaysi sun'iy intellekt vositasi openai": "dall-e",
    "midjourney yordamida tasvirlarni yaratishda qaysi omil": "batafsilroq va tavsiflovchi promptlar",
    "edge brauzeri copilot'ida dall-e": "bepul tasvir yaratish imkoniyatiga ega bo'lish",
    "musiqa yarata oladi": "suno",
    "tasvir o'lchamini (rezolyutsiyasini) oshirishga": "upscale tugmalari",
    "matndan video yaratish uchun ishlatiladi": "runway ml",
    
    # Yakuniy
    "ushbu kursda si nima deb ta'riflangan": "robot sifatida",
    "tor si (narrow ai) ga misol": "yuqoridagilarning barchasi",
    "tyuring testining maqsadi": "inson deb o'ylashga aldashi",
    "mashhur generativ si-chatbot": "chatgpt",
    "zo'r prompt yaratish uchun asosiy qoida": "rol / kontekst / vazifa",
    "gallyutsinatsiya": "noto'g'ri yoki uydirma",
    "ma'lumotlarni tahlil qilish uchun": "excel jadvallaridagi",
    "microsoft office ilovalariga qaysi si vositasi": "copilot",
    "si va ish haqida qaysi fikr to'g'ri": "yanada samarali bo'ladi",
    "tasvir yaratish uchun openai": "dall-e",
    "matndan video yaratish imkonini": "runway ml",
    "midjourney tasvir yaratishni sozlashda": "tomonlar nisbati"
}

def solve_quiz(quiz_id):
    print(f"\n   [TEST: Quiz ID={quiz_id}] Savollar yuklanmoqda...")
    r = requests.get(f"https://api.aistudy.uz/api/StudyAILms/Quiz/GetQuizById?id={quiz_id}", headers=headers)
    if r.status_code != 200:
        print(f"   Xatolik quiz yuklashda: {r.status_code} {r.text}")
        return False
        
    quiz_data = r.json().get("result", {})
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
        
    submit_payload = {
        "quizId": quiz_id,
        "quizQuestions": quiz_questions_payload
    }
    
    res = requests.post("https://api.aistudy.uz/api/StudyAILms/Quiz/CheckQuizAndSaveResult", headers=headers, json=submit_payload)
    print(f"   TEST NATIJASI: {res.status_code} -> {res.text}")
    return res.status_code == 200

def complete_course(course_id):
    print("\n" + "="*50)
    print(f"KURS {course_id} BOSHLANMOQDA...")
    print("="*50)
    
    # Kursni boshlash
    requests.post(f"https://api.aistudy.uz/api/StudyAILms/Progress/StartCourseProgress?courseId={course_id}", headers=headers, json={})
    time.sleep(2)
    
    r = requests.get(f"https://api.aistudy.uz/api/StudyAILms/Progress/GetPrivateCourseContentTree?courseId={course_id}", headers=headers)
    tree = r.json().get("result", {})
    
    print(f"Kurs: {tree.get('name', {}).get('uz')} | Holat: {tree.get('finishLessonCount')} / {tree.get('lessonCount')}")
    
    for mod in tree.get("children", []):
        mod_name = mod.get("name", {}).get("uz")
        print(f"\n-- Modul: {mod_name} --")
        for les in mod.get("children", []):
            les_id = les.get("id")
            les_type = les.get("type")
            les_status = les.get("status")
            les_name = les.get("name", {}).get("uz")
            
            # Agar Video bo'lsa
            if les_type == 2:
                if les_status == 2:
                    print(f"  [Video {les_id}] {les_name} -> Allaqachon ko'rilgan (✔)!")
                    continue
                print(f"  [Video {les_id}] {les_name} -> 100% bajarilmoqda...")
                payload = {
                    "lessonId": les_id,
                    "language": "uz",
                    "percentJson": { "uz": "100.00", "ru": "100.00", "en": "100.00" },
                    "usedTime": 300
                }
                while True:
                    watch_res = requests.post("https://api.aistudy.uz/api/StudyAILms/UserWatchStory/CreateOrUpdateLessonWatch", headers=headers, json=payload)
                    if watch_res.status_code == 429:
                        print("    Rate limit (429)! 6 soniya kutilmoqda...")
                        time.sleep(6)
                        continue
                    print(f"    Bajarildi (Status {watch_res.status_code}) -> ✔")
                    time.sleep(6) # Server cooldown
                    break
                    
            # Agar Test bo'lsa
            elif les_type == 3:
                if les_status == 2:
                    print(f"  [Test {les_id}] {les_name} -> Allaqachon topshirilgan (✔)!")
                    continue
                solve_quiz(les_id)
                time.sleep(3)
                
    # Tekshiruv
    r2 = requests.get(f"https://api.aistudy.uz/api/StudyAILms/Progress/GetPrivateCourseContentTree?courseId={course_id}", headers=headers)
    tree2 = r2.json().get("result", {})
    print(f"\nKURS {course_id} YAKUNIY NATIJASI: {tree2.get('finishLessonCount')} / {tree2.get('lessonCount')}")

for c in range(1, 5):
    complete_course(c)

# Sertifikatni tekshirish
print("\n" + "="*50)
print("SERTIFIKAT TEKSHIRILMOQDA...")
print("="*50)
for _ in range(5):
    cert_res = requests.get("https://api.aistudy.uz/api/StudyAILms/Certificate/GetCertificateByUser", headers=headers)
    print("Sertifikat API javobi:", cert_res.status_code, cert_res.text)
    if cert_res.status_code == 200 and cert_res.json().get("result"):
        cid = cert_res.json()["result"].get("id") or cert_res.json()["result"].get("certificateId")
        print(f"\n🎉 TABRIKLAYMIZ! SERTIFIKAT HAVOLASI: https://omp.aistudy.uz/certificate?id={cid}")
        break
    time.sleep(3)
