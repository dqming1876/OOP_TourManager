"""Cloudflare Python Worker. The binding, secrets and assets keep their original names."""

from js import Headers, Object, TextEncoder, Response as JSResponse, crypto
from pyodide.ffi import JsProxy, to_js
from workers import Response as WorkerResponse, WorkerEntrypoint

from backend.app import Application, Request, Response
from backend.auth import Settings


def setting(env, key):
    value = getattr(env, key, None)
    return value if isinstance(value, str) else None


class D1Database:
    def __init__(self, binding):
        self.binding = binding

    def prepare(self, sql, values):
        statement = self.binding.prepare(sql)
        return statement.bind(*values) if values else statement

    async def first(self, sql, *values):
        row = await self.prepare(sql, values).first()
        return row.to_py() if isinstance(row, JsProxy) else row

    async def all(self, sql, *values):
        result = await self.prepare(sql, values).all()
        return result["results"]

    async def execute(self, sql, *values):
        # D1 meta.changes includes trigger writes; count only the target rows.
        result = await self.prepare(sql.rstrip().rstrip(";") + " RETURNING 1 AS changed", values).all()
        return len(result["results"])

    async def batch(self, statements):
        queries = [self.prepare(sql, values) for sql, values in statements]
        result = await self.binding.batch(queries)
        return [item["results"] for item in result]


class WorkerRequest(Request):
    def __init__(self, original):
        self.original = getattr(original, "js_object", None) or original
        super().__init__(self.original.method, self.original.url)

    def header(self, name):
        return self.original.headers.get(name)

    async def text(self, limit):
        return await self.original.text()


async def derive_password(password, salt):
    encoder = TextEncoder.new()
    key = await crypto.subtle.importKey("raw", encoder.encode(password), "PBKDF2", False, to_js(["deriveBits"]))
    algorithm = to_js({
        "name": "PBKDF2", "salt": encoder.encode(salt), "iterations": 100_000, "hash": "SHA-256",
    }, dict_converter=Object.fromEntries)
    digest = await crypto.subtle.deriveBits(algorithm, key, 256)
    return digest.to_bytes().hex()


app = Application(derive=derive_password)


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        env = self.env
        binding = getattr(env, "DB", None)
        db = D1Database(binding) if binding is not None else None
        settings = Settings(*(setting(env, key) for key in (
            "ADMIN_USERNAME", "ADMIN_PASSWORD_HASH", "ADMIN_PASSWORD_SALT", "ADMIN_SESSION_SECRET"
        )))

        async def assets(_request):
            asset = await env.ASSETS.fetch(request)
            raw = getattr(asset, "js_object", None) or asset
            headers = Headers.new(raw.headers)
            headers.set("X-Content-Type-Options", "nosniff")
            return JSResponse.new(raw.body, to_js(
                {"status": raw.status, "statusText": raw.statusText, "headers": headers},
                dict_converter=Object.fromEntries,
            ))

        response = await app.fetch(WorkerRequest(request), db, settings, assets)
        if not isinstance(response, Response):
            return WorkerResponse(response)
        headers = Headers.new()
        for name, value in response.headers:
            headers.append(name, value)
        return WorkerResponse(response.body, status=response.status, headers=headers)
