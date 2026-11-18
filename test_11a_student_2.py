# -*- coding: utf-8 -*-
"""
11-A SINF 2-O'QUVCHINI TEST QILISH DASTURI
(Абдуллаева Шукуронахон Ойбек қизи, AE 5073439, 17.11.2009)
"""

import os
import sys
import time
import json
import re

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

# Qo'lda Telegram kod kiritish rejimini yoqish
os.environ["MANUAL_OTP"] = "1"
os.environ["HEADLESS"] = "0"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def main():
    print("\n" + "="*70)
    print("   🎯 11-A SINF: 2-O'QUVCHINI RO'YXATDAN O'TKAZISH VA TEST PANEL   ")
    print("="*70)
    print("👤 O'quvchi: Абдуллаева Шукуронахон Ойбек қизи")
    print("📄 Hujjat: AE 5073439")
    print("📅 Tug'ilgan sana: 17.11.2009")
    print("🏫 Sinf: 11-A")
    print("="*70)
    print("🌐 Jonli Chrome brauzeri ochilmoqda...")
    print("📝 1-qadam (Pasport/Tug'ilgan sana) va 2-qadam (Login/Parol) avtomatik to'ldiriladi.")
    print("📩 3-qadamda Telegram tasdiqlash kodi so'ralganda shu konsolga yozasiz!")
    print("="*70 + "\n")

    student_data = {
        "name": "Абдуллаева Шукуронахон Ойбек қизи",
        "birthdate": "17.11.2009",
        "seria": "AE",
        "number": "5073439",
        "sinf": "11-A"
    }

    from process_5million_excel import process_single_student

    try:
        ok, res_link, email, pwd = process_single_student(student_data)
        
        print("\n" + "="*70)
        if ok and email:
            print("🎉 MUVAFFAQIYATLI YAKUNLANDI!")
            print(f"🔑 Login (Email): {email}")
            print(f"🔒 Parol: {pwd}")
            print(f"📜 Sertifikat/Havola: {res_link}")
            print("="*70)
            
            # Bazani va 11A_order.xlsx ni yangilash
            try:
                import openpyxl
                excel_file = os.path.join(BASE_DIR, "11A_order.xlsx")
                if os.path.exists(excel_file):
                    wb = openpyxl.load_workbook(excel_file)
                    ws = wb.active
                    # 2-o'quvchi qatori = row 3
                    ws.cell(row=3, column=7, value=str(res_link or ""))
                    ws.cell(row=3, column=8, value=str(email or ""))
                    ws.cell(row=3, column=9, value=str(pwd or ""))
                    wb.save(excel_file)
                    print(f"💾 Natijalar 11A_order.xlsx faylining 2-qatoriga saqlandi!")
            except Exception as e_s:
                print(f"[EXCEL SAVE ERROR] {e_s}")
        else:
            print(f"⚠️ Natija: ok={ok}, res={res_link}")
            print("="*70)
    except Exception as e:
        print(f"❌ Xatolik yuz berdi: {e}")
        import traceback
        traceback.print_exc()

    print("\nBrauzer va konsol yopilmasligi uchun Enter bosing...")
    input()

if __name__ == "__main__":
    main()
