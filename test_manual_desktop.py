import os
import sys
import openpyxl

os.environ["MANUAL_OTP"] = "1"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXCEL_PATH = os.path.join(BASE_DIR, "Lotincha_royxat_69_oquvchi.xlsx")

def main():
    print("\n" + "="*65)
    print("   🎓 5 MILLION PROMPTER - TEST VA ISHGA TUSHIRISH PANEL   ")
    print("="*65)
    print(f"📁 Excel fayl: {EXCEL_PATH}")

    if not os.path.exists(EXCEL_PATH):
        print(f"❌ Xatolik: {EXCEL_PATH} fayli topilmadi!")
        input("\nChiqish uchun Enter bosing...")
        return

    # O'quvchilarni o'qish
    wb = openpyxl.load_workbook(EXCEL_PATH, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    header = rows[0]
    students = [r for r in rows[1:] if r and any(r) and r[1]]

    print(f"👥 Jami yuklangan o'quvchilar: {len(students)} ta\n")
    print("Quyidagilardan birini tanlang:")
    print("1. Faqat 1-o'quvchini test qilish (TILABOLDIEV OYATULLA)")
    print("2. Barcha 69 ta o'quvchini ketma-ket avtomatik bajarish")
    print("3. Muayyan bitta o'quvchini tanlash (T/r raqami bo'yicha)")
    print("="*65)

    choice = input("\nTanlovingizni kiriting (1, 2 yoki 3) [Standart: 1]: ").strip()
    if not choice:
        choice = "1"

    from process_5million_excel import process_excel_order, process_single_student

    if choice == "1":
        first_st = students[0]
        name = first_st[1]
        bdate = str(first_st[2])
        seria = str(first_st[3])
        num = str(first_st[4])
        print(f"\n🚀 1-o'quvchi boshlanmoqda: {name} ({seria} {num})...")
        print("🌐 Brauzer ochiladi, Telegram kod so'ralganda shu yerga yozasiz!")
        
        student_dict = {
            "name": name,
            "birthdate": bdate,
            "seria": seria,
            "number": num,
            "sinf": "11-A"
        }
        ok, res_link, email, pwd = process_single_student(student_dict)
        print("\n" + "="*65)
        if ok and "certificate" in str(res_link):
            print(f"🎉 MUVAFFAQIYATLI YAKUNLANDI!")
            print(f"📜 Sertifikat havolasi: {res_link}")
            print(f"🔑 Login: {email} | Parol: {pwd}")
            try:
                wb_save = openpyxl.load_workbook(EXCEL_PATH)
                ws_save = wb_save.active
                ws_save.cell(2, 7).value = res_link
                ws_save.cell(2, 8).value = email
                ws_save.cell(2, 9).value = pwd
                wb_save.save(EXCEL_PATH)
                print("💾 Natija Excel faylga muvaffaqiyatli saqlandi!")
            except Exception as es:
                print(f"Excelga saqlashda xato: {es}")
        else:
            print(f"⚠️ Natija: {res_link}")
        print("="*65)

    elif choice == "2":
        print("\n🚀 Barcha o'quvchilar navbat bilan boshlanmoqda...")
        process_excel_order(EXCEL_PATH)

    elif choice == "3":
        print("\nO'quvchilar ro'yxati:")
        for idx, s in enumerate(students[:20], 1):
            print(f"{idx}. {s[1]} ({s[3]} {s[4]})")
        if len(students) > 20:
            print(f"... va yana {len(students)-20} ta o'quvchi")
        sel_idx = input(f"\nO'quvchi raqamini kiriting (1-{len(students)}): ").strip()
        try:
            s_num = int(sel_idx) - 1
            sel_st = students[s_num]
            st_dict = {
                "name": sel_st[1],
                "birthdate": str(sel_st[2]),
                "seria": str(sel_st[3]),
                "number": str(sel_st[4]),
                "sinf": str(sel_st[5] or "6-A")
            }
            print(f"\n🚀 {sel_st[1]} boshlanmoqda...")
            ok, res_link, email, pwd = process_single_student(st_dict)
            print("\n" + "="*65)
            if ok and "certificate" in str(res_link):
                print(f"🎉 SERTIFIKAT OLINDI: {res_link}")
            else:
                print(f"⚠️ Natija: {res_link}")
            print("="*65)
        except Exception as e:
            print(f"❌ Xato tanlov: {e}")

    input("\nJarayon yakunlandi. Chiqish uchun Enter bosing...")

if __name__ == "__main__":
    main()
