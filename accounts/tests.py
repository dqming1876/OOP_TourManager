from io import StringIO

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.test import Client, TestCase, TransactionTestCase, override_settings
from django.urls import include, path
from django.views.generic import TemplateView

from catalog.models import Departure, Guide, Service, Supplier, Tour, TourItinerary, Vehicle
from customers.models import Customer

from .mixins import RoleRequiredMixin
from .views import permission_denied


class SalesOnlyView(RoleRequiredMixin, TemplateView):
    allowed_roles = ("Sales",)
    template_name = "accounts/dashboard.html"


urlpatterns = [path("sales-only/", SalesOnlyView.as_view()), path("", include("config.urls"))]
handler403 = permission_denied


@override_settings(ROOT_URLCONF=__name__)
class AccessTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("setup_roles", stdout=StringIO())
        User = get_user_model()
        cls.sales = User.objects.create_user("salesTest", password="testPassword123!")
        cls.sales.groups.add(Group.objects.get(name="Sales"))
        cls.operator = User.objects.create_user("operatorTest", password="testPassword123!")
        cls.operator.groups.add(Group.objects.get(name="Operator"))
        cls.admin = User.objects.create_user("adminTest")
        cls.admin.groups.add(Group.objects.get(name="Admin"))
        cls.superuser = User.objects.create_superuser("superTest", password="testPassword123!")
        cls.no_role = User.objects.create_user("noRole")

    def test_anonymous_is_redirected_to_login(self):
        response = self.client.get("/sales-only/")
        self.assertRedirects(response, "/login/?next=/sales-only/")

    def test_wrong_role_receives_custom_403(self):
        self.client.force_login(self.operator)
        response = self.client.get("/sales-only/")
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, "Bạn chưa được cấp quyền", status_code=403)

    def test_superuser_and_admin_bypass_role_restriction(self):
        for user in (self.admin, self.superuser, self.sales):
            with self.subTest(user=user.username):
                self.client.force_login(user)
                self.assertEqual(self.client.get("/sales-only/").status_code, 200)

    def test_authenticated_user_without_role_is_forbidden(self):
        self.client.force_login(self.no_role)
        self.assertEqual(self.client.get("/").status_code, 403)
        self.assertEqual(self.client.get("/login/").status_code, 200)

    def test_sidebar_and_context_follow_roles(self):
        self.client.force_login(self.sales)
        response = self.client.get("/")
        self.assertEqual(response.context["current_role"], "Sales")
        self.assertContains(response, 'href="/bookings/"')
        self.assertNotContains(response, 'href="/assignments/"')
        self.client.force_login(self.operator)
        response = self.client.get("/")
        self.assertContains(response, 'href="/assignments/"')
        self.assertNotContains(response, 'href="/bookings/"')

    def test_multiple_roles_show_both_menus(self):
        self.sales.groups.add(Group.objects.get(name="Operator"))
        self.client.force_login(self.sales)
        response = self.client.get("/")
        self.assertContains(response, 'href="/bookings/"')
        self.assertContains(response, 'href="/assignments/"')

    def test_login_success_and_invalid_password(self):
        response = self.client.post("/login/", {"username": "salesTest", "password": "wrong"})
        self.assertContains(response, "Tên đăng nhập hoặc mật khẩu không đúng.")
        response = self.client.post("/login/", {"username": "salesTest", "password": "testPassword123!"})
        self.assertRedirects(response, "/")

    def test_login_rejects_external_redirect(self):
        response = self.client.post("/login/?next=https://example.com/", {"username": "salesTest", "password": "testPassword123!"})
        self.assertRedirects(response, "/")

    def test_logout_requires_post_and_csrf(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.sales)
        self.assertEqual(client.get("/logout/").status_code, 405)
        client.get("/")
        self.assertEqual(client.post("/logout/").status_code, 403)
        response = client.post("/logout/", HTTP_X_CSRFTOKEN=client.cookies["csrftoken"].value)
        self.assertRedirects(response, "/login/")
        self.assertNotIn("_auth_user_id", client.session)

    def test_setup_roles_is_repeatable_and_assigns_permissions(self):
        before = {g.name: set(g.permissions.values_list("pk", flat=True)) for g in Group.objects.all()}
        call_command("setup_roles", stdout=StringIO())
        after = {g.name: set(g.permissions.values_list("pk", flat=True)) for g in Group.objects.all()}
        self.assertEqual(before, after)
        self.assertTrue(self.sales.has_perm("bookings.add_booking"))
        self.assertTrue(self.sales.has_perm("catalog.view_tour"))
        self.assertFalse(self.sales.has_perm("operations.add_tourexpense"))
        self.assertTrue(self.operator.has_perm("operations.add_tourexpense"))
        self.assertFalse(self.operator.has_perm("bookings.add_payment"))


