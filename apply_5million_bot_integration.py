import os
import sys

def apply_patch():
    bot_path = r"d:\uzbekcodersbot\telegram_bot.py"
    with open(bot_path, "r", encoding="utf-8") as f:
        code = f.read()

    # 1. Add run_5million_pipeline method to TelegramBotServer
    method_code = '''    def run_5million_pipeline(self, chat_id, user_name, local_file_path, orig_fname):
        """Coursera va Aileaders tizimiga MUTLAQO daxlsiz, alohida 5 Million Prompter jarayoni"""
        try:
            self.send_message(
                chat_id,
                f"🎓 <b>BESH MILLION PROMPTER (omp.aistudy.uz) BUYURTMASI QABUL QILINDI!</b>\\n\\n"
                f"📁 Fayl: <b>{orig_fname}</b>\\n"
                f"🤖 Tizim: <b>Mustaqil 5 Million AI Bot</b>\\n\\n"
                f"⏳ O'quvchilar ro'yxati tekshirilmoqda va darslarni 100% yopish boshlandi...\\n"
                f"<i>(Eslatma: Ushbu jarayon Coursera tizimiga daxl qilmasdan mustaqil ishlaydi)</i>"
            )

            def telegram_progress_callback(msg_text):
                try:
                    self.send_message(chat_id, msg_text)
                except Exception as ex:
                    print(f"[5M TG UPDATE ERROR] {ex}")

            p5m_dir = os.path.join(BASE_DIR, "5millionsertifikat")
            if p5m_dir not in sys.path:
                sys.path.insert(0, p5m_dir)
            import process_5million_excel
            
            success_cnt, total_cnt = process_5million_excel.process_excel_order(
                local_file_path,
                update_callback=telegram_progress_callback
            )

            self.send_message(
                chat_id,
                f"🎉 <b>5 MILLION PROMPTER BUYURTMASI YAKUNLANDI!</b>\\n\\n"
                f"📊 <b>Natija:</b> {success_cnt} ta o'quvchiga sertifikat olindi!\\n"
                f"📥 To'ldirilgan va barcha sertifikat havolalari yozilgan Excel fayl quyida yuborilmoqda 👇"
            )
            self.send_document(
                chat_id,
                local_file_path,
                caption=f"✅ 5 Million Prompter Tayyor Sertifikatlar ({success_cnt} ta)"
            )
        except Exception as e:
            print(f"[5MILLION XATO] {e}")
            import traceback
            traceback.print_exc()
            self.send_message(
                chat_id,
                f"❌ <b>5 Million Prompter jarayonida xatolik:</b>\\n<code>{str(e)[:300]}</code>"
            )

'''

    marker_method = "    def process_update(self, upd):"
    if marker_method in code and "def run_5million_pipeline" not in code:
        code = code.replace(marker_method, method_code + marker_method)
        print("SUCCESS: run_5million_pipeline method added!")
    elif "def run_5million_pipeline" in code:
        print("NOTICE: run_5million_pipeline already present.")
    else:
        print("ERROR: marker_method not found!")
        return False

    # 2. Intercept document upload for 5 Million
    old_doc_block = """        # Excel yoki matn fayl kelganda:
        if "document" in msg:
            doc = msg["document"]
            orig_fname = (doc.get("file_name") or "").strip()
            clean_base = re.sub(r'[\\/*?:"<>|]', "", os.path.splitext(orig_fname)[0]).strip() or "Buyurtma"
            fname = orig_fname.lower()
            pref = f"in_{chat_id}_" if (self.admin_id and chat_id == self.admin_id) else f"pending_{chat_id}_"
            if fname.endswith(".xlsx"):"""

    new_doc_block = """        # Excel yoki matn fayl kelganda:
        if "document" in msg:
            doc = msg["document"]
            orig_fname = (doc.get("file_name") or "").strip()
            clean_base = re.sub(r'[\\/*?:"<>|]', "", os.path.splitext(orig_fname)[0]).strip() or "Buyurtma"
            fname = orig_fname.lower()

            # --- 5 MILLION PROMPTER IZOLYATSIYA QILINGAN TIZIMI ---
            user_st = admin_input_state.get(chat_id, {})
            is_5mln = False
            if user_st and user_st.get("action") == "5million_order":
                is_5mln = True
            elif any(k in fname for k in ["5mln", "5million", "prompter", "aistudy"]):
                is_5mln = True

            if is_5mln:
                admin_input_state[chat_id] = None
                orders_5m_dir = os.path.join(BASE_DIR, "5millionsertifikat", "orders")
                os.makedirs(orders_5m_dir, exist_ok=True)
                local_5m = self.download_file(doc["file_id"], os.path.join(orders_5m_dir, f"5mln_{chat_id}_{int(time.time())}_{clean_base}.xlsx"))
                threading.Thread(
                    target=self.run_5million_pipeline,
                    args=(chat_id, user_name, local_5m, orig_fname),
                    daemon=True
                ).start()
                return
            # --- COURSERA (AILEADERS) TIZIMI (O'ZGARIShSIZ DAVOM ETADI) ---

            pref = f"in_{chat_id}_" if (self.admin_id and chat_id == self.admin_id) else f"pending_{chat_id}_"
            if fname.endswith(".xlsx"):"""

    if old_doc_block in code:
        code = code.replace(old_doc_block, new_doc_block)
        print("SUCCESS: 5 Million document interceptor installed!")
    elif "5 MILLION PROMPTER IZOLYATSIYA QILINGAN TIZIMI" in code:
        print("NOTICE: Document interceptor already installed.")
    else:
        print("ERROR: old_doc_block not found!")
        return False

    with open(bot_path, "w", encoding="utf-8") as f:
        f.write(code)

    print("ALL PATCHES APPLIED TO telegram_bot.py SUCCESSFULLY!")
    return True

if __name__ == "__main__":
    apply_patch()
