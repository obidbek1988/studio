import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import openpyxl

wb = openpyxl.load_workbook(r"C:\Users\user\Desktop\5mln 26-m 25 ta  30.03.2026.xlsx")
sheet = wb["o'quvchilar 9"]
for r in range(1, 10):
    vals = [sheet.cell(r, c).value for c in range(1, 12)]
    print(f"Row {r}:", vals)
