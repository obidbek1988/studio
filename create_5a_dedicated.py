# -*- coding: utf-8 -*-
"""
5-A SINFI UCHUN MAXSUS TAYYOR SHABLON YARATISH:
- Sertifikati tayyor bo'lganlar (Yashil, moviy bosiladigan giperhavola bilan)
- Foydalanuvchi yuborgan Login va Paroli bor o'quvchilar (Moviy fon, Login va Parol to'ldirilgan)
- Hujjati bor lekin noldan o'tadiganlar (Oq fon, metrika ma'lumotlari bilan)
"""

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from process_5million_excel import clean_latin_slug

BASE_FILE = "d:/5millionbot/5A_va_5B_tayyor_shablon.xlsx"
OUT_FILE = "d:/5millionbot/5A_sinf_tayyor_shablon.xlsx"

# 1. Mavjud 5-A faylidan o'quvchilarni olish
wb_in = openpyxl.load_workbook(BASE_FILE, data_only=True)
ws_in = wb_in["5-A"]

students_with_cert = []
students_with_doc_only = []

for r in range(2, ws_in.max_row + 1):
    nm = ws_in.cell(r, 2).value
    bdate = ws_in.cell(r, 3).value
    ser = ws_in.cell(r, 4).value
    num = ws_in.cell(r, 5).value
    cls = ws_in.cell(r, 6).value or "5-A"
    cert = str(ws_in.cell(r, 7).value or "").strip()
    log = str(ws_in.cell(r, 8).value or "").strip()
    pwd = str(ws_in.cell(r, 9).value or "").strip()
    if not nm: continue

    st = {
        "name": str(nm).strip(),
        "bdate": str(bdate or "").strip(),
        "seria": str(ser or "").strip(),
        "num": str(num or "").strip(),
        "sinf": "5-A",
        "cert": cert,
        "login": log,
        "pwd": pwd
    }
    if "certificate?id=" in cert:
        students_with_cert.append(st)
    else:
        students_with_doc_only.append(st)

# 2. Foydalanuvchi hozir tashlagan 15 ta Login-Parolli o'quvchilar
pasted_15 = [
    ("Maxamadjonov Yaxyobek", "Yahyobek282015", "Maktab28"),
    ("Abdulazizova Iymonaxon", "Iymonaxon282015", "Maktab28"),
    ("Muhammadjonova Muazzambonu", "Muazzambonu2015", "Maktab28"),
    ("Shokirjonova Ziyoda", "Ziyodaxon282015", "Maktab28"),
    ("Ne'matjonov Muhammadjon", "Muhammadjon201528", "Maktab28"),
    ("Nabijonova Muattarxon", "Muattarxon282015", "Maktab28"),
    ("Adxamova Xolidaxon", "Xolidaxon282015", "Maktab28"),
    ("Mamajonov Temur", "Temur282015", "Maktab28"),
    ("Nurmatova Mohidil", "Mohidil282015", "Maktab28"),
    ("Ababakirova Mohinur", "Mohinur282015", "Maktab28"),
    ("Anvarjonov Shohijaxon", "Anvarjonov282015", "Maktab28"),
    ("Yuldashev Zafarbek", "Yuldashev282015", "Maktab28"),
    ("Salimboyeva Muslimaxon", "Muslimaxon282015", "Maktab28"),
    ("O'ktamjonov Boburbek", "Boburbek282015", "Maktab28"),
    ("Muhiddinov Azizbek", "Azizbek282015", "Maktab28")
]

students_with_login_only = []
for p_nm, p_log, p_pwd in pasted_15:
    students_with_login_only.append({
        "name": p_nm,
        "bdate": "",
        "seria": "",
        "num": "",
        "sinf": "5-A",
        "cert": "",
        "login": p_log,
        "pwd": p_pwd
    })

