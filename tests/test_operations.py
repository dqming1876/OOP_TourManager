import json
from time import perf_counter
from unittest import IsolatedAsyncioTestCase

from backend.auth import ADMIN_COOKIE, CUSTOMER_COOKIE, password_hash
from backend.domain import AppError
from backend.repositories import BookingRepository
from backend.services import BookingService
from scripts.demo_data import DEMO_PASSWORD, demo_sql
from scripts.sqlite_worker import LocalWorker
from tests.fixtures import ADMIN, FUTURE, GUEST, ORDER, OTHER, TODAY, TOUR, api, cookie, last_seats


class Operations(IsolatedAsyncioTestCase):
    def setUp(self):
        self.worker = last_seats()
        self.db = self.worker.database
        self.addCleanup(self.db.close)
        self.admin = cookie(self.worker)
        self.guest = cookie(self.worker, GUEST)
        self.other = cookie(self.worker, OTHER)

    async def request(self, path, body=None, token=None):
        return await api(self.worker, path, body, token)

    async def place(self):
        response = await self.request("/api/ops/bookings", ORDER, self.guest)
        self.assertEqual(response.status, 201)
        return json.loads(response.body)["id"]

    async def action(self, booking_id, action, token=None):
        return await self.request(f"/api/ops/bookings/{booking_id}/{action}", {}, token or self.admin)

    def reserved(self):
        return self.db.execute("SELECT reserved FROM departures WHERE tour_id='axis5-tour'").fetchone()[0]

    async def test_hold_release_and_customer_scope(self):
        booking = await self.place()
        self.assertEqual(self.reserved(), 3)
        for token, ids in ((self.admin, [booking]), (self.guest, [booking]), (self.other, [])):
            response = await self.request("/api/ops/bookings", token=token)
            self.assertEqual([b["id"] for b in json.loads(response.body)["bookings"]], ids)
        self.assertEqual((await self.action(booking, "cancel", self.other)).status, 409)
        self.assertEqual((await self.action(booking, "cancel", self.guest)).status, 200)
        self.assertEqual(self.reserved(), 0)
        self.assertNotEqual(await self.place(), booking)

    async def test_transitions_and_historical_price(self):
        booking = await self.place()
        self.db.execute("UPDATE tours SET price=5000000 WHERE id='axis5-tour'")
        self.assertEqual((await self.action(booking, "collect")).status, 409)
        self.assertEqual((await self.action(booking, "confirm", self.guest)).status, 403)
        self.assertEqual((await self.action(booking, "confirm")).status, 200)
        self.assertEqual((await self.action(booking, "cancel", self.guest)).status, 409)
        self.assertEqual((await self.action(booking, "collect")).status, 200)
        self.assertEqual((await self.action(booking, "cancel")).status, 409)
        self.assertEqual((await self.action(booking, "refund")).status, 200)
        self.assertEqual((await self.action(booking, "cancel")).status, 200)
        history = await self.request(f"/api/ops/bookings/{booking}/payments", token=self.admin)
        self.assertEqual([event["signedAmount"] for event in json.loads(history.body)["payments"]],
                         [1_500_000, -1_500_000])
        orders = await self.request("/api/ops/bookings", token=self.admin)
        self.assertEqual(json.loads(orders.body)["bookings"][0]["total"], 1_500_000)

    async def test_validation_and_duplicate_departures(self):
        for patch, expected in (({"phone": "x"}, "phone"), ({"adults": 0}, "adults"),
                                ({"day": "2028-02-30"}, "day")):
            response = await self.request("/api/ops/bookings", {**ORDER, **patch}, self.guest)
            self.assertEqual((response.status, json.loads(response.body)["field"]), (400, expected))
        bad_tour = await self.request("/api/ops/tours", {**TOUR, "price": -1}, self.admin)
        self.assertEqual(json.loads(bad_tour.body)["field"], "price")
        bad_profile = await self.request("/api/profile", {"name": "Khách thử", "email": "x"}, self.guest)
        self.assertEqual(json.loads(bad_profile.body)["field"], "email")
        path = "/api/ops/tours/axis5-tour/departures"
        self.assertEqual((await self.request(path, {"day": FUTURE, "capacity": 0}, self.admin)).status, 400)
        self.assertEqual((await self.request(path, {"day": FUTURE, "capacity": 9}, self.admin)).status, 409)
        self.assertEqual(self.db.execute("SELECT capacity FROM departures WHERE tour_id='axis5-tour'").fetchone()[0], 3)
        self.assertEqual((await self.request(path, {"day": FUTURE, "capacity": 9, "edit": True}, self.admin)).status, 200)

    async def test_release_rollback(self):
        booking = await self.place()
        self.db.executescript("""
            CREATE TRIGGER fail_release BEFORE UPDATE OF reserved ON departures WHEN NEW.reserved < OLD.reserved
            BEGIN SELECT RAISE(ABORT, 'test release'); END;
        """)
        self.assertEqual((await self.action(booking, "cancel")).status, 500)
        self.assertEqual(self.reserved(), 3)
        self.assertEqual(self.db.execute("SELECT status FROM bookings").fetchone()[0], "pending")

    async def test_collect_rollback(self):
        booking = await self.place()
        await self.action(booking, "confirm")
        self.db.executescript("""
            CREATE TRIGGER fail_payment BEFORE INSERT ON payment_events
            BEGIN SELECT RAISE(ABORT, 'test payment'); END;
        """)
        self.assertEqual((await self.action(booking, "collect")).status, 500)
        self.assertEqual(self.db.execute("SELECT paid FROM bookings").fetchone()[0], 0)
        self.assertEqual(self.db.execute("SELECT count(*) FROM payment_events").fetchone()[0], 0)

    async def test_password_profile_and_sessions(self):
        body = {"username": "new_guest", "name": "Khách mới", "password": "example-123"}
        path = "/api/auth/register"
        self.assertEqual((await self.request(path, body)).status, 201)
        self.assertEqual((await self.request(path, body)).status, 409)
        row = dict(self.db.execute("SELECT * FROM accounts WHERE username='new_guest'").fetchone())
        self.assertEqual(row["password_hash"], password_hash(body["password"], row["salt"]))
        self.assertNotEqual(row["password_hash"], body["password"])
        login = await self.request("/api/auth/login", body)
        self.assertEqual(login.status, 200)
        cookies = [v for k, v in login.headers if k == "Set-Cookie"]
        self.assertEqual(len(cookies), 2)
        self.assertTrue(cookies[0].startswith(ADMIN_COOKIE + "="))
        self.assertTrue(cookies[1].startswith(CUSTOMER_COOKIE + "="))
        token = cookies[1].split(";", 1)[0]
        profile = await self.request("/api/profile", {"name": "Tên mới", "birthday": "2000-02-29"}, token)
        self.assertEqual(json.loads(profile.body)["user"]["name"], "Tên mới")
        me = await self.request("/api/auth/me", token=token)
        self.assertEqual(json.loads(me.body)["user"]["birthday"], "2000-02-29")
        admin = await self.request("/api/admin/login", {
            "username": self.worker.settings.username, "password": self.worker.admin_password,
        })
        self.assertEqual(json.loads(admin.body), {"ok": True})
        self.assertEqual((await self.request("/api/auth/login", {**body, "password": "wrong"})).status, 401)

    async def test_http_boundaries_and_legacy_session(self):
        from backend.app import Request, Response

        async def assets(_request):
            return Response("assets")

        self.worker.assets = assets
        self.assertEqual((await self.request("/admin.js")).status, 401)
        self.assertEqual((await self.request("/admin.js", token=self.admin)).body, "assets")
        session = await self.request("/api/admin/session", token=self.admin)
        self.assertEqual(json.loads(session.body), {"authenticated": True})
        self.assertEqual((await self.request("/api/ops/unknown")).status, 404)
        self.assertEqual((await self.request("/api/auth/logout")).status, 405)
        forged = await api(self.worker, "/api/auth/logout", {}, self.admin, origin="https://other.example")
        self.assertEqual(forged.status, 403)
        raw = await self.worker.fetch(Request("POST", "http://localhost/api/auth/login", {"Origin": "http://localhost"}, "[]"))
        self.assertEqual(raw.status, 400)

    async def test_expired_order_rejected_at_service_and_http(self):
        booking = await self.place()
        past_worker_day = "2028-03-08"
        self.worker.app.today = lambda: past_worker_day
        service = BookingService(BookingRepository(self.worker.db), ADMIN, past_worker_day)
        with self.assertRaises(AppError) as error:
            await service.update_booking(booking, "confirm")
        self.assertEqual(error.exception.status, 409)
        self.assertEqual((await self.action(booking, "confirm")).status, 409)

    async def test_shared_destinations_and_hidden_tours(self):
        path = "/api/ops/tours"
        one = await self.request(path, TOUR, self.admin)
        two = await self.request(path, {**TOUR, "title": "Tour khác", "itinerary": ["Đi khác", "Tham quan"]}, self.admin)
        self.assertEqual((one.status, two.status), (201, 201))
        one_id, two_id = [json.loads(reply.body)["id"] for reply in (one, two)]
        rows = self.db.execute(
            "SELECT destination_id, activity FROM tour_stops WHERE tour_id IN (?,?) AND day_number=1",
            (one_id, two_id),
        ).fetchall()
        self.assertEqual(rows[0]["destination_id"], rows[1]["destination_id"])
        self.assertEqual({row["activity"] for row in rows}, {"Đi bộ", "Đi khác"})
        self.assertEqual((await self.request(path + "/" + one_id + "/visibility", {"hidden": True}, self.admin)).status, 200)
        public, admin = [json.loads((await self.request(path, token=token)).body)["tours"]
                         for token in (self.guest, self.admin)]
        self.assertNotIn(one_id, {t["id"] for t in public})
        self.assertIn(one_id, {t["id"] for t in admin})

    async def test_120_orders_reports_use_three_queries(self):
        self.db.execute("UPDATE departures SET capacity=100 WHERE tour_id='axis5-tour'")
        self.db.execute("INSERT INTO departures (tour_id,day,capacity) VALUES ('axis5-tour','2028-03-09',100)")
        self.db.executemany("""
            INSERT INTO bookings (id,user_id,tour_id,day,title,name,phone,adults,children,unit_price,status)
            VALUES (?, 'axis5-guest', 'axis5-tour', ?, 'Tour', 'Khách', '0900000000', 1, 0, 500000, 'confirmed')
        """, [(str(index), FUTURE if index < 60 else "2028-03-09") for index in range(120)])
        self.assertEqual((await self.request("/api/ops/reports", token=self.guest)).status, 403)
        self.assertEqual((await self.request("/api/ops/reports?from=2028-02-30", token=self.admin)).status, 400)
        self.worker.db.queries.clear()
        all_orders = await self.request("/api/ops/reports", token=self.admin)
        self.assertEqual(sum(row["orders"] for row in json.loads(all_orders.body)["bookings"]), 120)
        self.assertEqual(len(self.worker.db.queries), 3)
        plan = self.db.execute("EXPLAIN QUERY PLAN " + self.worker.db.queries[1],
                               (TODAY, TODAY, FUTURE, "2028-03-09", "", "")).fetchall()
        self.assertTrue(any("bookings_report_by_day" in row["detail"] for row in plan))
        path = f"/api/ops/reports?tour=axis5-tour&from={FUTURE}&to={FUTURE}"
        timings = []
        for _ in range(30):
            self.worker.db.queries.clear()
            start = perf_counter()
            response = await self.request(path, token=self.admin)
            timings.append((perf_counter() - start) * 1000)
            self.assertEqual(len(self.worker.db.queries), 3)
            self.assertEqual(json.loads(response.body)["bookings"], [
                {"month": "2028-03", "state": "confirmed", "orders": 60, "guests": 60},
            ])
        print(f"120 đơn, 30 lượt lọc SQLite. P95 = {sorted(timings)[28]:.2f} ms.")