class SeedTests(TestCase):
    def test_seed_is_repeatable_preserves_passwords_and_has_no_transactions(self):
        from bookings.models import Booking, Payment
        from operations.models import GuideAssignment, TourExpense, VehicleAssignment

        output = StringIO()
        call_command("seed_base", stdout=output)
        self.assertNotIn("| Mật khẩu:", output.getvalue())
        User = get_user_model()
        passwords = dict(User.objects.values_list("username", "password"))
        call_command("seed_base", stdout=StringIO())
        self.assertEqual(passwords, dict(User.objects.values_list("username", "password")))
        self.assertEqual(User.objects.count(), 3)
        self.assertTrue(User.objects.get(username="admin").is_superuser)
        for model, count in [(Supplier, 2), (Service, 4), (Guide, 2), (Vehicle, 2), (Tour, 2), (TourItinerary, 5), (Departure, 3), (Customer, 3)]:
            self.assertEqual(model.objects.count(), count)
            for item in model.objects.all():
                item.full_clean()
        for model in (Booking, Payment, GuideAssignment, VehicleAssignment, TourExpense):
            self.assertEqual(model.objects.count(), 0)


class RegistrationTests(TestCase):
    password = "PurpleRiver!2026"

    def payload(self, **changes):
        data = {"username": "newMember", "full_name": "Nguyễn Thị Minh", "email": "minh@example.com", "password1": self.password, "password2": self.password}
        data.update(changes)
        return data

    def test_register_and_login_are_public(self):
        self.assertEqual(self.client.get("/register/").status_code, 200)
        self.assertContains(self.client.get("/login/"), 'href="/register/"')

    def test_registration_is_inactive_roleless_and_ignores_injected_privileges(self):
        response = self.client.post("/register/", self.payload(is_active="on", is_staff="on", is_superuser="on", role="Admin", groups="1"), follow=True)
        self.assertContains(response, "Đăng ký thành công, vui lòng chờ Admin duyệt")
        user = get_user_model().objects.get(username="newMember")
        self.assertFalse(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.groups.exists())
        self.assertEqual(user.get_full_name(), "Nguyễn Thị Minh")
        self.assertTrue(user.check_password(self.password))
        self.assertNotEqual(user.password, self.password)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_invalid_registration_is_not_saved(self):
        for changes in ({"password1": "123", "password2": "123"}, {"password2": "Mismatch!2026"}, {"email": "invalid"}, {"full_name": ""}):
            response = self.client.post("/register/", self.payload(**changes))
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.context["form"].errors)
            self.assertFalse(get_user_model().objects.filter(username="newMember").exists())

    def test_duplicate_username_is_rejected(self):
        self.client.post("/register/", self.payload())
        response = self.client.post("/register/", self.payload())
        self.assertIn("username", response.context["form"].errors)
        self.assertEqual(get_user_model().objects.filter(username="newMember").count(), 1)

    def test_pending_account_cannot_login_and_has_clear_message(self):
        self.client.post("/register/", self.payload())
        response = self.client.post("/login/", {"username": "newMember", "password": self.password})
        self.assertContains(response, "Tài khoản đang chờ Admin duyệt")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_wrong_password_does_not_reveal_pending_state(self):
        self.client.post("/register/", self.payload())
        response = self.client.post("/login/", {"username": "newMember", "password": "wrong"})
        self.assertContains(response, "Tên đăng nhập hoặc mật khẩu không đúng.")
        self.assertNotContains(response, "Tài khoản đang chờ Admin duyệt")

    def test_locked_account_has_distinct_login_message(self):
        self.client.post("/register/", self.payload())
        user = get_user_model().objects.get(username="newMember")
        user.groups.add(Group.objects.get_or_create(name="Sales")[0])
        response = self.client.post("/login/", {"username": user.username, "password": self.password})
        self.assertContains(response, "Tài khoản đã bị khóa")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_registration_requires_csrf(self):
        client = Client(enforce_csrf_checks=True)
        self.assertEqual(client.post("/register/", self.payload()).status_code, 403)
        client.get("/register/")
        token = client.cookies["csrftoken"].value
        response = client.post("/register/", self.payload(), HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code, 302)


