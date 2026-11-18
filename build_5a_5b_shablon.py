# -*- coding: utf-8 -*-
"""
5-A va 5-B sinflari uchun to'liq, mukammal va tayyor shablon yaratish.
- Barcha mavjud sertifikatlar (29+ ta) moviy giperhavola va yashil fon bilan saqlanadi
- Barcha login va parollar moviy fon bilan saqlanadi
- 5-A va 5-B o'quvchilari tartibli joylashtiriladi
"""

import os, re, json, datetime
from pathlib import Path
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from process_5million_excel import normalize_student_key, clean_latin_slug, to_latin

BASE_DIR = Path("d:/5millionbot")
F_37 = BASE_DIR / "5-A_va_5-B_sinf_tozalangan_37_oquvchi_TAYYOR_28_SERTIFIKAT.xlsx"
F_MASTER = BASE_DIR / "Maktab_Barcha_Sinflar_5Million_Master_Shablon.xlsx"
F2_PATH = r"C:/Users/user/.gemini/antigravity/brain/0608055f-1cd8-402c-8fee-4a980c504efa/.user_uploaded/media_1794985490142_0b534e0d.xlsx"

def format_bdate(val):
    if not val: return ""
    if isinstance(val, (datetime.datetime, datetime.date)): return val.strftime("%d.%m.%Y")
    s = str(val).strip()
    m_iso = re.match(r'(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})', s)
    if m_iso:
        y, m, d = m_iso.groups()
        return f"{d.zfill(2)}.{m.zfill(2)}.{y}"
    m_uz = re.match(r'(\d{1,2})[-/.](\d{1,2})[-/.](\d{4})', s)
    if m_uz:
        d, m, y = m_uz.groups()
        return f"{d.zfill(2)}.{m.zfill(2)}.{y}"
    return s

def get_words(n):
    lat = to_latin(str(n or "")).lower().replace("dj", "j").replace("'", "").replace("`", "").replace("’", "").replace("ʻ", "")
    return [clean_latin_slug(w) for w in lat.split() if len(clean_latin_slug(w)) >= 2]

def is_same(n1, n2):
    w1, w2 = get_words(n1), get_words(n2)
    if len(w1) < 2 or len(w2) < 2: return False
    if w1[1] != w2[1]: return False
    return (w1[0] == w2[0]) or (len(w1[0]) >= 5 and len(w2[0]) >= 5 and (w1[0] in w2[0] or w2[0] in w1[0]))

