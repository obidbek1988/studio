with open("d:/uzbekcodersbot/5millionsertifikat/run_visual_test.py", "r", encoding="utf-8") as f:
    text = f.read()

text = text.replace('print(f"\n" + "="*55, flush=True)', 'print("\\n" + "="*55, flush=True)')
text = text.replace('print(f"\n[Modul', 'print(f"\\n[Modul')
text = text.replace('print(f"\n   [TEST:', 'print(f"\\n   [TEST:')

with open("d:/uzbekcodersbot/5millionsertifikat/run_visual_test.py", "w", encoding="utf-8") as f:
    f.write(text)

print("FIXED")
