"""Generate the existing Cloudflare admin password hash and salt from stdin."""

import sys
from uuid import uuid4

from backend.auth import password_hash
from backend.domain import text_length


def main():
    password = sys.stdin.read().removesuffix("\n").removesuffix("\r")
    if not 12 <= text_length(password) <= 128:
        print("Nhập mật khẩu quản trị dài 12–128 ký tự qua stdin.", file=sys.stderr)
        return 1
    salt = str(uuid4())
    print(f"ADMIN_PASSWORD_SALT={salt}")
    print(f"ADMIN_PASSWORD_HASH={password_hash(password, salt)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
