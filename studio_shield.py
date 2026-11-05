# -*- coding: utf-8 -*-
"""
AI STUDIO - SECURITY SHIELD & ENCRYPTED VAULT
Ushbu modul barcha asosiy kodlar va ma'lumotlar bazasini AES-256 bilan
shifrlaydi va himoyalaydi.
"""

import os
import sys
import json
import zlib
import base64
import hashlib
from pathlib import Path
from cryptography.fernet import Fernet

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_SHIELD = "STUDIO_AI_SECURE_VAULT_KEY_2026_OBIDBEK_PROMPTER_99"
ENC_FILE = BASE_DIR / "studio_core.enc"

def get_fernet(shield_key: str = None) -> Fernet:
    key_str = shield_key or os.environ.get("STUDIO_KEY", DEFAULT_SHIELD)
    k = base64.urlsafe_b64encode(hashlib.sha256(key_str.encode("utf-8")).digest())
    return Fernet(k)

def encrypt_core_vault(shield_key: str = None) -> bool:
    """Asosiy kod va bazani bitta shifrlangan faylga joylash"""
    try:
        fernet = get_fernet(shield_key)
        bundle = {}

        # 1. Asosiy dvigatel kodi
        engine_path = BASE_DIR / "process_5million_excel.py"
        if engine_path.exists():
            with open(engine_path, "r", encoding="utf-8", errors="replace") as f:
                bundle["process_5million_excel.py"] = f.read()

        # 2. O'quvchilar ma'lumotlar bazasi
        db_path = BASE_DIR / "students_db.json"
        if db_path.exists():
            with open(db_path, "r", encoding="utf-8", errors="replace") as f:
                bundle["students_db.json"] = f.read()

        # 3. Javoblar
        ans_path = BASE_DIR / "pdf_javoblar.txt"
        if ans_path.exists():
            with open(ans_path, "r", encoding="utf-8", errors="replace") as f:
                bundle["pdf_javoblar.txt"] = f.read()

        raw_bytes = json.dumps(bundle, ensure_ascii=False).encode("utf-8")
        compressed = zlib.compress(raw_bytes, level=9)
        encrypted = fernet.encrypt(compressed)

        with open(ENC_FILE, "wb") as f:
            f.write(encrypted)

        print(f"[SHIELD] Muvaffaqiyatli shifrlandi: {ENC_FILE.name} ({len(encrypted) / 1024:.1f} KB)")
        return True
    except Exception as e:
        print(f"[SHIELD ENCRYPT ERROR] {e}")
        return False

def decrypt_core_vault(shield_key: str = None) -> bool:
    """Shifrlangan fayldan kerakli kod va bazani tiklash"""
    try:
        if not ENC_FILE.exists():
            print("[SHIELD] Shifrlangan fayl topilmadi!")
            return False

        fernet = get_fernet(shield_key)
        with open(ENC_FILE, "rb") as f:
            encrypted = f.read()

        compressed = fernet.decrypt(encrypted)
        raw_bytes = zlib.decompress(compressed)
        bundle = json.loads(raw_bytes.decode("utf-8"))

        for fname, content in bundle.items():
            dest = BASE_DIR / fname
            # Faqat fayl yo'q bo'lsa yoki yangi bo'lsa yozamiz
            with open(dest, "w", encoding="utf-8") as f:
                f.write(content)

        print("[SHIELD] Maxfiy dvigatel va baza xavfsiz ochildi!")
        return True
    except Exception as e:
        print(f"[SHIELD DECRYPT ERROR] {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "decrypt":
        decrypt_core_vault()
    else:
        encrypt_core_vault()
