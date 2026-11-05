import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import openpyxl

wb = openpyxl.load_workbook(r"C:\Users\user\Desktop\5mln 26-m 25 ta  30.03.2026.xlsx")
sheet = wb.active
print("Sheet title:", sheet.title)

for r in range(1, min(10, sheet.max_row + 1)):
    row_vals = [sheet.cell(r, c).value for c in range(1, min(12, sheet.max_column + 1))]
    print(f"Row {r}:", row_vals)
