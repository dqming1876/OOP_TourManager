from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from bookings.models import Booking
from catalog.models import Departure, Tour

from .models import Customer


class CustomerTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.sales = User.objects.create_user("customerSales")
        cls.sales.groups.add(Group.objects.get_or_create(name="Sales")[0])
        cls.operator = User.objects.create_user("customerOperator")
        cls.operator.groups.add(Group.objects.get_or_create(name="Operator")[0])
        cls.customer = Customer.objects.create(full_name="Khách hàng mẫu", phone="0901234567")
        tour = Tour.objects.create(code="CUST", name="Tour thử", days=2, nights=1, destination="Hạ Long", base_price=Decimal("2450000"))
        cls.departure = Departure.objects.create(tour=tour, start_date=date(2026, 12, 5), end_date=date(2026, 12, 6), max_seats=29, price=Decimal("2450000"))

    def setUp(self):
        self.client.force_login(self.sales)

    def test_sales_creates_updates_and_deletes_customer(self):
        data = {"full_name": "Khách mới", "phone": "0900000999", "email": "new@example.com", "id_number": "", "address": "Hà Nội", "note": "Ăn chay"}
        response = self.client.post("/customers/create/", data)
        self.assertEqual(response.status_code, 302)
        customer = Customer.objects.get(phone="0900000999")
        data["full_name"] = "Khách đã sửa"
        response = self.client.post(reverse("customers:customer_update", args=[customer.pk]), data, follow=True)
        self.assertContains(response, "Khách đã sửa")
        self.assertContains(response, "thành công")
        delete_url = reverse("customers:customer_delete", args=[customer.pk])
        self.assertContains(self.client.get(delete_url), "Xác nhận xóa")
        self.assertTrue(Customer.objects.filter(pk=customer.pk).exists())
        self.assertEqual(self.client.post(delete_url).status_code, 302)
        self.assertFalse(Customer.objects.filter(pk=customer.pk).exists())

    def test_operator_is_forbidden_for_all_customer_actions(self):
        self.client.force_login(self.operator)
        for action in ("list", "create", "detail", "update", "delete"):
            args = [self.customer.pk] if action in ("detail", "update", "delete") else []
            url = reverse(f"customers:customer_{action}", args=args)
            self.assertEqual(self.client.get(url).status_code, 403)
            self.assertEqual(self.client.post(url, {}).status_code, 403)

    def test_empty_history_is_valid(self):
        response = self.client.get(reverse("customers:customer_detail", args=[self.customer.pk]))
        self.assertContains(response, "Chưa có booking nào.")

    def test_history_is_paginated_scoped_to_customer_and_read_only(self):
        for index in range(12):
            Booking.objects.create(code=f"C{index:02}", customer=self.customer, departure=self.departure, total_amount=Decimal("2450000"), created_by=self.sales)
        other = Customer.objects.create(full_name="Khách khác", phone="0900000100")
        Booking.objects.create(code="OTHER", customer=other, departure=self.departure, total_amount=Decimal("2450000"), created_by=self.sales)
        url = reverse("customers:customer_detail", args=[self.customer.pk])
        response = self.client.get(url)
        self.assertEqual(response.context["paginator"].count, 12)
        self.assertEqual(len(response.context["bookings"]), 10)
        self.assertNotContains(response, "OTHER")
        self.assertEqual(len(self.client.get(url, {"page": 2}).context["bookings"]), 2)
        self.assertEqual(Booking.objects.count(), 13)

    def test_customer_with_booking_cannot_be_deleted(self):
        Booking.objects.create(code="PROTECTED", customer=self.customer, departure=self.departure, total_amount=Decimal("2450000"), created_by=self.sales)
        response = self.client.post(reverse("customers:customer_delete", args=[self.customer.pk]))
        self.assertContains(response, "Không thể xóa")
        self.assertTrue(Customer.objects.filter(pk=self.customer.pk).exists())

    def test_search_phone_and_paginate(self):
        for index in range(12):
            Customer.objects.create(full_name=f"Khách {index:02}", phone=f"08888888{index:02}")
        response = self.client.get("/customers/", {"q": "08888888"})
        self.assertEqual(response.context["paginator"].count, 12)
        self.assertEqual(len(response.context["object_list"]), 10)
        self.assertContains(response, "q=08888888&amp;page=2")
        self.assertEqual(len(self.client.get("/customers/", {"q": "08888888", "page": 2}).context["object_list"]), 2)

    def test_invalid_email_does_not_save(self):
        response = self.client.post("/customers/create/", {"full_name": "Khách mới", "phone": "0900000000", "email": "invalid"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("email", response.context["form"].errors)
        self.assertFalse(Customer.objects.filter(full_name="Khách mới").exists())