# Jami ro'yxatni shakllantirish:
# 1. Sertifikati borlar (yashil)
# 2. Login-paroli borlar (moviy)
# 3. Hujjati bor noldan o'tadiganlar (oq)
all_final = students_with_cert + students_with_login_only + students_with_doc_only

# Workbook yaratish
wb_out = openpyxl.Workbook()
ws_out = wb_out.active
ws_out.title = "5-A Sinf"

header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")

cert_font = Font(name="Calibri", size=10, color="0000FF", underline="single")
cert_fill = PatternFill(start_color="E2EFDA", end_color="E2EFDA", fill_type="solid") # Yashil
login_fill = PatternFill(start_color="DDEBF7", end_color="DDEBF7", fill_type="solid") # Moviy
normal_font = Font(name="Calibri", size=10)

thin_border = Border(
    left=Side(style='thin', color='D9D9D9'),
    right=Side(style='thin', color='D9D9D9'),
    top=Side(style='thin', color='D9D9D9'),
    bottom=Side(style='thin', color='D9D9D9')
)
center_align = Alignment(horizontal="center", vertical="center")
left_align = Alignment(horizontal="left", vertical="center")

headers = [
    "T/r", "F.I.SH (Familiya Ism Sharif)", "Tug'ilgan sana (KK.OO.YYYY)",
    "Metrika seriyasi", "Metrika raqami", "Sinf", "Sertifikat havolasi",
    "Login (Email)", "Parol"
]

ws_out.append(headers)
for c in range(1, 10):
    cell = ws_out.cell(1, c)
    cell.font = header_font
    cell.fill = header_fill
    cell.alignment = center_align

for idx, st in enumerate(all_final, 1):
    ws_out.append([
        idx, st["name"], st["bdate"], st["seria"], st["num"], st["sinf"],
        st["cert"], st["login"], st["pwd"]
    ])
    r_idx = idx + 1
    ws_out.cell(r_idx, 1).alignment = center_align
    ws_out.cell(r_idx, 2).alignment = left_align
    ws_out.cell(r_idx, 3).alignment = center_align
    ws_out.cell(r_idx, 4).alignment = center_align
    ws_out.cell(r_idx, 5).alignment = center_align
    ws_out.cell(r_idx, 6).alignment = center_align
    ws_out.cell(r_idx, 7).alignment = left_align
    ws_out.cell(r_idx, 8).alignment = left_align
    ws_out.cell(r_idx, 9).alignment = center_align

    for c in range(1, 10):
        cell = ws_out.cell(r_idx, c)
        cell.border = thin_border
        cell.font = normal_font

    if st["cert"] and "certificate?id=" in st["cert"]:
        c_cell = ws_out.cell(r_idx, 7)
        c_cell.font = cert_font
        c_cell.hyperlink = st["cert"]
        for c in range(1, 10):
            ws_out.cell(r_idx, c).fill = cert_fill
    elif st["login"] and st["pwd"]:
        for c in range(1, 10):
            ws_out.cell(r_idx, c).fill = login_fill

col_widths = {1: 6, 2: 38, 3: 16, 4: 12, 5: 14, 6: 10, 7: 44, 8: 26, 9: 18}
for col_idx, width in col_widths.items():
    col_letter = get_column_letter(col_idx)
    ws_out.column_dimensions[col_letter].width = width

wb_out.save(OUT_FILE)
print(f"🎉 5-A SINFI SHABLONI MUVAFFAQIYATLI YARATILDI!")
print(f"📁 Fayl manzili: {OUT_FILE}")
print(f"👥 Jami: {len(all_final)} ta o'quvchi")
print(f"  - 🎓 Sertifikati tayyor (Havolasi bor): {len(students_with_cert)} ta (Yashil)")
print(f"  - 🔑 Login va Paroli bor: {len(students_with_login_only)} ta (Moviy)")
print(f"  - ⚪ Noldan o'tadigan: {len(students_with_doc_only)} ta (Oq)")
