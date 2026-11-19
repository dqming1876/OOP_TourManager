from datetime import date
from decimal import Decimal
from io import StringIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.db import IntegrityError, connection
from django.test import Client, TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from bookings.models import Booking
from customers.models import Customer

from .models import Departure, Guide, Service, Supplier, Tour, TourItinerary, Vehicle


def make_user(username, role=None, superuser=False):
    user = get_user_model().objects.create_user(username, is_superuser=superuser, is_staff=superuser)
    if role:
        user.groups.add(Group.objects.get_or_create(name=role)[0])
    return user


def tour_payload(code="NEW", days=2, rows=None, initial=0):
    if rows is None:
        rows = [{"day_number": n, "title": f"Ngày {n}", "content": f"Tham quan ngày {n}"} for n in range(1, days + 1)]
    data = {
        "code": code, "name": "Tour thử nghiệm", "days": days, "nights": days - 1,
        "destination": "Hạ Long", "base_price": "2450000", "description": "Mô tả thử nghiệm", "status": "ACTIVE",
        "itineraries-TOTAL_FORMS": len(rows), "itineraries-INITIAL_FORMS": initial,
        "itineraries-MIN_NUM_FORMS": 1, "itineraries-MAX_NUM_FORMS": 1000,
    }
    for index, row in enumerate(rows):
        for name, value in row.items():
            data[f"itineraries-{index}-{name}"] = value
    return data


