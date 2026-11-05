import sys
import re
from session_pool import fetch_tg_code_from_pool

def fetch_code():
    try:
        code, session_name = fetch_tg_code_from_pool()
        if code:
            print(code)
            return code
    except Exception as e:
        sys.stderr.write(str(e))
    return None

if __name__ == "__main__":
    fetch_code()
