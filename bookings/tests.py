from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from catalog.models import Departure, Tour
from customers.models import Customer

from .models import Booking, Payment


class AmountAndSeatTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user("testUser")
        cls.customer = Customer.objects.create(full_name="Khách mẫu", phone="0900000000")
        tour = Tour.objects.create(code="TEST", name="Tour mẫu", days=2, nights=1, destination="Hạ Long", base_price=Decimal("2000000"))
        cls.departure = Departure.objects.create(tour=tour, start_date=date(2026, 12, 5), end_date=date(2026, 12, 6), max_seats=20, price=Decimal("2000000"))

    def make_booking(self, code, adults, children, status=Booking.Status.PENDING):
        return Booking.objects.create(code=code, customer=self.customer, departure=self.departure, num_adults=adults, num_children=children, total_amount=Decimal("10000000"), status=status, created_by=self.user)

    def test_empty_departure_and_unpaid_booking(self):
        self.assertEqual(self.departure.booked_seats, 0)
        self.assertEqual(self.departure.available_seats, 20)
        booking = self.make_booking("B01", 1, 0)
        self.assertEqual(booking.paid_amount, Decimal("0"))
        self.assertIsInstance(booking.paid_amount, Decimal)
        self.assertEqual(booking.remaining_amount, Decimal("10000000"))

    def test_counts_all_non_cancelled_statuses(self):
        self.make_booking("B01", 2, 1)
        self.make_booking("B02", 3, 2, Booking.Status.CONFIRMED)
        self.make_booking("B03", 1, 0, Booking.Status.COMPLETED)
        self.make_booking("B04", 5, 3, Booking.Status.CANCELLED)
        self.assertEqual(self.departure.booked_seats, 9)
        self.assertEqual(self.departure.available_seats, 11)

    def test_paid_and_remaining_amounts_use_decimal(self):
        booking = self.make_booking("B01", 2, 0)
        for amount, kind in [("3000000", Payment.PaymentType.DEPOSIT), ("2000000", Payment.PaymentType.INSTALLMENT)]:
            Payment.objects.create(booking=booking, amount=Decimal(amount), payment_type=kind, method=Payment.Method.TRANSFER, received_by=self.user)
        self.assertEqual(booking.paid_amount, Decimal("5000000"))
        self.assertEqual(booking.remaining_amount, Decimal("5000000"))
        self.assertIsInstance(booking.paid_amount, Decimal)

    def test_properties_are_derived_without_clamping_or_state_updates(self):
        booking = self.make_booking("B01", 21, 0)
        self.assertEqual(self.departure.available_seats, -1)
        Payment.objects.create(booking=booking, amount=Decimal("11000000"), payment_type=Payment.PaymentType.FULL, method=Payment.Method.CASH, received_by=self.user)
        self.assertEqual(booking.remaining_amount, Decimal("-1000000"))
        booking.refresh_from_db()
        self.departure.refresh_from_db()
        self.assertEqual(booking.status, Booking.Status.PENDING)
        self.assertEqual(self.departure.status, Departure.Status.OPEN)
