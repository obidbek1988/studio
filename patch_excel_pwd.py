with open("d:/uzbekcodersbot/5millionsertifikat/run_visual_test.py", "r", encoding="utf-8") as f:
    text = f.read()

# Update save_cert_to_excel signature and body
old_save_def = '''def save_cert_to_excel(student_name, cert_link):'''
new_save_def = '''def save_cert_to_excel(student_name, cert_link, login_email="", login_pwd=""):'''

text = text.replace(old_save_def, new_save_def, 1)

old_write_cell = '''                sheet.cell(r, 4).value = cert_link'''
new_write_cell = '''                sheet.cell(r, 4).value = cert_link
                if login_email: sheet.cell(r, 5).value = login_email
                if login_pwd: sheet.cell(r, 6).value = login_pwd'''

text = text.replace(old_write_cell, new_write_cell, 1)

old_call = '''            save_cert_to_excel(name, cert_link)'''
new_call = '''            save_cert_to_excel(name, cert_link, target_email, default_password)'''

text = text.replace(old_call, new_call, 1)

with open("d:/uzbekcodersbot/5millionsertifikat/run_visual_test.py", "w", encoding="utf-8") as f:
    f.write(text)

print("SUCCESS: Excel login/password saving added!")
