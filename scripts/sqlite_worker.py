"""SQLite counterpart to D1, shared by the demo and integration tests."""

import sqlite3
from pathlib import Path
from secrets import token_urlsafe
from uuid import uuid4

from backend.app import Application, Response, local_day
from backend.auth import Settings, password_hash

ROOT = Path(__file__).resolve().parents[1]


class SQLiteDatabase:
    def __init__(self, database):
        self.connection = database
        self.queries = []

    def query(self, sql, values):
        self.queries.append(sql)
        return self.connection.execute(sql, values)

    async def first(self, sql, *values):
        row = self.query(sql, values).fetchone()
        return dict(row) if row is not None else None

    async def all(self, sql, *values):
        return [dict(row) for row in self.query(sql, values)]

    async def execute(self, sql, *values):
        return self.query(sql, values).rowcount

    async def batch(self, statements):
        self.connection.execute("BEGIN")
        try:
            results = [await self.all(sql, *values) for sql, values in statements]
            self.connection.commit()
            return results
        except BaseException:
            self.connection.rollback()
            raise


class LocalWorker:
    def __init__(self, *, admin_password=None, seed=None, today=local_day, repositories=None, assets=None):
        self.database = sqlite3.connect(":memory:", isolation_level=None)
        self.database.row_factory = sqlite3.Row
        self.database.execute("PRAGMA foreign_keys = ON")
        try:
            for migration in sorted((ROOT / "Database").glob("*.sql")):
                self.database.executescript(migration.read_text(encoding="utf-8"))
            if seed:
                self.database.executescript("BEGIN;\n" + seed + "\nCOMMIT;")
        except BaseException:
            self.database.close()
            raise
        self.admin_password = admin_password or token_urlsafe(18)
        salt = str(uuid4())
        self.settings = Settings("demo_admin", password_hash(self.admin_password, salt), salt, str(uuid4()))
        self.db = SQLiteDatabase(self.database)
        self.app = Application(repositories=repositories, today=today)
        self.assets = assets or missing_asset

    async def fetch(self, request):
        return await self.app.fetch(request, self.db, self.settings, self.assets)


async def missing_asset(_request):
    return Response("Not found", 404)
