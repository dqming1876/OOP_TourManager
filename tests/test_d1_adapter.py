"""Exercise the production D1 adapter against a binding double with real SQLite triggers."""
import ast
from types import SimpleNamespace
from unittest import IsolatedAsyncioTestCase
from scripts.sqlite_worker import ROOT
from tests.fixtures import last_seats, ORDER, TODAY, ADMIN
from backend.domain import Booking
from backend.repositories import BookingRepository
from backend.services import BookingService


class D1AdapterRegression(IsolatedAsyncioTestCase):
    async def test_only_target_rows_count_for_payment_and_cancel(self):
        worker = last_seats()
        self.addCleanup(worker.database.close)
        db = worker.database
        class Statement:
            def __init__(self, sql, values=()): self.sql, self.values = sql, values
            def bind(self, *values): return Statement(self.sql, values)
            async def first(self):
                row = db.execute(self.sql, self.values).fetchone()
                return dict(row) if row else None
            async def all(self):
                return {'results': [dict(row) for row in db.execute(self.sql, self.values).fetchall()]}
            async def run(self):
                before = db.total_changes
                db.execute(self.sql, self.values)
                return SimpleNamespace(meta=SimpleNamespace(changes=db.total_changes-before))
        tree = ast.parse((ROOT/'entry.py').read_text())
        cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'D1Database')
        namespace = {'JsProxy': type('JsProxy', (), {})}
        exec(compile(ast.Module(body=[cls], type_ignores=[]), 'entry.py', 'exec'), namespace)
        adapter = namespace['D1Database'](SimpleNamespace(prepare=Statement))
        repo = BookingRepository(adapter)
        self.assertTrue(await repo.place_booking(Booking.request('adapter-order','axis5-guest',ORDER), TODAY))
        service = BookingService(repo, ADMIN, TODAY)
        for action in ('confirm','collect','refund','cancel'):
            await service.update_booking('adapter-order', action)
        self.assertEqual(db.execute("SELECT status FROM bookings WHERE id='adapter-order'").fetchone()[0], 'cancelled')
        self.assertEqual(db.execute('SELECT count(*) FROM payment_events').fetchone()[0], 2)
        self.assertEqual(await adapter.execute("UPDATE bookings SET paid=0 WHERE id='missing'"), 0)
