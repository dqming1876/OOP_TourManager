import json
from unittest import IsolatedAsyncioTestCase, TestCase

from backend.domain import Booking
from backend.pricing import PercentageDiscount, StandardPrice, pricing_from_percent
from backend.repositories import BookingRepository
from scripts.sqlite_worker import LocalWorker
from tests.fixtures import FUTURE, GUEST, GUEST_ID, ORDER, TODAY, api, cookie, last_seats


class TestPricingPolicy(TestCase):
    def test_policy_keeps_full_price_or_rounds_down_to_positive_vnd(self):
        self.assertEqual(StandardPrice().unit_price(500_000), 500_000)
        self.assertEqual(PercentageDiscount(10).unit_price(101), 90)
        self.assertEqual(PercentageDiscount(99).unit_price(1), 1)
        for percent in (0, 100, 1.5, True):
            with self.subTest(percent=percent), self.assertRaises(ValueError):
                PercentageDiscount(percent)

    def test_pricing_from_percent_selects_runtime_policy(self):
        self.assertIsInstance(pricing_from_percent(None), StandardPrice)
        self.assertIsInstance(pricing_from_percent(""), StandardPrice)
        self.assertIsInstance(pricing_from_percent("0"), StandardPrice)
        self.assertEqual(pricing_from_percent("15"), PercentageDiscount(15))
        self.assertEqual(pricing_from_percent(20), PercentageDiscount(20))
        for invalid in ("-5", "100", "abc", True):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                pricing_from_percent(invalid)


class TestBookingPriceSnapshot(IsolatedAsyncioTestCase):
    def setUp(self):
        self.worker = last_seats()
        self.addCleanup(self.worker.database.close)
        self.booking = Booking.request("pricing-test", GUEST_ID, ORDER)

    async def test_discount_is_saved_without_changing_total_calculation(self):
        repository = BookingRepository(self.worker.db, PercentageDiscount(10))
        self.assertTrue(await repository.place_booking(self.booking, TODAY))
        self.worker.database.execute("UPDATE tours SET price = 600000 WHERE id = ?", (ORDER["tourId"],))

        order, = await repository.list_bookings(GUEST_ID)
        self.assertEqual(order["unitPrice"], 450_000)
        self.assertEqual(order["total"], 1_350_000)

    async def test_price_change_between_read_and_insert_does_not_reserve_seats(self):
        class PriceChangeBeforeWrite:
            async def first(inner, sql, *values):
                return await self.worker.db.first(sql, *values)

            async def execute(inner, sql, *values):
                self.worker.database.execute("UPDATE tours SET price = 600000 WHERE id = ?", (ORDER["tourId"],))
                return await self.worker.db.execute(sql, *values)

        repository = BookingRepository(PriceChangeBeforeWrite(), PercentageDiscount(10))
        self.assertFalse(await repository.place_booking(self.booking, TODAY))
        self.assertEqual(self.worker.database.execute("SELECT count(*) FROM bookings").fetchone()[0], 0)
        self.assertEqual(self.worker.database.execute("SELECT reserved FROM departures").fetchone()[0], 0)

    async def test_runtime_http_wiring_applies_pricing_policy_to_catalog_and_booking(self):
        worker = LocalWorker(
            today=lambda: TODAY,
            pricing=PercentageDiscount(10),
            seed=f"""
                INSERT INTO accounts (id,username,name,password_hash,salt)
                VALUES ('axis5-guest','axis5_guest','Khách thử','fixture-only','fixture-only');
                INSERT INTO tours (id,price,title) VALUES ('axis5-tour',500000,'Tour thử khuyến mãi');
                INSERT INTO departures (tour_id,day,capacity) VALUES ('axis5-tour','{FUTURE}',3);
            """,
        )
        self.addCleanup(worker.database.close)
        token = cookie(worker, GUEST)
        tours = json.loads((await api(worker, "/api/ops/tours")).body)["tours"]
        promo_tour = next(item for item in tours if item["id"] == "axis5-tour")
        self.assertEqual((promo_tour["price"], promo_tour["bookingPrice"]), (500_000, 450_000))
        stale = await api(worker, "/api/ops/bookings", ORDER, token)
        self.assertEqual(stale.status, 409)
        created = await api(worker, "/api/ops/bookings", {**ORDER, "expectedPrice": 450_000}, token)
        self.assertEqual(created.status, 201)
        orders = json.loads((await api(worker, "/api/ops/bookings", token=token)).body)["bookings"]
        self.assertEqual((orders[0]["unitPrice"], orders[0]["total"]), (450_000, 1_350_000))