class UserManagementTests(TestCase):
    password = "PurpleRiver!2026"

    @classmethod
    def setUpTestData(cls):
        call_command("setup_roles", stdout=StringIO())
        User = get_user_model()
        cls.admin = User.objects.create_user("manager", first_name="Quản trị viên", email="manager@example.com", is_staff=True)
        cls.admin.groups.add(Group.objects.get(name="Admin"))
        cls.sales = User.objects.create_user("seller", password=cls.password, first_name="Nguyễn", last_name="Văn An", email="seller@example.com")
        cls.sales.groups.add(Group.objects.get(name="Sales"))
        cls.operator = User.objects.create_user("coordinator")
        cls.operator.groups.add(Group.objects.get(name="Operator"))
        cls.pending = User.objects.create_user("applicant", is_active=False, first_name="Người chờ duyệt")
        cls.locked = User.objects.create_user("lockedSeller", is_active=False)
        cls.locked.groups.add(Group.objects.get(name="Sales"))

    def setUp(self):
        self.client.force_login(self.admin)

    def update_payload(self, user, role="Sales", active=True, **changes):
        data = {"full_name": user.get_full_name() or "Họ tên mới", "email": user.email or "member@example.com", "role": Group.objects.get(name=role).pk}
        if active:
            data["is_active"] = "on"
        data.update(changes)
        return data

    def management_urls(self):
        pk = self.sales.pk
        return ["/users/", "/users/create/", f"/users/{pk}/edit/", f"/users/{pk}/delete/", f"/users/{pk}/approve/", f"/users/{pk}/password-reset/"]

    def test_non_admin_gets_403_for_every_user_route_get_and_post(self):
        for actor in (self.sales, self.operator):
            self.client.force_login(actor)
            for url in self.management_urls():
                with self.subTest(actor=actor.username, url=url):
                    self.assertContains(self.client.get(url), "Bạn chưa được cấp quyền", status_code=403)
                    self.assertEqual(self.client.post(url, {}).status_code, 403)

    def test_anonymous_user_routes_are_forbidden(self):
        self.client.logout()
        for url in self.management_urls():
            self.assertEqual(self.client.get(url).status_code, 403)
            self.assertEqual(self.client.post(url, {}).status_code, 403)

    def test_admin_can_create_each_role_with_correct_flags(self):
        User = get_user_model()
        for role in ("Admin", "Sales", "Operator"):
            data = {"username": f"new{role}", "full_name": "Nhân viên mới", "email": f"new{role}@example.com", "password1": self.password, "password2": self.password, "role": Group.objects.get(name=role).pk, "is_active": "on"}
            response = self.client.post("/users/create/", data)
            self.assertEqual(response.status_code, 302)
            user = User.objects.get(username=f"new{role}")
            self.assertEqual(list(user.groups.values_list("name", flat=True)), [role])
            self.assertEqual(user.is_staff, role == "Admin")
            self.assertFalse(user.is_superuser)
            self.assertTrue(user.is_active)
            self.assertTrue(user.check_password(self.password))

    def test_assigning_role_replaces_groups_and_revokes_superuser(self):
        target = get_user_model().objects.create_user("legacySuper", is_staff=True, is_superuser=True)
        target.groups.set(Group.objects.filter(name__in=["Admin", "Sales"]))
        response = self.client.post(f"/users/{target.pk}/edit/", self.update_payload(target, "Operator"))
        self.assertEqual(response.status_code, 302)
        target.refresh_from_db()
        self.assertEqual(list(target.groups.values_list("name", flat=True)), ["Operator"])
        self.assertFalse(target.is_staff)
        self.assertFalse(target.is_superuser)

    def test_promotion_to_admin_sets_staff(self):
        self.client.post(f"/users/{self.sales.pk}/edit/", self.update_payload(self.sales, "Admin"))
        self.sales.refresh_from_db()
        self.assertTrue(self.sales.is_staff)
        self.assertEqual(list(self.sales.groups.values_list("name", flat=True)), ["Admin"])

    def test_approval_requires_post_and_explicit_valid_role(self):
        url = f"/users/{self.pending.pk}/approve/"
        self.assertEqual(self.client.get(url).status_code, 405)
        response = self.client.post(url, {}, follow=True)
        self.assertContains(response, "Vui lòng chọn một vai trò hợp lệ")
        self.pending.refresh_from_db()
        self.assertFalse(self.pending.is_active)
        self.client.post(url, {"role": Group.objects.get(name="Sales").pk})
        self.pending.refresh_from_db()
        self.assertTrue(self.pending.is_active)
        self.assertEqual(list(self.pending.groups.values_list("name", flat=True)), ["Sales"])

    def test_repeated_approval_does_not_change_assigned_role(self):
        url = f"/users/{self.pending.pk}/approve/"
        self.client.post(url, {"role": Group.objects.get(name="Sales").pk})
        response = self.client.post(url, {"role": Group.objects.get(name="Admin").pk}, follow=True)
        self.assertContains(response, "đã được duyệt")
        self.assertEqual(list(self.pending.groups.values_list("name", flat=True)), ["Sales"])

    def test_last_active_admin_cannot_be_disabled_or_demoted(self):
        url = f"/users/{self.admin.pk}/edit/"
        for role, active in (("Admin", False), ("Sales", True)):
            response = self.client.post(url, self.update_payload(self.admin, role, active))
            self.assertContains(response, "Admin cuối cùng")
            self.admin.refresh_from_db()
            self.assertTrue(self.admin.is_active)
            self.assertTrue(self.admin.groups.filter(name="Admin").exists())

    def test_inactive_admin_does_not_count_as_replacement(self):
        other = get_user_model().objects.create_user("inactiveAdmin", is_active=False, is_staff=True)
        other.groups.add(Group.objects.get(name="Admin"))
        response = self.client.post(f"/users/{self.admin.pk}/delete/")
        self.assertContains(response, "Admin cuối cùng")
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)

    def test_admin_cannot_disable_or_delete_self_even_with_another_admin(self):
        other = get_user_model().objects.create_superuser("otherAdmin", email="other@example.com")
        other.groups.add(Group.objects.get(name="Admin"))
        response = self.client.post(f"/users/{self.admin.pk}/delete/")
        self.assertContains(response, "chính mình")
        response = self.client.post(f"/users/{self.admin.pk}/edit/", self.update_payload(self.admin, "Admin", False, full_name="Không được lưu"))
        self.assertContains(response, "chính mình")
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)
        self.assertEqual(self.admin.first_name, "Quản trị viên")

    def test_delete_unused_user_requires_confirmation_and_preserves_on_get(self):
        url = f"/users/{self.pending.pk}/delete/"
        self.assertContains(self.client.get(url), "Xác nhận xóa")
        self.assertTrue(get_user_model().objects.filter(pk=self.pending.pk).exists())
        self.assertEqual(self.client.post(url).status_code, 302)
        self.assertFalse(get_user_model().objects.filter(pk=self.pending.pk).exists())

    def make_booking(self, creator):
        from datetime import date
        from decimal import Decimal
        from bookings.models import Booking
        tour = Tour.objects.create(code="ACC", name="Tour kiểm thử", days=1, nights=0, destination="Hạ Long", base_price=Decimal("1000000"))
        departure = Departure.objects.create(tour=tour, start_date=date(2026, 12, 5), end_date=date(2026, 12, 5), max_seats=20, price=Decimal("1000000"))
        customer = Customer.objects.create(full_name="Khách mẫu", phone="0900000000")
        return Booking.objects.create(code="ACCBK", customer=customer, departure=departure, total_amount=Decimal("1000000"), created_by=creator)

    def test_user_with_booking_is_locked_instead_of_deleted(self):
        booking = self.make_booking(self.sales)
        response = self.client.post(f"/users/{self.sales.pk}/delete/", follow=True)
        self.assertContains(response, "được khóa và giữ lại dữ liệu")
        self.sales.refresh_from_db()
        self.assertFalse(self.sales.is_active)
        self.assertEqual(booking.created_by_id, self.sales.pk)
        self.assertEqual(list(self.sales.groups.values_list("name", flat=True)), ["Sales"])

    def test_user_with_only_received_payment_is_also_locked(self):
        from bookings.models import Payment
        booking = self.make_booking(self.admin)
        payment = Payment.objects.create(booking=booking, amount=100000, payment_type="DEPOSIT", method="CASH", received_by=self.sales)
        self.client.post(f"/users/{self.sales.pk}/delete/")
        self.sales.refresh_from_db()
        self.assertFalse(self.sales.is_active)
        self.assertTrue(Payment.objects.filter(pk=payment.pk, received_by=self.sales).exists())

    def test_search_full_name_role_status_and_pagination(self):
        response = self.client.get("/users/", {"q": "Nguyễn Văn An", "role": "Sales", "status": "active"})
        self.assertEqual([user.pk for user in response.context["users"]], [self.sales.pk])
        for index in range(12):
            get_user_model().objects.create_user(f"Waiting{index:02}", is_active=False)
        response = self.client.get("/users/", {"q": "Waiting", "status": "pending"})
        self.assertEqual(response.context["paginator"].count, 12)
        self.assertEqual(len(response.context["users"]), 10)
        self.assertContains(response, "q=Waiting&amp;status=pending&amp;page=2")
        self.assertEqual(len(self.client.get("/users/", {"q": "Waiting", "status": "pending", "page": 2}).context["users"]), 2)

    def test_pending_and_locked_filters_are_distinct(self):
        pending = self.client.get("/users/", {"status": "pending"})
        locked = self.client.get("/users/", {"status": "locked"})
        self.assertEqual([user.pk for user in pending.context["users"]], [self.pending.pk])
        self.assertEqual([user.pk for user in locked.context["users"]], [self.locked.pk])
        self.assertContains(pending, 'class="table-warning"')

    def test_invalid_filters_do_not_crash(self):
        response = self.client.get("/users/", {"status": "INVALID"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["filter_form"].errors)

    def test_pending_badge_only_shown_to_admin(self):
        response = self.client.get("/")
        self.assertEqual(response.context["pending_user_count"], 1)
        self.assertContains(response, 'href="/users/"')
        self.client.force_login(self.sales)
        response = self.client.get("/")
        self.assertEqual(response.context["pending_user_count"], 0)
        self.assertNotContains(response, 'href="/users/"')
        self.assertContains(response, 'href="/profile/"')
        self.assertContains(response, 'href="/password-change/"')

    def test_user_mutations_require_csrf(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.admin)
        for url in ("/users/create/", f"/users/{self.sales.pk}/edit/", f"/users/{self.pending.pk}/approve/", f"/users/{self.sales.pk}/delete/", f"/users/{self.sales.pk}/password-reset/"):
            self.assertEqual(client.post(url, {}).status_code, 403)

    def test_django_admin_cannot_bypass_account_management(self):
        for url in (f"/admin/auth/user/{self.sales.pk}/change/", f"/admin/auth/user/{self.admin.pk}/delete/", "/admin/auth/user/add/", f"/admin/auth/group/{Group.objects.get(name='Admin').pk}/change/"):
            self.assertEqual(self.client.post(url, {}).status_code, 403)
        self.assertEqual(self.client.get(f"/admin/auth/user/{self.sales.pk}/change/").status_code, 200)

    def test_password_reset_invalidates_other_sessions(self):
        old_session = Client()
        old_session.force_login(self.sales)
        new_password = "AnotherRiver!2027"
        response = self.client.post(f"/users/{self.sales.pk}/password-reset/", {"new_password1": new_password, "new_password2": new_password})
        self.assertEqual(response.status_code, 302)
        self.sales.refresh_from_db()
        self.assertTrue(self.sales.check_password(new_password))
        self.assertEqual(old_session.get("/profile/").status_code, 302)
        self.assertNotIn("_auth_user_id", old_session.session)

    def test_self_reset_keeps_admin_session(self):
        response = self.client.post(f"/users/{self.admin.pk}/password-reset/", {"new_password1": "AnotherRiver!2027", "new_password2": "AnotherRiver!2027"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.get("/users/").status_code, 200)


class ProfileTests(TestCase):
    password = "PurpleRiver!2026"

    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user("profileUser", password=cls.password, first_name="Tên cũ", email="old@example.com")
        cls.user.groups.add(Group.objects.get_or_create(name="Sales")[0])

    def setUp(self):
        self.client.force_login(self.user)

    def test_profile_only_changes_name_and_email(self):
        response = self.client.post("/profile/", {"full_name": "Nguyễn Văn Mới", "email": "new@example.com", "username": "hacked", "is_superuser": "on", "is_staff": "on", "role": "Admin"})
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.get_full_name(), "Nguyễn Văn Mới")
        self.assertEqual(self.user.email, "new@example.com")
        self.assertEqual(self.user.username, "profileUser")
        self.assertFalse(self.user.is_superuser)
        self.assertFalse(self.user.is_staff)
        self.assertEqual(list(self.user.groups.values_list("name", flat=True)), ["Sales"])

    def test_profile_and_password_change_require_login(self):
        self.client.logout()
        self.assertEqual(self.client.get("/profile/").status_code, 302)
        self.assertEqual(self.client.get("/password-change/").status_code, 302)

    def test_password_change_validates_old_password_and_keeps_session(self):
        data = {"old_password": "wrong", "new_password1": "AnotherRiver!2027", "new_password2": "AnotherRiver!2027"}
        response = self.client.post("/password-change/", data)
        self.assertIn("old_password", response.context["form"].errors)
        data["old_password"] = self.password
        self.assertEqual(self.client.post("/password-change/", data).status_code, 302)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("AnotherRiver!2027"))
        self.assertEqual(self.client.get("/profile/").status_code, 200)

    def test_password_change_rejects_weak_password(self):
        response = self.client.post("/password-change/", {"old_password": self.password, "new_password1": "123", "new_password2": "123"})
        self.assertTrue(response.context["form"].errors)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(self.password))

    def test_stale_profile_form_does_not_reactivate_a_locked_user(self):
        from .forms import ProfileForm
        form = ProfileForm({"full_name": "Tên mới", "email": "new@example.com"}, instance=self.user)
        self.assertTrue(form.is_valid())
        get_user_model().objects.filter(pk=self.user.pk).update(is_active=False)
        form.save()
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)

    def test_stale_password_form_does_not_reactivate_a_locked_user(self):
        from .forms import AdminPasswordResetForm
        form = AdminPasswordResetForm(self.user, {"new_password1": "AnotherRiver!2027", "new_password2": "AnotherRiver!2027"})
        self.assertTrue(form.is_valid())
        get_user_model().objects.filter(pk=self.user.pk).update(is_active=False)
        form.save()
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)


