# -*- coding: utf-8 -*-
"""
MAKTAB BARCHA SINFLAR UCHUN MASTER 5 MILLION SHABLON YARATISH DASTURI (MUKAMMAL VA ANIQ)
- 5-A va 5-B kiritilgan, 5-V chiqarib tashlangan (Foydalanuvchi talabi)
- 11-A ning haqiqiy 26 ta o'quvchisi va ularning kechadan beri tekshirib bazaga saqlangan loginlari to'liq kiritilgan
- "Allaqachon ro'yxatdan o'tgan (Parol yo'q)" bo'lganlar aniq belgilanadi va bot 0 soniyada o'tkazib yuboradi
- Mavjud sertifikat havolalari aslo yo'qolmaydi (moviy giperhavola va yashil fon)
- Bot to'liq tushunadigan rasmiy 9 ta ustunli formatda
"""

import os
import re
import glob
import json
import datetime
from pathlib import Path
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from process_5million_excel import normalize_student_key, clean_latin_slug, to_latin

BASE_DIR = Path("d:/5millionbot")
F1_PATH = r"C:/Users/user/.gemini/antigravity/brain/0608055f-1cd8-402c-8fee-4a980c504efa/.user_uploaded/media_1794985482625_853ce809.xlsx"
F2_PATH = r"C:/Users/user/.gemini/antigravity/brain/0608055f-1cd8-402c-8fee-4a980c504efa/.user_uploaded/media_1794985490142_0b534e0d.xlsx"
F_11A_PATH = BASE_DIR / "11A_order.xlsx"

def format_bdate(val):
    if not val:
        return ""
    if isinstance(val, (datetime.datetime, datetime.date)):
        return val.strftime("%d.%m.%Y")
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

def class_sort_key(c_name):
    m = re.match(r'(\d+)\s*[-_]?\s*([a-zA-Zа-яА-Я]*)', str(c_name or ''))
    if m:
        num = int(m.group(1))
        letter = m.group(2).upper()
        trans = {'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G'}
        letter = trans.get(letter, letter)
        return (num, letter)
    return (999, str(c_name or 'Z'))

def get_words(n):
    lat = to_latin(str(n or "")).lower().replace("dj", "j").replace("'", "").replace("`", "").replace("’", "").replace("ʻ", "")
    return [clean_latin_slug(w) for w in lat.split() if len(clean_latin_slug(w)) >= 2]

def is_strict_same_student(n1, n2):
    w1 = get_words(n1)
    w2 = get_words(n2)
    if len(w1) < 2 or len(w2) < 2:
        return False
    s1, s2 = w1[0], w2[0] # Familiya
    i1, i2 = w1[1], w2[1] # Ism
    if i1 != i2:
        return False
    if s1 == s2:
        return True
    if len(s1) >= 5 and len(s2) >= 5 and (s1 in s2 or s2 in s1 or s1[:5] == s2[:5]):
        return True
    return False