class CatalogFixture(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_catalog", stdout=StringIO())
        cls.operator = make_user("operatorTest", "Operator")
        cls.sales = make_user("salesTest", "Sales")
        cls.admin = make_user("adminTest", "Admin")
        cls.superuser = make_user("superTest", superuser=True)
        cls.no_role = make_user("noRole")

    def setUp(self):
        self.client.force_login(self.operator)


class CatalogAccessTests(CatalogFixture):
    def test_anonymous_redirects_for_every_catalog(self):
        self.client.logout()
        for name in ("supplier", "service", "guide", "vehicle", "tour", "departure"):
            response = self.client.get(reverse(f"catalog:{name}_list"))
            self.assertEqual(response.status_code, 302)
            self.assertIn("/login/?next=", response.url)

    def test_operator_can_open_every_catalog_action(self):
        for name, model in [("supplier", Supplier), ("service", Service), ("guide", Guide), ("vehicle", Vehicle), ("tour", Tour), ("departure", Departure)]:
            for action in ("list", "detail", "create", "update", "delete"):
                args = [model.objects.first().pk] if action in ("detail", "update", "delete") else []
                with self.subTest(name=name, action=action):
                    self.assertEqual(self.client.get(reverse(f"catalog:{name}_{action}", args=args)).status_code, 200)

    def test_sales_cannot_access_private_catalogs_even_by_post(self):
        self.client.force_login(self.sales)
        for name, model in [("supplier", Supplier), ("service", Service), ("guide", Guide), ("vehicle", Vehicle)]:
            for action in ("list", "detail", "create", "update", "delete"):
                args = [model.objects.first().pk] if action in ("detail", "update", "delete") else []
                url = reverse(f"catalog:{name}_{action}", args=args)
                with self.subTest(name=name, action=action):
                    self.assertEqual(self.client.get(url).status_code, 403)
                    self.assertEqual(self.client.post(url, {}).status_code, 403)

    def test_sales_only_reads_tours_and_departures(self):
        self.client.force_login(self.sales)
        for name, model in [("tour", Tour), ("departure", Departure)]:
            self.assertEqual(self.client.get(reverse(f"catalog:{name}_list")).status_code, 200)
            detail = self.client.get(reverse(f"catalog:{name}_detail", args=[model.objects.first().pk]))
            self.assertEqual(detail.status_code, 200)
            self.assertFalse(detail.context["can_manage"])
            for action in ("create", "update", "delete"):
                args = [] if action == "create" else [model.objects.first().pk]
                url = reverse(f"catalog:{name}_{action}", args=args)
                self.assertEqual(self.client.get(url).status_code, 403)
                self.assertEqual(self.client.post(url, {}).status_code, 403)

    def test_admin_group_and_superuser_bypass_restrictions(self):
        for user in (self.admin, self.superuser):
            self.client.force_login(user)
            for url in ("/suppliers/", "/tours/create/", "/customers/", "/customers/create/"):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_no_role_gets_custom_forbidden_page(self):
        self.client.force_login(self.no_role)
        response = self.client.get("/tours/")
        self.assertContains(response, "Bạn chưa được cấp quyền", status_code=403)

    def test_create_requires_csrf(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.operator)
        self.assertEqual(client.post("/suppliers/create/", {"name": "NCC"}).status_code, 403)

    def test_nonexistent_object_is_404(self):
        self.assertEqual(self.client.get("/tours/999999/").status_code, 404)


class CatalogCrudTests(CatalogFixture):
    def test_create_update_confirm_and_delete_for_simple_catalogs(self):
        cases = [
            ("supplier", Supplier, {"name": "Nhà cung cấp mới", "supplier_type": "Lưu trú", "phone": "0901234567", "email": "new@example.com", "address": "Hà Nội"}, "name"),
            ("service", Service, {"name": "Dịch vụ mới", "service_type": "MEAL", "supplier": Supplier.objects.first().pk, "unit_price": "123000", "unit": "suất", "description": "Thực đơn"}, "name"),
            ("guide", Guide, {"full_name": "HDV mới", "phone": "0901234567", "languages": "Tiếng Việt", "status": "ACTIVE"}, "full_name"),
            ("vehicle", Vehicle, {"plate_number": "29B-999.99", "vehicle_type": "Xe 16 chỗ", "seats": "16", "driver_name": "Tài xế mới", "driver_phone": "0901234567", "status": "ACTIVE"}, "driver_name"),
            ("departure", Departure, {"tour": Tour.objects.first().pk, "start_date": "2027-01-01", "end_date": "2027-01-03", "max_seats": "20", "price": "1230000", "status": "OPEN"}, "price"),
        ]
        for name, model, data, update_field in cases:
            with self.subTest(model=name):
                before = set(model.objects.values_list("pk", flat=True))
                response = self.client.post(reverse(f"catalog:{name}_create"), data)
                self.assertEqual(response.status_code, 302)
                obj = model.objects.exclude(pk__in=before).get()
                self.assertRedirects(response, reverse(f"catalog:{name}_detail", args=[obj.pk]))
                updated = dict(data)
                updated[update_field] = "2340000" if update_field == "price" else "Đã sửa"
                response = self.client.post(reverse(f"catalog:{name}_update", args=[obj.pk]), updated)
                self.assertEqual(response.status_code, 302)
                obj.refresh_from_db()
                self.assertEqual(str(getattr(obj, update_field)), updated[update_field])
                delete_url = reverse(f"catalog:{name}_delete", args=[obj.pk])
                self.assertContains(self.client.get(delete_url), "Xác nhận xóa")
                self.assertTrue(model.objects.filter(pk=obj.pk).exists())
                response = self.client.post(delete_url, follow=True)
                self.assertFalse(model.objects.filter(pk=obj.pk).exists())
                self.assertContains(response, "thành công")

    def test_search_and_pagination_preserve_query(self):
        for index in range(13):
            Supplier.objects.create(name=f"A&B {index:02}", supplier_type="Khác", phone="0901234567")
        response = self.client.get("/suppliers/", {"q": "A&B"})
        self.assertEqual(len(response.context["object_list"]), 10)
        self.assertEqual(response.context["paginator"].count, 13)
        self.assertContains(response, "q=A%26B&amp;page=2")
        response = self.client.get("/suppliers/", {"q": "A&B", "page": 2})
        self.assertEqual(len(response.context["object_list"]), 3)

    def test_service_searches_supplier_name(self):
        response = self.client.get("/services/", {"q": "Mường Hoa"})
        self.assertEqual(response.context["paginator"].count, 1)

    def test_empty_search_results_render(self):
        for url in ("/suppliers/", "/services/", "/guides/", "/vehicles/", "/tours/", "/departures/"):
            self.assertContains(self.client.get(url, {"q": "noMatchXYZ"}), "Chưa có dữ liệu phù hợp.")

    def test_protected_supplier_and_tour_cannot_be_deleted(self):
        for name, obj in [("supplier", Service.objects.first().supplier), ("tour", Departure.objects.first().tour)]:
            response = self.client.post(reverse(f"catalog:{name}_delete", args=[obj.pk]))
            self.assertContains(response, "Không thể xóa vì bản ghi")
            self.assertTrue(type(obj).objects.filter(pk=obj.pk).exists())

    def test_duplicate_plate_and_negative_price_are_invalid(self):
        vehicle = Vehicle.objects.first()
        data = {"plate_number": vehicle.plate_number, "vehicle_type": "Xe", "seats": 16, "driver_name": "Tài xế", "driver_phone": "0901234567", "status": "ACTIVE"}
        response = self.client.post("/vehicles/create/", data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("plate_number", response.context["form"].errors)
        response = self.client.post("/services/create/", {"name": "Giá âm", "service_type": "MEAL", "supplier": Supplier.objects.first().pk, "unit_price": "-1", "unit": "suất"})
        self.assertIn("unit_price", response.context["form"].errors)

    def test_user_text_is_escaped(self):
        supplier = Supplier.objects.create(name="<script>alert(1)</script>", supplier_type="Khác", phone="0901234567")
        response = self.client.get(reverse("catalog:supplier_detail", args=[supplier.pk]))
        self.assertContains(response, "&lt;script&gt;alert(1)&lt;/script&gt;")
        self.assertNotContains(response, "<script>alert(1)</script>")


class TourFormsetTests(CatalogFixture):
    def test_create_tour_with_every_day_and_delete_unused_tour(self):
        response = self.client.post("/tours/create/", tour_payload())
        self.assertEqual(response.status_code, 302)
        tour = Tour.objects.get(code="NEW")
        self.assertEqual(list(tour.itineraries.values_list("day_number", flat=True)), [1, 2])
        detail = self.client.get(response.url)
        self.assertContains(detail, "Tham quan ngày 1")
        self.assertContains(detail, "Tour chưa có lịch khởi hành.")
        self.assertEqual(self.client.post(reverse("catalog:tour_delete", args=[tour.pk])).status_code, 302)
        self.assertFalse(TourItinerary.objects.filter(tour_id=tour.pk).exists())

    def test_missing_duplicate_or_out_of_range_day_does_not_create_tour(self):
        for numbers in ([1], [1, 1], [1, 3], [0, 2]):
            rows = [{"day_number": n, "title": "Ngày", "content": "Nội dung"} for n in numbers]
            response = self.client.post("/tours/create/", tour_payload(rows=rows))
            self.assertEqual(response.status_code, 200)
            self.assertFalse(Tour.objects.filter(code="NEW").exists())
            self.assertTrue(response.context["itinerary_formset"].errors or response.context["itinerary_formset"].non_form_errors())

    def test_invalid_parent_keeps_bound_formset(self):
        data = tour_payload()
        data["name"] = ""
        response = self.client.post("/tours/create/", data)
        self.assertIn("name", response.context["form"].errors)
        self.assertTrue(response.context["itinerary_formset"].is_bound)
        self.assertContains(response, "Tham quan ngày 1")

    def test_management_form_is_required(self):
        data = tour_payload()
        del data["itineraries-TOTAL_FORMS"]
        response = self.client.post("/tours/create/", data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Tour.objects.filter(code="NEW").exists())

    def test_duplicate_tour_code_is_invalid(self):
        response = self.client.post("/tours/create/", tour_payload(code=Tour.objects.first().code))
        self.assertIn("code", response.context["form"].errors)

    def test_update_can_swap_day_numbers(self):
        tour = Tour.objects.get(code="HNHL2N1D")
        items = list(tour.itineraries.all())
        rows = [{"id": item.pk, "day_number": 2 - index, "title": f"Nội dung cũ {index}", "content": "Đã cập nhật"} for index, item in enumerate(items)]
        response = self.client.post(reverse("catalog:tour_update", args=[tour.pk]), tour_payload(code=tour.code, rows=rows, initial=2))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(list(tour.itineraries.values_list("title", flat=True)), ["Nội dung cũ 1", "Nội dung cũ 0"])

    def test_delete_row_and_reduce_number_of_days(self):
        tour = Tour.objects.get(code="HNHL2N1D")
        items = list(tour.itineraries.all())
        rows = [{"id": items[0].pk, "day_number": 1, "title": "Còn lại", "content": "Nội dung"}, {"id": items[1].pk, "DELETE": "on"}]
        response = self.client.post(reverse("catalog:tour_update", args=[tour.pk]), tour_payload(code=tour.code, days=1, rows=rows, initial=2))
        self.assertEqual(response.status_code, 302)
        tour.refresh_from_db()
        self.assertEqual(tour.days, 1)
        self.assertEqual(tour.itineraries.count(), 1)

    def test_cannot_submit_itinerary_id_of_another_tour(self):
        other_item = TourItinerary.objects.exclude(tour__code="HNHL2N1D").first()
        tour = Tour.objects.get(code="HNHL2N1D")
        rows = [{"id": other_item.pk, "day_number": 1, "title": "Thử", "content": "Thử"}]
        response = self.client.post(reverse("catalog:tour_update", args=[tour.pk]), tour_payload(code=tour.code, days=1, rows=rows, initial=1))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(tour.itineraries.count(), 2)
        self.assertTrue(TourItinerary.objects.filter(pk=other_item.pk).exists())

    def test_database_failure_rolls_back_parent_and_children(self):
        tour = Tour.objects.get(code="HNHL2N1D")
        original_name = tour.name
        original_items = list(tour.itineraries.values_list("day_number", "title", "content"))
        rows = [{"id": item.pk, "day_number": item.day_number, "title": "Đã sửa", "content": "Mới"} for item in tour.itineraries.all()]
        with patch("catalog.views.TourItinerary.objects.bulk_create", side_effect=IntegrityError("Kiểm tra rollback")):
            with self.assertRaises(IntegrityError):
                self.client.post(reverse("catalog:tour_update", args=[tour.pk]), tour_payload(code=tour.code, rows=rows, initial=2))
        tour.refresh_from_db()
        self.assertEqual(tour.name, original_name)
        self.assertEqual(list(tour.itineraries.values_list("day_number", "title", "content")), original_items)


class DepartureTests(CatalogFixture):
    def make_booking(self, code="BK1", status="PENDING", adults=2, children=1):
        departure = Departure.objects.get(tour__code="HNHL2N1D", start_date=date(2026, 12, 5))
        return Booking.objects.create(code=code, customer=Customer.objects.first(), departure=departure, num_adults=adults, num_children=children, total_amount=Decimal("5000000"), status=status, created_by=self.operator)

    def test_combined_filters_are_inclusive_on_start_date(self):
        departure = Departure.objects.get(tour__code="HNHL2N1D", start_date=date(2026, 12, 5))
        departure.status = "FULL"
        departure.save(update_fields=["status"])
        response = self.client.get("/departures/", {"q": "HNHL", "status": "FULL", "start_date": "2026-12-05", "end_date": "2026-12-05"})
        self.assertEqual([obj.pk for obj in response.context["object_list"]], [departure.pk])

    def test_invalid_date_range_value_or_status_does_not_crash(self):
        for params in ({"start_date": "2026-12-20", "end_date": "2026-12-01"}, {"start_date": "not-a-date"}, {"status": "INVALID"}):
            response = self.client.get("/departures/", params)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.context["filter_form"].errors)
            self.assertEqual(response.context["paginator"].count, 0)

    def test_seat_totals_and_related_bookings_are_read_only(self):
        first = self.make_booking()
        self.make_booking("BK2", "CONFIRMED", 1, 0)
        self.make_booking("BK3", "COMPLETED", 1, 0)
        self.make_booking("BK4", "CANCELLED", 8, 2)
        response = self.client.get("/departures/")
        self.assertContains(response, "5/29")
        detail = self.client.get(reverse("catalog:departure_detail", args=[first.departure_id]))
        self.assertEqual(detail.context["booked_seats"], first.departure.booked_seats)
        self.assertContains(detail, "BK4")
        self.assertContains(detail, "chỉ đọc")
        self.assertEqual(Booking.objects.count(), 4)

    def test_empty_booking_list_renders(self):
        response = self.client.get(reverse("catalog:departure_detail", args=[Departure.objects.first().pk]))
        self.assertContains(response, "Chưa có booking nào.")

    def test_departure_list_has_bounded_query_count(self):
        self.make_booking()
        with CaptureQueriesContext(connection) as captured:
            response = self.client.get("/departures/")
        self.assertEqual(response.status_code, 200)
        self.assertLessEqual(len(captured), 10)

    def test_end_date_and_existing_booked_capacity_are_validated(self):
        booking = self.make_booking()
        departure = booking.departure
        data = {"tour": departure.tour_id, "start_date": "2026-12-05", "end_date": "2026-12-04", "max_seats": 2, "price": "2450000", "status": "OPEN"}
        response = self.client.post(reverse("catalog:departure_update", args=[departure.pk]), data)
        self.assertIn("end_date", response.context["form"].errors)
        self.assertIn("max_seats", response.context["form"].errors)
        departure.refresh_from_db()
        self.assertEqual(departure.max_seats, 29)

    def test_booked_departure_is_protected_from_deletion(self):
        booking = self.make_booking()
        response = self.client.post(reverse("catalog:departure_delete", args=[booking.departure_id]))
        self.assertContains(response, "Không thể xóa")
        self.assertTrue(Departure.objects.filter(pk=booking.departure_id).exists())


class SeedCatalogTests(TestCase):
    def assert_counts(self):
        for model, count in [(Supplier, 5), (Service, 10), (Guide, 4), (Vehicle, 4), (Tour, 4), (TourItinerary, 10), (Departure, 8), (Customer, 10)]:
            self.assertEqual(model.objects.count(), count)
            for item in model.objects.all():
                item.full_clean()

    def test_seed_from_empty_database_is_repeatable_and_keeps_edits(self):
        call_command("seed_catalog", stdout=StringIO())
        self.assert_counts()
        service = Service.objects.first()
        service.unit_price = Decimal("999999")
        service.save(update_fields=["unit_price"])
        call_command("seed_catalog", stdout=StringIO())
        self.assert_counts()
        service.refresh_from_db()
        self.assertEqual(service.unit_price, Decimal("999999"))
        self.assertEqual(get_user_model().objects.count(), 0)
        self.assertEqual(Booking.objects.count(), 0)

    def test_seed_extends_base_without_duplicates(self):
        call_command("seed_base", stdout=StringIO())
        call_command("seed_catalog", stdout=StringIO())
        call_command("seed_catalog", stdout=StringIO())
        self.assert_counts()
        self.assertEqual(get_user_model().objects.count(), 3)
