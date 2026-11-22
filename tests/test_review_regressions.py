import json
from unittest import IsolatedAsyncioTestCase
from unittest.mock import patch

from backend.auth import ADMIN_COOKIE
from scripts.sqlite_worker import LocalWorker
from tests.fixtures import GUEST, ORDER, api, cookie, last_seats


class ReviewRegressions(IsolatedAsyncioTestCase):
    async def test_it05_past_departure_is_rejected_without_holding_seats(self):
        worker = last_seats(day_offset=-1)
        self.addCleanup(worker.database.close)
        day, = worker.database.execute("SELECT day FROM departures").fetchone()

        response = await api(worker, "/api/ops/bookings", {**ORDER, "day": day}, cookie(worker, GUEST))

        self.assertEqual(response.status, 409)
        self.assertEqual(worker.database.execute("SELECT count(*) FROM bookings").fetchone()[0], 0)
        self.assertEqual(worker.database.execute("SELECT reserved FROM departures").fetchone()[0], 0)

    async def test_it06_admin_session_expires_after_eight_hours(self):
        worker = LocalWorker()
        self.addCleanup(worker.database.close)
        start = 1_800_000_000
        with patch("backend.auth.time.time", return_value=start):
            response = await api(worker, "/api/auth/login", {
                "username": worker.settings.username, "password": worker.admin_password,
            })
        self.assertEqual(response.status, 200)
        token = next(
            value.split(";", 1)[0] for key, value in response.headers
            if key.lower() == "set-cookie" and value.startswith(f"{ADMIN_COOKIE}=")
        )

        for elapsed, expected in ((8 * 3600 - 1, True), (8 * 3600 + 1, False)):
            with self.subTest(elapsed=elapsed), patch("backend.auth.time.time", return_value=start + elapsed):
                session = await api(worker, "/api/admin/session", token=token)
                self.assertEqual(json.loads(session.body), {"authenticated": expected})

    async def test_it07_login_is_locked_after_twelve_failures_and_recovers_in_five_minutes(self):
        worker = LocalWorker()
        self.addCleanup(worker.database.close)
        path = "/api/auth/login"
        invalid = {"username": worker.settings.username, "password": "fixture-incorrect"}
        valid = {**invalid, "password": worker.admin_password}
        with patch("backend.services.monotonic", return_value=1000):
            for attempt in range(1, 13):
                response = await api(worker, path, invalid)
                self.assertEqual(response.status, 401, f"Lần nhập sai {attempt}")
        with patch("backend.services.monotonic", return_value=1299):
            self.assertEqual((await api(worker, path, valid)).status, 429)
        with patch("backend.services.monotonic", return_value=1300):
            self.assertEqual((await api(worker, path, valid)).status, 200)
