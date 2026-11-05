with open("d:/uzbekcodersbot/5millionsertifikat/run_visual_test.py", "r", encoding="utf-8") as f:
    text = f.read()

target = '        for attempt in range(1, 4):'
replacement = '''        # Agar o'quvchi allaqachon Excelda sertifikat olgan bo'lsa, o'tkazib yuboramiz
        excel_path = r"C:\\Users\\user\\Desktop\\5mln 26-m 25 ta  30.03.2026.xlsx"
        already_has_cert = False
        if os.path.exists(excel_path):
            try:
                wb_chk = openpyxl.load_workbook(excel_path, read_only=True)
                sh_chk = wb_chk["o'quvchilar 9"] if "o'quvchilar 9" in wb_chk.sheetnames else wb_chk.active
                for r in range(2, sh_chk.max_row + 1):
                    c_name = str(sh_chk.cell(r, 3).value or "").strip().lower()
                    c_link = str(sh_chk.cell(r, 4).value or "").strip()
                    if (student["name"].strip().lower() in c_name or c_name in student["name"].strip().lower()) and "certificate?id=" in c_link:
                        print(f"  [ALBATTA TAYYOR] {student['name']} ning sertifikati mavjud: {c_link}", flush=True)
                        print(f"  -> Qayta bajarilmaydi (SKIP). Keyingi o'quvchiga o'tilmoqda!\\n", flush=True)
                        already_has_cert = True
                        student_success = True
                        break
                wb_chk.close()
            except Exception:
                pass
                
        if already_has_cert:
            continue

        for attempt in range(1, 4):'''

if target in text:
    text = text.replace(target, replacement, 1)
    with open("d:/uzbekcodersbot/5millionsertifikat/run_visual_test.py", "w", encoding="utf-8") as f:
        f.write(text)
    print("SUCCESS: Skip completed students logic added!")
else:
    print("ERROR: target not found")
