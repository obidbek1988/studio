import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import openpyxl

wb = openpyxl.load_workbook(r"C:\Users\user\Desktop\5mln 26-m 25 ta  30.03.2026.xlsx")
print("Sheets:", wb.sheetnames)
for name in wb.sheetnames:
    sheet = wb[name]
    print(f"Sheet '{name}': {sheet.max_row} rows")