class CreateAdminTests(TestCase):
    password = "PurpleRiver!2026"

    def test_command_creates_roles_and_is_repeatable_without_password_output(self):
        output = StringIO()
        call_command("create_admin", username="cliAdmin", email="first@example.com", password=self.password, stdout=output)
        user = get_user_model().objects.get(username="cliAdmin")
        first_pk = user.pk
        self.assertTrue(user.is_superuser and user.is_staff and user.is_active)
        self.assertEqual(list(user.groups.values_list("name", flat=True)), ["Admin"])
        user.groups.add(Group.objects.get(name="Sales"))
        user.is_active = False
        user.save(update_fields=["is_active"])
        new_password = "AnotherRiver!2027"
        call_command("create_admin", username="cliAdmin", email="second@example.com", password=new_password, stdout=output)
        user.refresh_from_db()
        self.assertEqual(user.pk, first_pk)
        self.assertEqual(user.email, "second@example.com")
        self.assertTrue(user.is_superuser and user.is_staff and user.is_active)
        self.assertEqual(list(user.groups.values_list("name", flat=True)), ["Admin"])
        self.assertTrue(user.check_password(new_password))
        self.assertNotIn(self.password, output.getvalue())
        self.assertNotIn(new_password, output.getvalue())

    def test_command_reads_env_file(self):
        import os
        from pathlib import Path
        from tempfile import TemporaryDirectory
        from unittest.mock import patch
        with TemporaryDirectory() as directory, override_settings(BASE_DIR=directory), patch.dict(os.environ):
            for key in ("ADMIN_USERNAME", "ADMIN_EMAIL", "ADMIN_PASSWORD"):
                os.environ.pop(key, None)
            Path(directory, ".env").write_text(f"ADMIN_USERNAME=envAdmin\nADMIN_EMAIL=env@example.com\nADMIN_PASSWORD={self.password}\n")
            output = StringIO()
            call_command("create_admin", stdout=output)
            user = get_user_model().objects.get(username="envAdmin")
            self.assertEqual(user.email, "env@example.com")
            self.assertTrue(user.check_password(self.password))
            self.assertNotIn(self.password, output.getvalue())

    def test_missing_password_uses_getpass(self):
        import os
        from unittest.mock import patch
        with patch.dict(os.environ, {"ADMIN_PASSWORD": ""}), patch("accounts.management.commands.create_admin.getpass", return_value=self.password) as prompt:
            call_command("create_admin", username="promptAdmin", email="prompt@example.com", stdout=StringIO())
        self.assertEqual(prompt.call_count, 2)
        self.assertTrue(get_user_model().objects.get(username="promptAdmin").check_password(self.password))

    def test_weak_password_is_rejected(self):
        from django.core.management.base import CommandError
        with self.assertRaises(CommandError):
            call_command("create_admin", username="weakAdmin", email="weak@example.com", password="123", stdout=StringIO())
        self.assertFalse(get_user_model().objects.filter(username="weakAdmin").exists())

    def test_getpass_mismatch_is_rejected(self):
        import os
        from unittest.mock import patch
        from django.core.management.base import CommandError
        with patch.dict(os.environ, {"ADMIN_PASSWORD": ""}), patch("accounts.management.commands.create_admin.getpass", side_effect=[self.password, "AnotherRiver!2027"]):
            with self.assertRaises(CommandError):
                call_command("create_admin", username="mismatchAdmin", stdout=StringIO())
        self.assertFalse(get_user_model().objects.filter(username="mismatchAdmin").exists())

    def test_seed_does_not_promote_pending_username_admin_or_print_passwords(self):
        pending = get_user_model().objects.create_user("admin", is_active=False)
        output = StringIO()
        call_command("seed_base", stdout=output)
        pending.refresh_from_db()
        self.assertFalse(pending.is_active)
        self.assertFalse(pending.is_staff)
        self.assertFalse(pending.is_superuser)
        self.assertFalse(pending.groups.exists())
        self.assertNotIn("| Mật khẩu:", output.getvalue())


