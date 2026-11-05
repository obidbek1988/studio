with open("d:/uzbekcodersbot/5millionsertifikat/run_visual_test.py", "r", encoding="utf-8") as f:
    text = f.read()

# Dynamic password generation logic
old_pwd_code = '    default_password = "Maktab29"'
new_pwd_code = '''    # Har bir o'quvchiga unikal shaxsiy parol (Ismi + Yili)
    name_parts = [p.capitalize() for p in re.findall(r'[a-zA-Z]+', name)]
    first_name = name_parts[1] if len(name_parts) > 1 else (name_parts[0] if name_parts else "Oquvchi")
    birth_year = birthdate_digits[4:] if len(birthdate_digits) >= 8 else "2015"
    student_password = f"{first_name}{birth_year}"
    
    # Raxmonova Zulayho avval Maktab29 bilan ochilgan edi, boshqalar yangi shaxsiy parol bilan
    default_password = "Maktab29" if "raxmonova" in name.lower() else student_password'''

if old_pwd_code in text:
    text = text.replace(old_pwd_code, new_pwd_code, 1)
    with open("d:/uzbekcodersbot/5millionsertifikat/run_visual_test.py", "w", encoding="utf-8") as f:
        f.write(text)
    print("SUCCESS: Dynamic password logic added!")
else:
    print("ERROR: old_pwd_code not found")
