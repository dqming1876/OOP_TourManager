import json
from unittest import IsolatedAsyncioTestCase

from backend.domain import AppError
from backend.repositories import BookingRepository, ReportsRepository
from backend.services import BookingService, ReportsService
from scripts.sqlite_worker import LocalWorker
from tests.fixtures import ADMIN, GUEST, ORDER, OTHER, REPORT_SEED, TODAY, api, cookie, last_seats


class IntegrationAxis5(IsolatedAsyncioTestCase):
    def setUp(self):
        self.worker = last_seats()
        self.addCleanup(self.worker.database.close)
        self.db = self.worker.database
        self.guest = cookie(self.worker, GUEST)

    async def place(self):
        return await api(self.worker, "/api/ops/bookings", ORDER, self.guest)

    def seats(self):
        return tuple(self.db.execute("SELECT capacity,reserved FROM departures WHERE tour_id='axis5-tour'").fetchone())

    async def test_it01_last_seats(self):
        response = await self.place()
        self.assertEqual(response.status, 201, "Ba khách phải đặt được khi đợt còn đúng ba chỗ")
        booking_id = json.loads(response.body)["id"]
        order = self.db.execute("SELECT unit_price,title,adults,children,status FROM bookings WHERE id = ?",
                                (booking_id,)).fetchone()
        self.assertEqual(tuple(order), (500_000, "Tour thử trục 5", 2, 1, "pending"))
        self.assertEqual(self.seats(), (3, 3))
        self.assertEqual((await self.place()).status, 409)
        self.assertEqual(self.db.execute("SELECT count(*) FROM bookings").fetchone()[0], 1)

    async def test_it02_reservation_rollback(self):
        self.db.executescript("""
            CREATE TRIGGER axis5_fail_reserve BEFORE UPDATE OF reserved ON departures
            WHEN NEW.tour_id = 'axis5-tour' AND NEW.reserved > OLD.reserved
            BEGIN SELECT RAISE(ABORT, 'axis5:test reserve failure'); END;
        """)
        failed = await self.place()
        self.assertEqual(failed.status, 500)
        self.assertEqual(json.loads(failed.body)["error"], "Không thể xử lý yêu cầu lúc này.")
        self.assertEqual(self.db.execute("SELECT count(*) FROM bookings").fetchone()[0], 0)
        self.assertEqual(self.seats(), (3, 0))
        self.db.execute("DROP TRIGGER axis5_fail_reserve")
        self.assertEqual((await self.place()).status, 201)
        self.assertEqual(self.seats(), (3, 3))

    async def test_it03_report_boundaries(self):
        report_worker = LocalWorker(seed=REPORT_SEED, today=lambda: "2028-05-01")
        self.addCleanup(report_worker.database.close)
        service = ReportsService(ReportsRepository(report_worker.db), ADMIN, "2028-05-01")
        params = {"from": "2028-05-10", "to": "2028-05-12", "tour": "report-tour"}
        result = await service.load(params)
        self.assertEqual(result["cash"], [{"month": "2028-05", "collected": 2_500_000, "refunded": 1_000_000}])
        self.assertEqual([(d["day"], d["reserved"], d["available"]) for d in result["capacity"]],
                         [("2028-05-10", 2, 4), ("2028-05-12", 3, 3)])
        self.assertEqual({r["state"]: (r["orders"], r["guests"]) for r in result["bookings"]},
                         {"cancelled": (1, 1), "confirmed": (1, 2), "pending": (1, 3)})
        single = await service.load({**params, "from": "2028-05-12"})
        self.assertEqual(single["cash"], [{"month": "2028-05", "collected": 0, "refunded": 1_000_000}])

    async def test_it04_service_authorization(self):
        booking_id = json.loads((await self.place()).body)["id"]
        repository = BookingRepository(self.worker.db)
        bookings = BookingService(repository, GUEST, TODAY)
        reports = ReportsService(ReportsRepository(self.worker.db), GUEST, TODAY)
        before = len(self.worker.db.queries)
        for operation in (bookings.update_booking(booking_id, "collect"), reports.load({})):
            with self.assertRaises(AppError) as error:
                await operation
            self.assertEqual(error.exception.status, 403)
        self.assertEqual(len(self.worker.db.queries), before)
        with self.assertRaises(AppError) as error:
            await BookingService(repository, OTHER, TODAY).update_booking(booking_id, "cancel")
        self.assertEqual(error.exception.status, 409)
        self.assertEqual(tuple(self.db.execute("SELECT paid,status FROM bookings WHERE id=?", (booking_id,)).fetchone()),
                         (0, "pending"))
        self.assertEqual(self.seats(), (3, 3))
        self.assertEqual(self.db.execute("SELECT count(*) FROM payment_events").fetchone()[0], 0)