class ConcurrentAdminProtectionTests(TransactionTestCase):
    def test_two_admins_cannot_disable_each_other_at_the_same_time(self):
        from concurrent.futures import ThreadPoolExecutor
        from threading import Barrier
        from django.core.exceptions import ValidationError
        from django.db import close_old_connections, connections
        from .services import save_user_account

        role = Group.objects.create(name="Admin")
        users = []
        for username in ("firstAdmin", "secondAdmin"):
            user = get_user_model().objects.create_user(username, is_staff=True)
            user.groups.add(role)
            users.append(user)
        barrier = Barrier(2)

        def disable(actor_pk, target_pk):
            close_old_connections()
            try:
                actor = get_user_model().objects.get(pk=actor_pk)
                target = get_user_model().objects.get(pk=target_pk)
                group = Group.objects.get(name="Admin")
                barrier.wait(timeout=10)
                try:
                    save_user_account(target, group, False, actor=actor)
                    return "disabled"
                except ValidationError:
                    return "blocked"
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(disable, users[0].pk, users[1].pk), pool.submit(disable, users[1].pk, users[0].pk)]
            results = [future.result(timeout=20) for future in futures]
        self.assertCountEqual(results, ["disabled", "blocked"])
        self.assertEqual(get_user_model().objects.filter(is_active=True, groups__name="Admin").count(), 1)
