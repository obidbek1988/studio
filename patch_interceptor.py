with open(r"d:\uzbekcodersbot\telegram_bot.py", "r", encoding="utf-8") as f:
    text = f.read()

pos1 = text.find('pref = f"in_{chat_id}_" if (self.admin_id and chat_id == self.admin_id) else f"pending_{chat_id}_"')
if pos1 != -1:
    interceptor_code = '''            # --- 5 MILLION PROMPTER IZOLYATSIYA QILINGAN TIZIMI ---
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
            '''
    text = text[:pos1] + interceptor_code + text[pos1:]
    with open(r"d:\uzbekcodersbot\telegram_bot.py", "w", encoding="utf-8") as f:
        f.write(text)
    print("SUCCESS: 5 Million interceptor successfully injected into telegram_bot.py!")
else:
    print("ERROR: pos1 not found")
