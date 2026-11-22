"""Shared login windows persisted through AccountsPort."""
import hmac
from time import time
from .domain import AppError


class LoginRateLimiter:
    def __init__(self, repository, secret):
        self.repository = repository
        self.secret = secret or "local"

    async def claim(self, address):
        key = hmac.new(self.secret.encode(), address.encode(), "sha256").hexdigest()
        ticket = await self.repository.claim_attempt(key, int(time()))
        if ticket is None:
            raise AppError(429, "Bạn đã thử quá nhiều lần. Vui lòng thử lại sau 5 phút.")
        return key, ticket["expires_at"]

    async def clear(self, ticket):
        await self.repository.clear_attempts(*ticket)
