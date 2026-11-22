"""Password verification and the existing signed-session wire format."""

import hashlib
import hmac
import re
import time
from dataclasses import dataclass

from .domain import AppError

ADMIN_COOKIE = "dv_admin"
CUSTOMER_COOKIE = "dv_user"
SESSION_SECONDS = 8 * 60 * 60
COOKIE_OPTIONS = "; HttpOnly; Secure; SameSite=Strict; Path=/; Max-Age="


@dataclass(frozen=True)
class Settings:
    username: str | None
    password_hash: str | None
    salt: str | None
    secret: str | None


def password_hash(password, salt):
    encoded = password.encode("utf-16-le", errors="surrogatepass").decode("utf-16-le", errors="replace").encode()
    return hashlib.pbkdf2_hmac("sha256", encoded, salt.encode(), 100_000, 32).hex()


async def derive_password(password, salt):
    return password_hash(password, salt)


def signature(value, secret):
    return hmac.new(secret.encode(), value.encode(), hashlib.sha256).hexdigest()


def equal(left, right):
    return isinstance(right, str) and hmac.compare_digest(left.encode(), right.encode(errors="surrogatepass"))


def cookie_options(secure=True):
    return f"; HttpOnly{'; Secure' if secure else ''}; SameSite=Strict; Path=/; Max-Age="


def clear_cookie(name, secure=True):
    return f"{name}={cookie_options(secure)}0"


def create_session(name, secret, customer_id=None, secure=True):
    if not secret:
        raise AppError(503, "Hệ thống tài khoản chưa sẵn sàng.")
    expiry = int(time.time() * 1000) + SESSION_SECONDS * 1000
    value = f"{customer_id}.{expiry}" if customer_id else str(expiry)
    return f"{name}={value}.{signature(value, secret)}{cookie_options(secure)}{SESSION_SECONDS}"


def session_identity(request, secret, name):
    if not secret:
        return None
    token = re.search(r"(?:^|;\s*)" + name + r"=([^;]+)", request.header("Cookie") or "")
    if not token:
        return None
    parts = token[1].split(".")
    admin = name == ADMIN_COOKIE
    if len(parts) != (2 if admin else 3):
        return None
    expiry = parts[-2]
    if not re.fullmatch(r"[0-9]{1,16}", expiry):
        return None
    now = int(time.time() * 1000)
    if not now <= int(expiry) <= now + 9 * 3_600_000:
        return None
    if equal(signature(".".join(parts[:-1]), secret), parts[-1]):
        return "admin" if admin else parts[0]
    return None
