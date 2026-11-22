import ast
import json
import sqlite3
from dataclasses import FrozenInstanceError
from types import MappingProxyType
from unittest import IsolatedAsyncioTestCase

from backend.app import Repositories
from backend.domain import AdministratorAccount, AppError, Destination, Tour, TourStop
from backend.services import AccessPolicy
from scripts.sqlite_worker import ROOT, LocalWorker
from tests.fixtures import FUTURE, GUEST, ORDER, TOUR, api, cookie


class Architecture(IsolatedAsyncioTestCase):
    def test_ownership_of_tour_stops(self):
        worker = LocalWorker()
        db = worker.database
        self.addCleanup(db.close)
        db.executescript("""
            INSERT INTO tours (id,price) VALUES ('tour-4a',1200000),('tour-4b',1200000);
            INSERT INTO destinations (province,name) VALUES ('Hà Nội','Điểm thử 4.1');
            INSERT INTO tour_stops SELECT 'tour-4a',1,id,'Sáng đi bộ' FROM destinations WHERE name='Điểm thử 4.1';
            INSERT INTO tour_stops SELECT 'tour-4b',1,id,'Tối đi bộ' FROM destinations WHERE name='Điểm thử 4.1';
            DELETE FROM tours WHERE id='tour-4a';
        """)
        rows = db.execute("""
            SELECT tour_id FROM tour_stops JOIN destinations ON destinations.id = destination_id WHERE name='Điểm thử 4.1'
        """).fetchall()
        self.assertEqual([row[0] for row in rows], ["tour-4b"])
        db.execute("INSERT INTO departures(tour_id,day,capacity) VALUES ('tour-4b',?,5)", (FUTURE,))
        with self.assertRaises(sqlite3.IntegrityError):
            db.execute("DELETE FROM tours WHERE id='tour-4b'")
        self.assertFalse(db.execute("PRAGMA foreign_key_check").fetchall())

    def test_schema_migration_preserves_existing_data(self):
        db = sqlite3.connect(":memory:")
        self.addCleanup(db.close)
        db.execute("PRAGMA foreign_keys = ON")
        migrations = sorted(p for p in (ROOT / "Database").glob("*.sql") if p.name <= "0005_tour_stop_ownership.sql")
        for migration in migrations[:-1]:
            db.executescript(migration.read_text(encoding="utf-8"))
        db.executescript("""
            INSERT INTO tours VALUES ('legacy-tour',100000,0,'{}');
            INSERT INTO destinations (province,name) VALUES ('Hà Nội','Địa danh cũ');
            INSERT INTO tour_stops SELECT 'legacy-tour',1,id,'Dữ liệu cũ' FROM destinations WHERE name='Địa danh cũ';
        """)
        before = db.execute("SELECT * FROM tour_stops").fetchall()
        db.executescript(migrations[-1].read_text(encoding="utf-8"))
        self.assertEqual(db.execute("SELECT * FROM tour_stops").fetchall(), before)
        self.assertFalse(db.execute("PRAGMA foreign_key_check").fetchall())

    def test_layer_boundaries(self):
        modules = {source.stem: ast.parse(source.read_text(encoding="utf-8"))
                   for source in (ROOT / "backend").glob("*.py")}
        dependencies = {name: {node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.level}
                        for name, tree in modules.items()}

        def visit(name, stack):
            self.assertNotIn(name, stack)
            for dependency in dependencies[name]:
                visit(dependency, stack | {name})

        for name in modules:
            visit(name, set())
        self.assertFalse(dependencies["domain"])
        self.assertFalse(dependencies["pricing"])
        self.assertLessEqual(dependencies["services"], {"domain", "auth", "ports", "login_limits"})
        self.assertNotIn("services", dependencies["repositories"])
        for name in ("app", "domain", "services", "destinations", "login_limits", "pricing"):
            for node in ast.walk(modules[name]):
                if isinstance(node, ast.Constant) and isinstance(node.value, str):
                    self.assertNotRegex(node.value, r"(?i)\b(SELECT .+ FROM|INSERT INTO|UPDATE .+ SET|DELETE FROM)\b")

    def test_immutability_and_polymorphic_scope(self):
        self.assertEqual(AccessPolicy(GUEST.actor).booking_scope(), GUEST.actor.id)
        self.assertIsNone(AccessPolicy(AdministratorAccount("admin")).booking_scope())
        with self.assertRaises(FrozenInstanceError):
            GUEST.actor.role = "admin"
        with self.assertRaises(AppError):
            AccessPolicy(None).booking_scope()
        tour = Tour.request("tour", TOUR)
        with self.assertRaises(TypeError):
            tour.details["days"] = 0
        self.assertIsInstance(tour.stops, tuple)
        valid_place = Destination("Hà Nội", "Hồ Gươm")
        for invalid in (
            lambda: Destination("", "Hồ Gươm"),
            lambda: Destination("Hà Nội", "   "),
            lambda: TourStop(0, "Đi bộ", valid_place),
            lambda: TourStop(1, "  ", valid_place),
            lambda: Tour("tour", MappingProxyType({}), ()),
            lambda: Tour("tour", dict(tour.details), None),
            lambda: Tour("tour", tour.details, (TourStop(1, "Đi bộ", valid_place),)),
        ):
            with self.assertRaises(AppError) as error:
                invalid()
            self.assertEqual(error.exception.status, 400)

    async def test_in_memory_booking_port_at_http_entry(self):
        class InMemoryBooking:
            def __init__(self, _db):
                pass

            async def place_booking(self, booking, _today):
                orders.append({"id": booking.id, "people": booking.people})
                return True

            async def list_bookings(self, _owner):
                return orders.copy()

        orders = []
        worker = LocalWorker(repositories=Repositories(bookings=InMemoryBooking), seed="""
            INSERT INTO accounts (id,username,name,password_hash,salt)
            VALUES ('axis5-guest','axis5_guest','Khách thử','fixture-only','fixture-only');
        """)
        self.addCleanup(worker.database.close)
        token = cookie(worker, GUEST)
        response = await api(worker, "/api/ops/bookings", ORDER, token)
        self.assertEqual(response.status, 201)
        result = await api(worker, "/api/ops/bookings", token=token)
        self.assertEqual(json.loads(result.body)["bookings"], [{"id": json.loads(response.body)["id"], "people": 3}])
        self.assertEqual(worker.database.execute("SELECT count(*) FROM bookings").fetchone()[0], 0)