def main():
    print("="*70, flush=True)
    print("🚀 MASTER SHABLON YARATISH (5-V CHIQARILGAN, 11-A HAQIQIY RO'YXAT BILAN)...", flush=True)
    print("="*70, flush=True)

    # 1. Barcha mavjud sertifikatlar va login/parollar ro'yxatini yig'ish
    known_records = []

    # 1.1 students_db.json dan
    db_file = BASE_DIR / "students_db.json"
    if db_file.exists():
        with open(db_file, "r", encoding="utf-8") as f:
            s_db = json.load(f)
        for k, v in s_db.items():
            cert = v.get("certificate") or v.get("cert_url") or ""
            log = v.get("login") or ""
            pwd = v.get("password") or ""
            nm = v.get("name") or ""
            ser = v.get("seria") or ""
            num = v.get("number") or ""
            status = v.get("status") or ""

            if status == "ALREADY_REGISTERED_NO_PASSWORD":
                if not cert:
                    cert = "Allaqachon ro'yxatdan o'tgan (Parol yo'q)"
                if not pwd:
                    pwd = "Parol yo'q"

            if cert or log:
                known_records.append({
                    "key": k,
                    "name": nm,
                    "seria": ser,
                    "num": num,
                    "cert": cert,
                    "login": log,
                    "pwd": pwd,
                    "status": status,
                    "source": "students_db.json"
                })

    # 1.2 File 2 dan (5-A va 5-B) - 5-V chiqarib tashlanadi!
    if os.path.exists(F2_PATH):
        wb2 = openpyxl.load_workbook(F2_PATH, data_only=True)
        for sname in wb2.sheetnames:
            if "5-V" in sname.upper() or "5V" in sname.upper() or "5 В" in sname.upper():
                continue
            ws = wb2[sname]
            for r in range(1, ws.max_row + 1):
                nm = ws.cell(r, 2).value
                cert = ws.cell(r, 4).value
                log = ws.cell(r, 5).value
                pwd = ws.cell(r, 6).value
                if nm and (cert or log):
                    known_records.append({
                        "key": None,
                        "name": str(nm).strip(),
                        "seria": "",
                        "num": "",
                        "cert": str(cert or "").strip(),
                        "login": str(log or "").strip(),
                        "pwd": str(pwd or "").strip(),
                        "status": "COMPLETED" if ("certificate?id=" in str(cert or "")) else "HAS_LOGIN",
                        "source": f"5-sinflar_{sname}"
                    })

    # 1.3 Papkadagi boshqa fayllardan
    for xl in glob.glob(str(BASE_DIR / "*.xlsx")):
        fname = os.path.basename(xl)
        if "Maktab_Barcha_Sinflar" in fname or "shablon_5million" in fname or "26m 4v" in fname:
            continue
        try:
            wb_x = openpyxl.load_workbook(xl, data_only=True)
            for sn in wb_x.sheetnames:
                if "5-V" in sn.upper() or "5V" in sn.upper() or "5 В" in sn.upper():
                    continue
                ws = wb_x[sn]
                h_vals = [str(ws.cell(1, c).value or '').lower() for c in range(1, 15)]
                c_cert = next((i+1 for i, v in enumerate(h_vals) if any(x in v for x in ['cert', 'sertifikat', 'link', 'havola'])), None)
                c_log = next((i+1 for i, v in enumerate(h_vals) if any(x in v for x in ['login', 'email'])), None)
                c_pwd = next((i+1 for i, v in enumerate(h_vals) if any(x in v for x in ['parol', 'password', 'kod'])), None)
                c_name = next((i+1 for i, v in enumerate(h_vals) if any(x in v for x in ['f.i.sh', 'fish', 'ism', 'name', 'fio'])), None)
                c_seria = next((i+1 for i, v in enumerate(h_vals) if any(x in v for x in ['seria', 'seriya', 'series'])), None)
                c_num = next((i+1 for i, v in enumerate(h_vals) if any(x in v for x in ['raqam', 'num', 'number'])), None)

                if not (c_name and (c_cert or c_log)):
                    continue

                for r in range(2, ws.max_row + 1):
                    nm = ws.cell(r, c_name).value if c_name else None
                    cert = ws.cell(r, c_cert).value if c_cert else None
                    log = ws.cell(r, c_log).value if c_log else None
                    pwd = ws.cell(r, c_pwd).value if c_pwd else None
                    ser = ws.cell(r, c_seria).value if c_seria else None
                    num = ws.cell(r, c_num).value if c_num else None

                    c_str = str(cert or "").strip()
                    l_str = str(log or "").strip()
                    p_str = str(pwd or "").strip()
                    if ("certificate?id=" in c_str) or ("@" in l_str and p_str):
                        k = normalize_student_key(ser, num) if (ser and num) else None
                        known_records.append({
                            "key": k,
                            "name": str(nm or "").strip(),
                            "seria": str(ser or "").strip(),
                            "num": str(num or "").strip(),
                            "cert": c_str if "certificate?id=" in c_str else "",
                            "login": l_str if "@" in l_str else "",
                            "pwd": p_str,
                            "status": "COMPLETED" if ("certificate?id=" in c_str) else "HAS_LOGIN",
                            "source": fname
                        })
        except Exception:
            pass

    print(f"✅ Barcha ma'lumotlar bazasi yig'ildi: {len(known_records)} ta qayd", flush=True)

    # Indekslash
    doc_index = {}
    name_index = {}

    for rec in known_records:
        rec_words = get_words(rec["name"])
        rec["words"] = rec_words
        rec_k = rec.get("key")
        if rec_k:
            if rec_k not in doc_index:
                doc_index[rec_k] = rec
            else:
                existing = doc_index[rec_k]
                if not existing.get("cert") and rec.get("cert"):
                    doc_index[rec_k] = rec
                elif not existing.get("login") and rec.get("login"):
                    doc_index[rec_k] = rec
        if len(rec_words) >= 2:
            s_lead = rec_words[0][:4]
            i_lead = rec_words[1]
            name_index.setdefault((s_lead, i_lead), []).append(rec)

    # 2. File 1 dan umumiy ro'yxatni yuklash (11-A va 5-V bundan mustasno)
    wb1 = openpyxl.load_workbook(F1_PATH, data_only=True)
    ws1 = wb1.active

    all_students = []

    for r in range(7, ws1.max_row + 1):
        name = ws1.cell(r, 1).value
        bdate = ws1.cell(r, 2).value
        seria = ws1.cell(r, 3).value
        num = ws1.cell(r, 4).value
        sinf = ws1.cell(r, 5).value

        if not name:
            continue

        sinf_str = str(sinf or "").strip()
        # 5-V chiqarib tashlanadi
        if any(v in sinf_str.upper() for v in ["5-V", "5 V", "5-В", "5 В"]):
            continue
        # 11-A ni File 1 dan olmaymiz, chunki uning haqiqiy 26 talik to'g'ri ro'yxatini pastda qo'shamiz!
        if any(v in sinf_str.upper() for v in ["11-A", "11 A", "11-А", "11 А"]):
            continue

        name_str = str(name).strip()
        seria_str = str(seria or "").strip()
        num_str = str(num or "").strip()
        bdate_str = format_bdate(bdate)

        k_doc = normalize_student_key(seria_str, num_str) if (seria_str and num_str) else None

        cert_val = ""
        login_val = ""
        pwd_val = ""

        if k_doc and k_doc in doc_index:
            rec = doc_index[k_doc]
            cert_val = rec.get("cert", "")
            login_val = rec.get("login", "")
            pwd_val = rec.get("pwd", "")

        if not cert_val and not login_val:
            st_words = get_words(name_str)
            if len(st_words) >= 2:
                s_lead = st_words[0][:4]
                i_lead = st_words[1]
                candidates = name_index.get((s_lead, i_lead), [])
                for rec in candidates:
                    if is_strict_same_student(name_str, rec["name"]):
                        cert_val = rec.get("cert", "")
                        login_val = rec.get("login", "")
                        pwd_val = rec.get("pwd", "")
                        if cert_val or login_val:
                            break

        all_students.append({
            "name": name_str,
            "bdate": bdate_str,
            "seria": seria_str,
            "num": num_str,
            "sinf": sinf_str or "Sinfi ko'rsatilmagan",
            "cert": cert_val,
            "login": login_val,
            "pwd": pwd_val
        })

    # 3. 11-A ning HAQIQIY 26 TA O'QUVCHISINI QO'SHISH (Bazada bor loginlar bilan birga)
    print("🎓 11-A sinfining haqiqiy 26 ta o'quvchisi va loginlari biriktirilmoqda...", flush=True)
    if os.path.exists(F_11A_PATH):
        wb_11a = openpyxl.load_workbook(F_11A_PATH, data_only=True)
        ws_11a = wb_11a.active
        for r in range(2, ws_11a.max_row + 1):
            nm = ws_11a.cell(r, 2).value
            bdate = ws_11a.cell(r, 3).value
            ser = ws_11a.cell(r, 4).value
            num = ws_11a.cell(r, 5).value
            cls = ws_11a.cell(r, 6).value

            if not nm:
                continue

            nm_str = str(nm).strip()
            ser_str = str(ser or "").strip()
            num_str = str(num or "").strip()
            bdate_str = format_bdate(bdate)

            k_doc = normalize_student_key(ser_str, num_str) if (ser_str and num_str) else None

            c_val = ""
            l_val = ""
            p_val = ""

            if k_doc and k_doc in doc_index:
                rec = doc_index[k_doc]
                c_val = rec.get("cert", "")
                l_val = rec.get("login", "")
                p_val = rec.get("pwd", "")

            if not c_val and not l_val:
                st_words = get_words(nm_str)
                if len(st_words) >= 2:
                    candidates = name_index.get((st_words[0][:4], st_words[1]), [])
                    for rec in candidates:
                        if is_strict_same_student(nm_str, rec["name"]):
                            c_val = rec.get("cert", "")
                            l_val = rec.get("login", "")
                            p_val = rec.get("pwd", "")
                            if c_val or l_val:
                                break

            all_students.append({
                "name": nm_str,
                "bdate": bdate_str,
                "seria": ser_str,
                "num": num_str,
                "sinf": "11-A",
                "cert": c_val,
                "login": l_val,
                "pwd": p_val
            })

    # Statistika
    matched_certs_count = sum(1 for s in all_students if "certificate?id=" in str(s["cert"] or ""))
    already_reg_count = sum(1 for s in all_students if "Allaqachon" in str(s["cert"] or ""))
    matched_logins_count = sum(1 for s in all_students if s["login"] and s["pwd"] and s["pwd"] != "Parol yo'q")

    print(f"📊 Jami o'quvchilar: {len(all_students)} ta", flush=True)
    print(f"🎓 Sertifikati tayyor: {matched_certs_count} ta", flush=True)
    print(f"⚠️ Allaqachon ro'yxatdan o'tganlar (Login bor, Parol yo'q): {already_reg_count} ta", flush=True)
    print(f"🔑 Kirishga tayyor login/parolli: {matched_logins_count} ta", flush=True)

    # 4. Sinfma-sinf tartiblash (1-A dan 11-V gacha)
    print("🔄 Sinfma-sinf tartiblanmoqda...", flush=True)
    all_students.sort(key=lambda x: (class_sort_key(x["sinf"]), clean_latin_slug(x["name"])))

    # 5. Master Excel faylini yaratish
    wb_out = openpyxl.Workbook()

    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    
    cert_font = Font(name="Calibri", size=10, color="0000FF", underline="single")
    cert_fill = PatternFill(start_color="E2EFDA", end_color="E2EFDA", fill_type="solid") # Yashil (Sertifikat tayyor)
    login_fill = PatternFill(start_color="DDEBF7", end_color="DDEBF7", fill_type="solid") # Moviy (Login/Parol bor)
    already_fill = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid") # Sariq (Allaqachon ro'yxatdan o'tgan)
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
        "T/r",
        "F.I.SH (Familiya Ism Sharif)",
        "Tug'ilgan sana (KK.OO.YYYY)",
        "Metrika seriyasi",
        "Metrika raqami",
        "Sinf",
        "Sertifikat havolasi",
        "Login (Email)",
        "Parol"
    ]

    col_widths = {
        1: 6,   # T/r
        2: 38,  # F.I.SH
        3: 16,  # Sana
        4: 12,  # Seriya
        5: 14,  # Raqam
        6: 10,  # Sinf
        7: 44,  # Sertifikat havolasi
        8: 26,  # Login
        9: 18   # Parol
    }

    # 5.1 Bosh faol varaq: "Barcha Sinflar" (Bot aynan shuni o'qiydi!)
    ws_main = wb_out.active
    ws_main.title = "Barcha Sinflar"

    ws_main.append(headers)
    for col_idx in range(1, 10):
        cell = ws_main.cell(row=1, column=col_idx)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_align

    for idx, st in enumerate(all_students, 1):
        ws_main.append([
            idx,
            st["name"],
            st["bdate"],
            st["seria"],
            st["num"],
            st["sinf"],
            st["cert"],
            st["login"],
            st["pwd"]
        ])
        row_idx = idx + 1

        ws_main.cell(row_idx, 1).alignment = center_align
        ws_main.cell(row_idx, 2).alignment = left_align
        ws_main.cell(row_idx, 3).alignment = center_align
        ws_main.cell(row_idx, 4).alignment = center_align
        ws_main.cell(row_idx, 5).alignment = center_align
        ws_main.cell(row_idx, 6).alignment = center_align
        ws_main.cell(row_idx, 7).alignment = left_align
        ws_main.cell(row_idx, 8).alignment = left_align
        ws_main.cell(row_idx, 9).alignment = center_align

        for c in range(1, 10):
            cell = ws_main.cell(row_idx, c)
            cell.border = thin_border
            cell.font = normal_font

        if st["cert"] and "certificate?id=" in st["cert"]:
            c_cell = ws_main.cell(row_idx, 7)
            c_cell.font = cert_font
            c_cell.hyperlink = st["cert"]
            for c in range(1, 10):
                ws_main.cell(row_idx, c).fill = cert_fill
        elif "Allaqachon" in str(st["cert"] or ""):
            for c in range(1, 10):
                ws_main.cell(row_idx, c).fill = already_fill
        elif st["login"] and st["pwd"]:
            for c in range(1, 10):
                ws_main.cell(row_idx, c).fill = login_fill

    for col_idx, width in col_widths.items():
        col_letter = get_column_letter(col_idx)
        ws_main.column_dimensions[col_letter].width = width

    # 5.2 Har bir sinf uchun alohida varaqlar (5-V yo'q)
    unique_classes = []
    for st in all_students:
        if st["sinf"] not in unique_classes:
            unique_classes.append(st["sinf"])

    print(f"📑 {len(unique_classes)} ta sinf varaqlari to'ldirilmoqda...", flush=True)
    for cls in unique_classes:
        clean_sheet_title = re.sub(r'[/\\?*:[\]]', '_', cls)[:30]
        ws_cls = wb_out.create_sheet(title=clean_sheet_title)
        ws_cls.append(headers)
        for col_idx in range(1, 10):
            cell = ws_cls.cell(row=1, column=col_idx)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = center_align

        cls_students = [s for s in all_students if s["sinf"] == cls]
        for c_idx, st in enumerate(cls_students, 1):
            ws_cls.append([
                c_idx,
                st["name"],
                st["bdate"],
                st["seria"],
                st["num"],
                st["sinf"],
                st["cert"],
                st["login"],
                st["pwd"]
            ])
            r_idx = c_idx + 1
            ws_cls.cell(r_idx, 1).alignment = center_align
            ws_cls.cell(r_idx, 2).alignment = left_align
            ws_cls.cell(r_idx, 3).alignment = center_align
            ws_cls.cell(r_idx, 4).alignment = center_align
            ws_cls.cell(r_idx, 5).alignment = center_align
            ws_cls.cell(r_idx, 6).alignment = center_align
            ws_cls.cell(r_idx, 7).alignment = left_align
            ws_cls.cell(r_idx, 8).alignment = left_align
            ws_cls.cell(r_idx, 9).alignment = center_align

            for c in range(1, 10):
                cell = ws_cls.cell(r_idx, c)
                cell.border = thin_border
                cell.font = normal_font

            if st["cert"] and "certificate?id=" in st["cert"]:
                c_cell = ws_cls.cell(r_idx, 7)
                c_cell.font = cert_font
                c_cell.hyperlink = st["cert"]
                for c in range(1, 10):
                    ws_cls.cell(r_idx, c).fill = cert_fill
            elif "Allaqachon" in str(st["cert"] or ""):
                for c in range(1, 10):
                    ws_cls.cell(r_idx, c).fill = already_fill
            elif st["login"] and st["pwd"]:
                for c in range(1, 10):
                    ws_cls.cell(r_idx, c).fill = login_fill

        for col_idx, width in col_widths.items():
            col_letter = get_column_letter(col_idx)
            ws_cls.column_dimensions[col_letter].width = width

    # Asosiy varaqni faol qilamiz (index 0)
    wb_out.active = 0

    out_file = BASE_DIR / "Maktab_Barcha_Sinflar_5Million_Master_Shablon.xlsx"
    wb_out.save(out_file)
    wb_out.save(BASE_DIR / "shablon_5million.xlsx")

    # Alohida 11-A shablonini ham yangilab qo'yamiz
    wb_11a_out = openpyxl.Workbook()
    ws_11_single = wb_11a_out.active
    ws_11_single.title = "11-A"
    ws_11_single.append(headers)
    for col_idx in range(1, 10):
        cell = ws_11_single.cell(row=1, column=col_idx)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_align

    st_11a = [s for s in all_students if s["sinf"] == "11-A"]
    for idx_11, s in enumerate(st_11a, 1):
        ws_11_single.append([
            idx_11, s["name"], s["bdate"], s["seria"], s["num"], s["sinf"], s["cert"], s["login"], s["pwd"]
        ])
        r_num = idx_11 + 1
        for c in range(1, 10):
            cell = ws_11_single.cell(r_num, c)
            cell.border = thin_border
            cell.font = normal_font
            if "Allaqachon" in str(s["cert"] or ""):
                cell.fill = already_fill
            elif s["login"] and s["pwd"]:
                cell.fill = login_fill
    for col_idx, width in col_widths.items():
        col_letter = get_column_letter(col_idx)
        ws_11_single.column_dimensions[col_letter].width = width
    wb_11a_out.save(BASE_DIR / "11A_tayyor_shablon.xlsx")

    print("\n" + "="*70, flush=True)
    print(f"🎉 MASTER SHABLON MUVAFFAQIYATLI YARATILDI!", flush=True)
    print(f"📁 Asosiy fayl: {out_file}", flush=True)
    print(f"📁 Alohida 11-A fayli: {BASE_DIR / '11A_tayyor_shablon.xlsx'}", flush=True)
    print(f"👥 Jami o'quvchilar: {len(all_students)} ta", flush=True)
    print(f"🏫 Jami sinflar: {len(unique_classes)} ta varaq (5-V butunlay olib tashlandi)", flush=True)
    print(f"🎓 Sertifikati tayyor (Havolasi bor): {matched_certs_count} ta (Yashil)", flush=True)
    print(f"⚠️ Allaqachon ro'yxatdan o'tganlar (Login yozilgan, 0s skip): {already_reg_count} ta (Sariq)", flush=True)
    print(f"🔑 Kirishga tayyor (Login/Parolli): {matched_logins_count} ta (Moviy)", flush=True)
    print(f"🆕 Noldan o'tadigan yangilar: {len(all_students) - matched_certs_count - already_reg_count - matched_logins_count} ta", flush=True)
    print("="*70, flush=True)

if __name__ == "__main__":
    main()
