with open("d:/uzbekcodersbot/5millionsertifikat/run_visual_test.py", "r", encoding="utf-8") as f:
    text = f.read()

# Replace date entry and error handling to support swapped date fallback
old_block = '''        page.locator("input#seria, input[formcontrolname='seria']").fill(seria)
        page.locator("input#number, input[formcontrolname='number']").fill(number)
        
        birth_input = page.locator("input[formcontrolname='birthdate'], input.p-inputtext").first
        birth_input.click()
        birth_input.fill("")
        birth_input.press_sequentially(birthdate_digits, delay=60)
        birth_input.press("Enter")
        birth_input.press("Tab")
        print(f"Metrika ({seria} {number}) va sana kiritildi!", flush=True)
        time.sleep(1.5)
        
        handle_recaptcha(page)
        time.sleep(1.5)
        
        print("'Yuborish' tugmasi bosilmoqda...", flush=True)
        page.evaluate("""() => {
            const btn = document.querySelector('button[type="submit"]') || Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Yuborish'));
            if (btn) {
                btn.removeAttribute('disabled');
                btn.click();
            }
        }""")
        
        target_email = generated_email
        is_already_registered = False
        is_new_student = False
        has_error = False
        
        print("Natija kutilmoqda va tekshirilmoqda...", flush=True)
        for sec in range(1, 15):
            time.sleep(1)
            content = page.content()
            u_input = page.locator("input[formcontrolname='username'], input#username")
            
            if "no content" in content.lower():
                has_error = True
                print(f"[{sec}s] SAYT XATOLIGI (GCP): Davlat bazasida bu o'quvchi topilmadi (No content)!", flush=True)
                break
                
            toast = page.locator(".p-toast-message, .p-toast-detail, .p-toast-summary, div[role='alert']")
            if toast.count() > 0:
                t_text = toast.first.inner_text().lower()
                if "no content" in t_text or "topilmadi" in t_text:
                    has_error = True
                    print(f"[{sec}s] SAYT XATOLIGI: {t_text}", flush=True)
                    break
            
            if "allaqachon" in content.lower():
                is_already_registered = True
                print(f"[{sec}s] O'quvchi allaqachon ro'yxatdan o'tgan ekan!", flush=True)
                try:
                    email_elem = page.locator(".text-main-primary, span, p").filter(has_text="@gmail.com").first
                    if email_elem.count() > 0:
                        txt = email_elem.inner_text().strip()
                        if "@" in txt:
                            target_email = txt
                except Exception:
                    pass
                break
            elif u_input.count() > 0 and u_input.first.is_visible():
                is_new_student = True
                print(f"[{sec}s] YANGI O'QUVCHI! 2-bosqich ochildi!", flush=True)
                break'''

new_block = '''        # Sana variantlari (Asosiy va Kun/Oy almashgan zaxira variant)
        date_variants = [birthdate_digits]
        d_p1, d_p2, d_yr = birthdate_digits[:2], birthdate_digits[2:4], birthdate_digits[4:]
        if d_p1.isdigit() and d_p2.isdigit() and int(d_p1) <= 12 and int(d_p2) <= 12 and d_p1 != d_p2:
            alt_date = f"{d_p2}{d_p1}{d_yr}"
            date_variants.append(alt_date)

        target_email = generated_email
        is_already_registered = False
        is_new_student = False
        has_error = False

        for cur_bdate in date_variants:
            has_error = False
            page.locator("input#seria, input[formcontrolname='seria']").fill(seria)
            page.locator("input#number, input[formcontrolname='number']").fill(number)
            
            birth_input = page.locator("input[formcontrolname='birthdate'], input.p-inputtext").first
            birth_input.click()
            birth_input.fill("")
            birth_input.press_sequentially(cur_bdate, delay=60)
            birth_input.press("Enter")
            birth_input.press("Tab")
            print(f"Metrika ({seria} {number}) va sana ({cur_bdate[:2]}.{cur_bdate[2:4]}.{cur_bdate[4:]}) kiritildi!", flush=True)
            time.sleep(1.5)
            
            handle_recaptcha(page)
            time.sleep(1.5)
            
            print("'Yuborish' tugmasi bosilmoqda...", flush=True)
            page.evaluate("""() => {
                const btn = document.querySelector('button[type="submit"]') || Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Yuborish'));
                if (btn) {
                    btn.removeAttribute('disabled');
                    btn.click();
                }
            }""")
            
            print("Natija kutilmoqda va tekshirilmoqda...", flush=True)
            for sec in range(1, 15):
                time.sleep(1)
                content = page.content()
                u_input = page.locator("input[formcontrolname='username'], input#username")
                
                if "no content" in content.lower():
                    has_error = True
                    print(f"[{sec}s] SAYT XATOLIGI (GCP): Davlat bazasida bu o'quvchi topilmadi (No content)!", flush=True)
                    break
                    
                toast = page.locator(".p-toast-message, .p-toast-detail, .p-toast-summary, div[role='alert']")
                if toast.count() > 0:
                    t_text = toast.first.inner_text().lower()
                    if "no content" in t_text or "topilmadi" in t_text:
                        has_error = True
                        print(f"[{sec}s] SAYT XATOLIGI: {t_text}", flush=True)
                        break
                
                if "allaqachon" in content.lower():
                    is_already_registered = True
                    print(f"[{sec}s] O'quvchi allaqachon ro'yxatdan o'tgan ekan!", flush=True)
                    try:
                        email_elem = page.locator(".text-main-primary, span, p").filter(has_text="@gmail.com").first
                        if email_elem.count() > 0:
                            txt = email_elem.inner_text().strip()
                            if "@" in txt:
                                target_email = txt
                    except Exception:
                        pass
                    break
                elif u_input.count() > 0 and u_input.first.is_visible():
                    is_new_student = True
                    print(f"[{sec}s] YANGI O'QUVCHI! 2-bosqich ochildi!", flush=True)
                    break

            if not has_error:
                # Muvaffaqiyatli o'tdi (allaqachon ro'yxatdan o'tgan yoki yangi oyna ochildi)
                break
            else:
                if cur_bdate != date_variants[-1]:
                    print(f"⚠️ [AVTO-ALMASHISH] Sana davlat bazasida topilmadi. Zaxira sana (oy <-> kun) bilan qayta urinilmoqda...", flush=True)
                    time.sleep(2)'''

if old_block in text:
    text = text.replace(old_block, new_block, 1)
    with open("d:/uzbekcodersbot/5millionsertifikat/run_visual_test.py", "w", encoding="utf-8") as f:
        f.write(text)
    print("SUCCESS: Auto swapped date fallback added!")
else:
    print("ERROR: old_block not matched")
