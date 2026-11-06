import os
import sys
import io
import zipfile
import secrets
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

BASE_DIR = Path(__file__).resolve().parent
SESSIONS_DIR = BASE_DIR / "sessions"
VAULT_FILE = BASE_DIR / "sessions_vault_aes256.enc"

DEFAULT_SECRET = "UzbekCoders2026!Studio5Million"

def derive_key(passphrase: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,  # 256 bits for AES-256
        salt=salt,
        iterations=100000,
    )
    return kdf.derive(passphrase.encode("utf-8"))

def encrypt_sessions(passphrase: str = DEFAULT_SECRET) -> str:
    if not SESSIONS_DIR.exists():
        raise FileNotFoundError(f"{SESSIONS_DIR} papkasi topilmadi!")

    # 1. Barcha .session fayllarni xotiradagi ZIP arxiviga yig'ish
    zip_buffer = io.BytesIO()
    count = 0
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in SESSIONS_DIR.glob("*.session"):
            zf.write(f, arcname=f.name)
            count += 1
        # session_pool_state.json ni ham qo'shib saqlaymiz
        pool_state = BASE_DIR / "session_pool_state.json"
        if pool_state.exists():
            zf.write(pool_state, arcname="session_pool_state.json")

    raw_data = zip_buffer.getvalue()

    # 2. AES-256-GCM shifrlash
    salt = secrets.token_bytes(16)
    key = derive_key(passphrase, salt)
    aesgcm = AESGCM(key)
    nonce = secrets.token_bytes(12)  # 96-bit nonce for GCM

    ciphertext = aesgcm.encrypt(nonce, raw_data, None)

    # 3. Faylga saqlash: [16 bayt Salt] + [12 bayt Nonce] + [Ciphertext + Tag]
    with open(VAULT_FILE, "wb") as f:
        f.write(salt + nonce + ciphertext)

    size_kb = os.path.getsize(VAULT_FILE) / 1024
    print(f"✅ [AES-256 SHIFRLANDI] {count} ta sessiya shifrlandi!")
    print(f"📁 Shifrlangan fayl: {VAULT_FILE.name} ({size_kb:.1f} KB)")
    return str(VAULT_FILE)

def decrypt_sessions(passphrase: str = DEFAULT_SECRET, output_dir: Path = SESSIONS_DIR):
    if not VAULT_FILE.exists():
        raise FileNotFoundError(f"{VAULT_FILE} fayli topilmadi!")

    with open(VAULT_FILE, "rb") as f:
        data = f.read()

    salt = data[:16]
    nonce = data[16:28]
    ciphertext = data[28:]

    key = derive_key(passphrase, salt)
    aesgcm = AESGCM(key)

    decrypted_data = aesgcm.decrypt(nonce, ciphertext, None)

    output_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(decrypted_data), "r") as zf:
        zf.extractall(output_dir)
        names = zf.namelist()

    print(f"✅ [AES-256 TIKLANDI] {len(names)} ta fayl {output_dir.name} papkasiga ochildi!")

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "encrypt"
    pwd = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_SECRET

    if action == "encrypt":
        encrypt_sessions(pwd)
    elif action == "decrypt":
        decrypt_sessions(pwd)
    else:
        print("Foydalanish: python secure_sessions_aes256.py [encrypt|decrypt] [parol]")
