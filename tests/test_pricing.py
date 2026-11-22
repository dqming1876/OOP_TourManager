from unittest import IsolatedAsyncioTestCase, TestCase

from backend.domain import Booking
from backend.pricing import PercentageDiscount, StandardPrice
from backend.repositories import BookingRepository
from tests.fixtures import GUEST_ID, ORDER, TODAY, last_seats


class TestPricingPolicy(TestCase):
    def test_policy_keeps_full_price_or_rounds_down_to_positive_vnd(self):
        self.assertEqual(StandardPrice().unit_price(500_000), 500_000)
        self.assertEqual(PercentageDiscount(10).unit_price(101), 90)
        self.assertEqual(PercentageDiscount(99).unit_price(1), 1)
        for percent in (0, 100, 1.5, True):
            with self.subTest(percent=percent), self.assertRaises(ValueError):
                PercentageDiscount(percent)


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