def main():
    print("🚀 5-A va 5-B UCHUN MAXSUS TAYYOR SHABLON YARATILMOQDA...")
    
    # 1. Barcha 5-A va 5-B o'quvchilarini to'plash
    students = {} # key -> student dict

    # 1.1 F_37 faylidan (tayyor 29 ta sertifikat va loginlar bor)
    if F_37.exists():
        wb_37 = openpyxl.load_workbook(F_37, data_only=True)
        ws = wb_37.active
        for r in range(2, ws.max_row + 1):
            nm = ws.cell(r, 2).value
            bdate = ws.cell(r, 3).value
            ser = ws.cell(r, 4).value
            num = ws.cell(r, 5).value
            sinf = ws.cell(r, 6).value
            cert = ws.cell(r, 7).value
            log = ws.cell(r, 8).value
            pwd = ws.cell(r, 9).value
            if nm:
                nm_s = str(nm).strip()
                s_s = str(ser or "").strip()
                n_s = str(num or "").strip()
                cls_s = "5-B" if "5-B" in str(sinf or "").upper() or "5B" in str(sinf or "").upper() else "5-A"
                k = normalize_student_key(s_s, n_s) if (s_s and n_s) else nm_s.lower()
                c_val = str(cert or "").strip()
                if "certificate?id=" not in c_val and "Allaqachon" not in c_val:
                    c_val = ""
                students[k] = {
                    "name": nm_s,
                    "bdate": format_bdate(bdate),
                    "seria": s_s,
                    "num": n_s,
                    "sinf": cls_s,
                    "cert": c_val,
                    "login": str(log or "").strip(),
                    "pwd": str(pwd or "").strip()
                }

    # 1.2 Master fayldagi 5-A va 5-B o'quvchilari
    if F_MASTER.exists():
        wb_m = openpyxl.load_workbook(F_MASTER, data_only=True)
        for sname in ["5-A", "5-B"]:
            if sname in wb_m.sheetnames:
                ws = wb_m[sname]
                for r in range(2, ws.max_row + 1):
                    nm = ws.cell(r, 2).value
                    bdate = ws.cell(r, 3).value
                    ser = ws.cell(r, 4).value
                    num = ws.cell(r, 5).value
                    sinf = ws.cell(r, 6).value
                    cert = ws.cell(r, 7).value
                    log = ws.cell(r, 8).value
                    pwd = ws.cell(r, 9).value
                    if nm:
                        nm_s = str(nm).strip()
                        s_s = str(ser or "").strip()
                        n_s = str(num or "").strip()
                        k = normalize_student_key(s_s, n_s) if (s_s and n_s) else nm_s.lower()
                        # Agar mavjud bo'lsa yangilaymiz
                        matched_key = None
                        if k in students:
                            matched_key = k
                        else:
                            for sk, sv in students.items():
                                if is_same(nm_s, sv["name"]):
                                    matched_key = sk
                                    break
                        if matched_key:
                            rec = students[matched_key]
                            if not rec["cert"] and cert: rec["cert"] = str(cert).strip()
                            if not rec["login"] and log: rec["login"] = str(log).strip()
                            if not rec["pwd"] and pwd: rec["pwd"] = str(pwd).strip()
                            if not rec["seria"] and s_s: rec["seria"] = s_s
                            if not rec["num"] and n_s: rec["num"] = n_s
                        else:
                            students[k] = {
                                "name": nm_s,
                                "bdate": format_bdate(bdate),
                                "seria": s_s,
                                "num": n_s,
                                "sinf": sname,
                                "cert": str(cert or "").strip(),
                                "login": str(log or "").strip(),
                                "pwd": str(pwd or "").strip()
                            }

    # Ro'yxatni tartiblash (avval 5-A, keyin 5-B, har birida ism bo'yicha)
    st_list = list(students.values())
    st_list.sort(key=lambda x: (x["sinf"], clean_latin_slug(x["name"])))

    print(f"Jami 5-A va 5-B o'quvchilari: {len(st_list)} ta")
    certs_cnt = sum(1 for s in st_list if "certificate?id=" in str(s["cert"]))
    logins_cnt = sum(1 for s in st_list if s["login"] and s["pwd"] and not "certificate?id=" in str(s["cert"]))
    print(f"  - Sertifikati tayyor: {certs_cnt} ta")
    print(f"  - Logini bor: {logins_cnt} ta")
    print(f"  - Noldan o'tadigan: {len(st_list) - certs_cnt - logins_cnt} ta")

    # Excel fayl yaratish
    wb_out = openpyxl.Workbook()
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

    col_widths = {1: 6, 2: 38, 3: 16, 4: 12, 5: 14, 6: 10, 7: 44, 8: 26, 9: 18}

    # 1. Bosh faol varaq: "5-A va 5-B"
    ws_main = wb_out.active
    ws_main.title = "5-A va 5-B"
    ws_main.append(headers)
    for c in range(1, 10):
        cell = ws_main.cell(1, c)
        cell.font = header_font; cell.fill = header_fill; cell.alignment = center_align

    for idx, st in enumerate(st_list, 1):
        ws_main.append([
            idx, st["name"], st["bdate"], st["seria"], st["num"], st["sinf"],
            st["cert"], st["login"], st["pwd"]
        ])
        r_idx = idx + 1
        ws_main.cell(r_idx, 1).alignment = center_align
        ws_main.cell(r_idx, 2).alignment = left_align
        ws_main.cell(r_idx, 3).alignment = center_align
        ws_main.cell(r_idx, 4).alignment = center_align
        ws_main.cell(r_idx, 5).alignment = center_align
        ws_main.cell(r_idx, 6).alignment = center_align
        ws_main.cell(r_idx, 7).alignment = left_align
        ws_main.cell(r_idx, 8).alignment = left_align
        ws_main.cell(r_idx, 9).alignment = center_align

        for c in range(1, 10):
            cell = ws_main.cell(r_idx, c)
            cell.border = thin_border
            cell.font = normal_font

        if st["cert"] and "certificate?id=" in st["cert"]:
            c_cell = ws_main.cell(r_idx, 7)
            c_cell.font = cert_font
            c_cell.hyperlink = st["cert"]
            for c in range(1, 10): ws_main.cell(r_idx, c).fill = cert_fill
        elif st["login"] and st["pwd"]:
            for c in range(1, 10): ws_main.cell(r_idx, c).fill = login_fill

    for col_idx, width in col_widths.items():
        ws_main.column_dimensions[get_column_letter(col_idx)].width = width

    # 2. Alohida "5-A" va "5-B" varaqlari
    for target_cls in ["5-A", "5-B"]:
        ws_sub = wb_out.create_sheet(title=target_cls)
        ws_sub.append(headers)
        for c in range(1, 10):
            cell = ws_sub.cell(1, c)
            cell.font = header_font; cell.fill = header_fill; cell.alignment = center_align

        sub_list = [s for s in st_list if s["sinf"] == target_cls]
        for s_idx, st in enumerate(sub_list, 1):
            ws_sub.append([
                s_idx, st["name"], st["bdate"], st["seria"], st["num"], st["sinf"],
                st["cert"], st["login"], st["pwd"]
            ])
            r_idx = s_idx + 1
            ws_sub.cell(r_idx, 1).alignment = center_align
            ws_sub.cell(r_idx, 2).alignment = left_align
            ws_sub.cell(r_idx, 3).alignment = center_align
            ws_sub.cell(r_idx, 4).alignment = center_align
            ws_sub.cell(r_idx, 5).alignment = center_align
            ws_sub.cell(r_idx, 6).alignment = center_align
            ws_sub.cell(r_idx, 7).alignment = left_align
            ws_sub.cell(r_idx, 8).alignment = left_align
            ws_sub.cell(r_idx, 9).alignment = center_align

            for c in range(1, 10):
                cell = ws_sub.cell(r_idx, c)
                cell.border = thin_border
                cell.font = normal_font

            if st["cert"] and "certificate?id=" in st["cert"]:
                c_cell = ws_sub.cell(r_idx, 7)
                c_cell.font = cert_font
                c_cell.hyperlink = st["cert"]
                for c in range(1, 10): ws_sub.cell(r_idx, c).fill = cert_fill
            elif st["login"] and st["pwd"]:
                for c in range(1, 10): ws_sub.cell(r_idx, c).fill = login_fill

        for col_idx, width in col_widths.items():
            ws_sub.column_dimensions[get_column_letter(col_idx)].width = width

    wb_out.active = 0
    out_file = BASE_DIR / "5A_va_5B_tayyor_shablon.xlsx"
    wb_out.save(out_file)
    print(f"✅ Fayl tayyorlandi: {out_file}")

if __name__ == "__main__":
    main()
