raw_data = """1,RAXMONOVA ZULAYHO ILHOMJON QIZI,2014-09-09,I-FR,806159,5-A
2,ISMANOV AXLIDIN AZIZJONOVICH,2015-08-13,PE,1507204,5-A
1,MIRZOKALONOVA SHUKRONA RASHIDJONOVNA,2015-05-04,III-CT,686484,5-A
2,SHAYMURODOV NURMUHAMMAD NODIRBEK O`G`LI,2015-03-03,T,985966,5-A
3,Nayko Ayko Aleksandrovna,2015-04-06,I-FR,872014,5-A
4,Raximov Saidamirbek Muzaffarovich,2015-02-24,I-FR,854351,5-A
5,SAYDALIYEVA SAID OLIMAXON POSHSHA OLIMXONOVNA,2014-08-08,T,48065699,5-A
6,MAXAMMADOV MIRZIYO AXMADJON O`G`LI,2015-09-30,I-FR,897155,5-A
7,BOLTABOYEVA MAFTUNA RAVSHANOVNA,2015-07-15,AB,8499911,5-A
8,DILMURODOVA OISHA JAXONGIR QIZI,2015-03-13,I-FR,854481,5-A
9,ALIYEV ALIMALIK DILSHOD O`G`LI,2015-08-27,T,1430873,5-A
10,ABDUKAXOROVA OSIYOXON ABDUG`AFUROVNA,2015-09-29,T,1522509,5-A
11,TURGUNOV AVAZBEK XASHIMDJON O`G`LI,2015-03-06,I-FR,854426,5-A
12,SAIDAKBAROV SAIDXON SAIDJALOLIDIN O`G`LI,2015-09-13,I-FR,972858,5-A
13,SIROJIDDINOV MUHAMMADISO ZUHRIDDIN O`G`LI,2015-05-16,I-FR,874171,5-A
14,SOTIVOLDIYEVA JASMINAXON JASURBEK QIZI,2015-07-21,I-FR,889332,5-A
15,TESHABOYEV SHOHJAHON MAXAMMADJON O`G`LI,2015-08-29,I-FR,914258,5-A
16,NURITDINOVA MUBINABONU FARRUX QIZI,2015-07-09,I-FR,889238,5-A
17,MIRZAYEVA AZIZA BAXTIYOROVNA,2015-09-17,I-FR,913052,5-A
18,TURGUNOVA FARZONA NURIDDINOVNA,2015-09-29,I-FR,913183,5-A
19,ORAZBEKOV ABDULLOH ASHIRBEK O`G`LI,2015-06-09,I-FR,872608,5-A
20,ABDUMUTALIBOVA SAMIRAXON MUMIN QIZI,2015-09-01,I-FR,913570,5-A
21,SAMINJONOV MUSTAFO NASIBULLO O`G`LI,2015-08-04,I-FR,920004,5-A
22,XABIBJONOVA GULYORAXON BOTIRJON QIZI,2015-05-21,I-FR,872439,5-A
23,ERGASHEV MUSTAFO MA`RUFJON O`G`LI,2015-08-28,I-FR,913303,5-A
24,RUSTAMOVA RUXSHONA DILMURODOVNA,2015-04-21,T,1102872,5-A
25,MADIYAROVA MADINA MASHXURBEKOVNA,2015-06-14,I-FR,872655,5-A
26,MUXIDINOV MUXAMMADSODIQ MURODULLOYEVICH,2015-07-12,T,1293348,5-A
27,SALIKAYEVA RUMIYA MARATOVNA,2015-03-25,I-FR,854583,5-A
28,SIROJIDDINOV SANJARBEK XAYRULLAYEVICH,2015-06-06,I-FR,872570,5-A
29,AZAMOV ABDULLOH SHAHBOZOVICH,2015-08-11,I-FR,889591,5-A
30,GAYNAZAROVA LIYA VALERYEVNA,2015-03-06,I-FR,854412,5-A"""

students_list = []
for line in raw_data.strip().splitlines():
    parts = [p.strip() for p in line.split(",")]
    if len(parts) >= 6:
        name = parts[1]
        raw_bdate = parts[2] # 2014-09-09
        # Convert YYYY-MM-DD -> DDMMYYYY
        bparts = raw_bdate.split("-")
        if len(bparts) == 3:
            bdate = f"{bparts[2]}{bparts[1]}{bparts[0]}"
        else:
            bdate = raw_bdate.replace("-", "").replace(".", "")
            
        seria = parts[3]
        raw_num = parts[4]
        num = raw_num.zfill(7) if len(raw_num) < 7 else raw_num
        sinf = parts[5]
        
        students_list.append({
            "name": name,
            "birthdate": bdate,
            "seria": seria,
            "number": num,
            "sinf": sinf
        })

import pprint
import re

with open("d:/uzbekcodersbot/5millionsertifikat/run_visual_test.py", "r", encoding="utf-8") as f:
    code = f.read()

# Replace STUDENTS = [...] in run_visual_test.py
formatted_students = "STUDENTS = " + pprint.pformat(students_list, indent=4, width=120)

pattern = r"STUDENTS\s*=\s*\[.*?\]"
new_code = re.sub(pattern, formatted_students, code, flags=re.DOTALL)

with open("d:/uzbekcodersbot/5millionsertifikat/run_visual_test.py", "w", encoding="utf-8") as f:
    f.write(new_code)

print(f"SUCCESS: {len(students_list)} ta o'quvchi run_visual_test.py ga muvaffaqiyatli kiritildi!")
