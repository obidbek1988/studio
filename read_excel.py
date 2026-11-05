import sys
import openpyxl

sys.stdout.reconfigure(encoding='utf-8')
wb = openpyxl.load_workbook(r'C:\Users\user\Desktop\5mln 26-m 25 ta  30.03.2026.xlsx')
sheet = wb["o'quvchilar 9"]
for r in range(1, 15):
    row_vals = [str(sheet.cell(r, c).value) for c in range(1, 8)]
    print(f"Row {r}:", " | ".join(row_vals))
