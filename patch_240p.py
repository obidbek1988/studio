with open("d:/uzbekcodersbot/5millionsertifikat/run_visual_test.py", "r", encoding="utf-8") as f:
    c = f.read()

target = 'page.add_init_script("window._sys_dt_bypass = true;")'
replacement = '''page.add_init_script("window._sys_dt_bypass = true;")
        # Kompyuterga nagruzka tushmasligi uchun: 240p sifati va ovozsiz rejim
        page.add_init_script("""
            setInterval(function() {
                var vids = document.querySelectorAll('video');
                for (var i = 0; i < vids.length; i++) {
                    vids[i].muted = true;
                    vids[i].volume = 0;
                }
                var btn240 = document.querySelector('button[data-plyr="quality"][value="240"]');
                if (btn240) btn240.click();
            }, 1000);
        """)'''

if target in c:
    c = c.replace(target, replacement, 1)
    with open("d:/uzbekcodersbot/5millionsertifikat/run_visual_test.py", "w", encoding="utf-8") as f:
        f.write(c)
    print("Muvaffaqiyatli qo'shildi: 240p va Mute rejimi")
else:
    print("Target topilmadi")
