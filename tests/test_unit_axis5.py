from dataclasses import replace
from types import SimpleNamespace
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock

from backend.domain import (AppError, Booking, BookingAction, Departure, PaymentEvent,
                            Tour, TRANSITIONS, ValidationError)
from backend.services import BookingService, ReportsService, TourCatalogService
from tests.fixtures import ADMIN, GUEST, GUEST_ID, ORDER, TODAY, TOUR


class UnitAxis5(IsolatedAsyncioTestCase):
    def order(self, **changes):
        return Booking.request("order-1", GUEST_ID, {**ORDER, **changes})

    def test_booking_action_rules(self):
        self.assertEqual({action.value for action in BookingAction}, {"confirm", "collect", "refund", "cancel"})
        self.assertEqual(set(TRANSITIONS), set(BookingAction))
        for action in TRANSITIONS:
            with self.subTest(action=action):
                self.assertIsInstance(action, BookingAction)
                self.assertIs(Booking.transition(action.value, False), TRANSITIONS[action])
        self.assertEqual(Booking.transition(BookingAction.CANCEL, True).also_from, "pending")
        self.assertEqual(Booking.transition("cancel", False).also_from, "confirmed")

    def test_invalid_booking_action(self):
        for value in ("delete", "", None, []):
            with self.subTest(value=value), self.assertRaises(ValidationError):
                Booking.transition(value, False)

    def test_ut01_adults(self):
        self.assertEqual([self.order(adults=n, children=0).people for n in (1, 100)], [1, 100])
        for n in (0, 101, True):
            with self.assertRaises(AppError) as error:
                self.order(adults=n)
            self.assertEqual((error.exception.status, error.exception.field), (400, "adults"))

    def test_ut02_children(self):
        self.assertEqual([self.order(adults=1, children=n).people for n in (0, 99)], [1, 100])
        for n in (-1, 100):
            with self.assertRaises(AppError) as error:
                self.order(children=n)
            self.assertEqual(error.exception.field, "children")

    def test_ut03_phone(self):
        self.assertEqual(self.order(phone=" 090-123-4567 ").phone, "090-123-4567")
        for phone in ("090123456X", "1234567--"):
            with self.assertRaises(AppError) as error:
                self.order(phone=phone)
            self.assertEqual(error.exception.field, "phone")

    def test_ut04_snapshot_price(self):
        draft = self.order()
        self.assertEqual(replace(draft, unit_price=500_000).total, 1_500_000)
        with self.assertRaises(AppError) as error:
            _ = draft.total
        self.assertEqual(error.exception.status, 409)

    def test_ut05_capacity(self):
        self.assertEqual([Departure("t", TODAY, n).remaining for n in (1, 100)], [1, 100])
        for n in (0, 101):
            with self.assertRaises(AppError) as error:
                Departure("t", TODAY, n)
            self.assertEqual(error.exception.field, "capacity")

    async def test_ut06_leap_day(self):
        port = SimpleNamespace(create_departure=AsyncMock(return_value=True))
        service = TourCatalogService(port, ADMIN, TODAY)
        for day in ("2028-02-28", "2028-02-30"):
            with self.assertRaises(AppError) as error:
                await service.save_departure("t", {"day": day, "capacity": 5})
            self.assertEqual(error.exception.field, "day")
        await service.save_departure("t", {"day": TODAY, "capacity": 5})
        port.create_departure.assert_awaited_once_with(Departure("t", TODAY, 5))

    async def test_ut07_denied_before_repository(self):
        port = SimpleNamespace(update_booking=AsyncMock())
        with self.assertRaises(AppError) as error:
            await BookingService(port, GUEST, TODAY).update_booking("order-1", "collect")
        self.assertEqual(error.exception.status, 403)
        port.update_booking.assert_not_called()

    async def test_ut08_no_seats(self):
        port = SimpleNamespace(place_booking=AsyncMock(return_value=False))
        with self.assertRaises(AppError) as error:
            await BookingService(port, GUEST, TODAY).place_booking(ORDER)
        self.assertEqual((error.exception.status, error.exception.field), (409, "day"))
        port.place_booking.assert_awaited_once()
        booking, cutoff = port.place_booking.call_args.args
        self.assertEqual((booking.user_id, booking.people, cutoff), (GUEST_ID, 3, TODAY))

    async def test_ut09_own_pending_only(self):
        port = SimpleNamespace(update_booking=AsyncMock(return_value=True))
        await BookingService(port, GUEST, TODAY).update_booking("order-1", "cancel")
        booking_id, rule, owner, cutoff = port.update_booking.call_args.args
        self.assertEqual((booking_id, rule.before, rule.also_from, rule.after, rule.paid, owner, cutoff),
                         ("order-1", "pending", "pending", "cancelled", False, GUEST_ID, TODAY))

    async def test_ut10_payment_transitions(self):
        port = SimpleNamespace(update_booking=AsyncMock(return_value=True))
        service = BookingService(port, ADMIN, TODAY)
        await service.update_booking("order-1", "collect")
        await service.update_booking("order-1", "refund")
        self.assertEqual([(r.before, r.after, r.paid, r.next_paid, o) for _, r, o, _ in
                          (call.args for call in port.update_booking.call_args_list)],
                         [("confirmed", "confirmed", False, True, None),
                          ("confirmed", "confirmed", True, False, None)])

    async def test_ut11_report_range(self):
        port = SimpleNamespace(load=AsyncMock(return_value={"cash": []}))
        service = ReportsService(port, ADMIN, TODAY)
        with self.assertRaises(AppError) as error:
            await service.load({"from": "2028-03-01", "to": TODAY})
        self.assertEqual(error.exception.status, 400)
        await service.load({"from": TODAY, "to": TODAY, "tour": "t"})
        port.load.assert_awaited_once_with(TODAY, TODAY, "t", TODAY)

    def test_ut12_itinerary(self):
        tour = Tour.request("t", TOUR)
        self.assertEqual([stop.write_row() for stop in tour.stops], [
            {"dayNumber": 1, "place": "Hồ Gươm", "activity": "Đi bộ"},
            {"dayNumber": 2, "place": "Bảo tàng Hà Nội", "activity": "Tham quan"},
        ])
        with self.assertRaises(AppError):
            Tour.request("t", {**TOUR, "itinerary": ["Đi bộ"]})

    def test_ut13_payments(self):
        self.assertEqual([PaymentEvent(TODAY, "collect", 1_000_000).signed_amount,
                          PaymentEvent(TODAY, "refund", 400_000).signed_amount], [1_000_000, -400_000])
        with self.assertRaises(AppError) as error:
            PaymentEvent(TODAY, "refund", 0)
        self.assertEqual(error.exception.field, "amount")
