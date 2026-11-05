with open("d:/uzbekcodersbot/5millionsertifikat/run_visual_test.py", "r", encoding="utf-8") as f:
    text = f.read()

# 1. Fix get_telegram_verification_code regex
old_regex = "m = re.search(r'KOD:\s*(\d{6})', out_text)"
new_regex = "m = re.search(r'(\d{6})', out_text)"
text = text.replace(old_regex, new_regex)

# 2. Fix code input filling with dispatchEvent + sequential typing
old_code_fill = '''            print(f"Telegram tasdiqlash kodi kiritilmoqda: [{code}]", flush=True)
            code_inputs = page.locator(".verification-input, input[maxlength='1']")
            if code_inputs.count() >= 6:
                for idx_d, digit in enumerate(code[:6]):
                    code_inputs.nth(idx_d).fill(digit)
                    time.sleep(0.1)
            else:
                page.locator("input[type='text']").last.fill(code)'''

new_code_fill = '''            print(f"Telegram tasdiqlash kodi kiritilmoqda: [{code}]", flush=True)
            page.evaluate("""(code) => {
                const inputs = document.querySelectorAll('.verification-input, input[maxlength="1"]');
                for (let i = 0; i < Math.min(6, inputs.length); i++) {
                    inputs[i].focus();
                    inputs[i].value = code[i];
                    inputs[i].dispatchEvent(new Event('input', { bubbles: true }));
                    inputs[i].dispatchEvent(new Event('change', { bubbles: true }));
                }
            }""", code)
            time.sleep(0.5)
            code_inputs = page.locator(".verification-input, input[maxlength='1']")
            if code_inputs.count() >= 6:
                for idx_d, digit in enumerate(code[:6]):
                    try:
                        code_inputs.nth(idx_d).click()
                        code_inputs.nth(idx_d).fill(digit)
                        time.sleep(0.1)
                    except Exception:
                        pass
            else:
                try:
                    page.locator("input[type='text']").last.fill(code)
                except Exception:
                    pass'''

text = text.replace(old_code_fill, new_code_fill)

# 3. Nayko Ayko Aleksandrovnani 1-o'ringa qo'yish
# Find Nayko in STUDENTS
import re
nayko_obj = {
    'birthdate': '06042015',
    'name': 'Nayko Ayko Aleksandrovna',
    'number': '0872014',
    'seria': 'I-FR',
    'sinf': '5-A'
}

# We can reorder STUDENTS so Nayko is first!
import pprint
from run_visual_test import STUDENTS

reordered_students = []
# Add Nayko first
for s in STUDENTS:
    if "nayko" in s["name"].lower():
        reordered_students.append(s)
        break

# Add remaining
for s in STUDENTS:
    if "nayko" not in s["name"].lower():
        reordered_students.append(s)

formatted_students = "STUDENTS = " + pprint.pformat(reordered_students, indent=4, width=120)
pattern = r"STUDENTS\s*=\s*\[.*?\]"
text = re.sub(pattern, formatted_students, text, flags=re.DOTALL)

with open("d:/uzbekcodersbot/5millionsertifikat/run_visual_test.py", "w", encoding="utf-8") as f:
    f.write(text)

print("SUCCESS: Regex tuzatildi, kod kiritish mukammallashtirildi va Nayko 1-o'ringa qo'yildi!")