class SeedTests(IsolatedAsyncioTestCase):
    def setUp(self):
        self.today = "2026-11-21"
        self.worker = LocalWorker(seed=demo_sql(self.today), today=lambda: self.today)
        self.db = self.worker.database
        self.addCleanup(self.db.close)

    async def test_demo_seed_and_reports(self):
        for table, count in (("accounts", 8), ("departures", 18), ("bookings", 126), ("payment_events", 69)):
            self.assertEqual(self.db.execute(f"SELECT count(*) FROM {table}" + (" WHERE tour_id LIKE 'demo-%'" if table == "departures" else "")).fetchone()[0], count)
        self.assertFalse(self.db.execute("PRAGMA foreign_key_check").fetchall())
        token = cookie(self.worker)
        orders = await api(self.worker, "/api/ops/bookings", token=token)
        self.assertEqual(len(json.loads(orders.body)["bookings"]), 126)
        customer = await api(self.worker, "/api/auth/login", {"username": "mingo_khach1", "password": DEMO_PASSWORD})
        self.assertEqual(customer.status, 200)
        customer_token = next(v.split(";", 1)[0] for k, v in customer.headers if v.startswith("dv_user="))
        own_orders = await api(self.worker, "/api/ops/bookings", token=customer_token)
        self.assertEqual(len(json.loads(own_orders.body)["bookings"]), 11)
        path = "/api/ops/reports?tour=demo-hanoi&from=2026-10-01&to=2026-10-28"
        report = json.loads((await api(self.worker, path, token=token)).body)
        self.assertEqual(report["cash"], [{"month": "2026-10", "collected": 3_600_000, "refunded": 1_200_000}])
        self.assertEqual({b["state"]: b["guests"] for b in report["bookings"]},
                         {"cancelled": 1, "completed": 2, "confirmed": 2, "expired": 2})
        all_report = json.loads((await api(self.worker, "/api/ops/reports?tour=demo-hanoi", token=token)).body)
        self.assertEqual([d["available"] for d in all_report["capacity"]], [6, 2, 2, 4, 1, 0])
        self.assertEqual([c["collected"] for c in all_report["cash"]],
                         [14_400_000, 3_600_000, 3_600_000, 28_800_000, 3_600_000])
        self.assertEqual((await api(self.worker, path, token=customer_token)).status, 403)

    async def test_payment_updates_report_and_details(self):
        from backend.app import local_day

        token = cookie(self.worker)
        day = local_day()
        path = f"/api/ops/reports?tour=demo-hanoi&from={day}&to={day}"
        initial = json.loads((await api(self.worker, path, token=token)).body)["cash"]
        baseline = initial[0] if initial else {"month": day[:7], "collected": 0, "refunded": 0}
        action = "/api/ops/bookings/MGDEMO023/"
        for verb in ("collect", "refund"):
            self.assertEqual((await api(self.worker, action + verb, {}, token)).status, 200)
            baseline["collected" if verb == "collect" else "refunded"] += 2_400_000
            self.assertEqual(json.loads((await api(self.worker, path, token=token)).body)["cash"], [baseline])
        history = json.loads((await api(self.worker, action + "payments", token=token)).body)["payments"]
        self.assertEqual([p["signedAmount"] for p in history], [2_400_000, -2_400_000])
