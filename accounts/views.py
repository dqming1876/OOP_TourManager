from django.contrib import messages
from django.contrib.auth import get_user_model, update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.db.models import CharField, Q, Value
from django.db.models.functions import Concat
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.debug import sensitive_post_parameters
from django.views.generic import CreateView, DeleteView, FormView, ListView, TemplateView, UpdateView

from .forms import AdminPasswordResetForm, AdminUserCreateForm, AdminUserUpdateForm, ApproveUserForm, ConfirmationForm, LoginForm, ProfileForm, RegistrationForm, SelfPasswordChangeForm, UserFilterForm
from .mixins import RoleRequiredMixin
from .roles import ROLE_NAMES
from .services import approve_user, delete_or_lock_user, is_pending_user, pending_users, role_label

User = get_user_model()


class UserLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = LoginForm

    def form_valid(self, form):
        messages.success(self.request, "Đăng nhập thành công.")
        return super().form_valid(form)


class UserLogoutView(LogoutView):
    # Django 5 dùng POST để đăng xuất, đi kèm CSRF token ở thanh điều hướng.
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        messages.success(request, "Bạn đã đăng xuất.")
        return response


class DashboardView(RoleRequiredMixin, TemplateView):
    allowed_roles = ROLE_NAMES
    template_name = "accounts/dashboard.html"


@method_decorator(sensitive_post_parameters(), name="dispatch")
class RegisterView(CreateView):
    form_class = RegistrationForm
    template_name = "accounts/register.html"
    success_url = reverse_lazy("accounts:login")

    def form_valid(self, form):
        try:
            with transaction.atomic():
                self.object = form.save()
        except IntegrityError:
            if User.objects.filter(username=form.cleaned_data["username"]).exists():
                form.add_error("username", "Tên đăng nhập đã được sử dụng.")
                return self.form_invalid(form)
            raise
        messages.success(self.request, "Đăng ký thành công, vui lòng chờ Admin duyệt")
        return HttpResponseRedirect(self.get_success_url())


class AdminRequiredMixin(RoleRequiredMixin):
    allowed_roles = ()

    def handle_no_permission(self):
        # Các trang /users/ trả 403 đẹp cả khi chưa đăng nhập.
        raise PermissionDenied("Chỉ Admin được quản lý người dùng.")


class UserListView(AdminRequiredMixin, ListView):
    model = User
    template_name = "accounts/user_list.html"
    paginate_by = 10
    context_object_name = "users"

    def get_queryset(self):
        queryset = User.objects.prefetch_related("groups").annotate(
            full_name_text=Concat("first_name", Value(" "), "last_name", output_field=CharField()),
        ).order_by("username", "pk")
        self.filter_form = UserFilterForm(self.request.GET)
        if not self.filter_form.is_valid():
            return queryset.none()
        data = self.filter_form.cleaned_data
        q = data.get("q", "").strip()
        if q:
            queryset = queryset.filter(Q(username__icontains=q) | Q(full_name_text__icontains=q) | Q(email__icontains=q))
        role = data.get("role")
        if role == "Admin":
            queryset = queryset.filter(Q(is_superuser=True) | Q(groups__name="Admin"))
        elif role:
            queryset = queryset.filter(groups__name=role)
        status = data.get("status")
        if status == "active":
            queryset = queryset.filter(is_active=True)
        elif status == "pending":
            queryset = queryset.filter(pk__in=pending_users().values("pk"))
        elif status == "locked":
            queryset = queryset.filter(is_active=False).exclude(pk__in=pending_users().values("pk"))
        return queryset.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        for user in context["users"]:
            user.display_role = role_label(user)
            user.is_pending = is_pending_user(user)
        query = self.request.GET.copy()
        query.pop("page", None)
        context.update(filter_form=self.filter_form, pagination_query=query.urlencode(), approve_form=ApproveUserForm())
        return context


class UserSaveMixin:
    success_url = reverse_lazy("accounts:user_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Sửa người dùng" if getattr(self, "object", None) else "Thêm người dùng"
        return context

    def form_valid(self, form):
        try:
            self.object = form.save()
        except ValidationError as error:
            form.add_error(None, error)
            return self.form_invalid(form)
        messages.success(self.request, "Đã lưu người dùng và vai trò thành công.")
        return HttpResponseRedirect(self.get_success_url())


@method_decorator(sensitive_post_parameters(), name="dispatch")
class UserCreateView(AdminRequiredMixin, UserSaveMixin, CreateView):
    model = User
    form_class = AdminUserCreateForm
    template_name = "accounts/user_form.html"


class UserUpdateView(AdminRequiredMixin, UserSaveMixin, UpdateView):
    model = User
    form_class = AdminUserUpdateForm
    template_name = "accounts/user_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["actor"] = self.request.user
        return kwargs


class UserApproveView(AdminRequiredMixin, View):
    http_method_names = ["post"]

    def post(self, request, pk):
        get_object_or_404(User, pk=pk)
        form = ApproveUserForm(request.POST)
        if not form.is_valid():
            messages.error(request, "Vui lòng chọn một vai trò hợp lệ để duyệt tài khoản.")
        else:
            try:
                approve_user(pk, form.cleaned_data["role"], request.user)
                messages.success(request, "Đã duyệt tài khoản và gán vai trò thành công.")
            except ValidationError as error:
                messages.error(request, " ".join(error.messages))
        return redirect("accounts:user_list")


class UserDeleteView(AdminRequiredMixin, DeleteView):
    model = User
    form_class = ConfirmationForm
    template_name = "accounts/user_confirm_delete.html"
    success_url = reverse_lazy("accounts:user_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["has_related_data"] = self.object.created_bookings.exists() or self.object.received_payments.exists()
        return context

    def form_valid(self, form):
        try:
            action = delete_or_lock_user(self.object.pk, self.request.user)
        except ValidationError as error:
            form.add_error(None, error)
            return self.form_invalid(form)
        message = "Tài khoản đã có dữ liệu liên quan nên được khóa và giữ lại dữ liệu." if action == "locked" else "Đã xóa tài khoản chưa phát sinh dữ liệu."
        messages.success(self.request, message)
        return HttpResponseRedirect(self.get_success_url())


@method_decorator(sensitive_post_parameters(), name="dispatch")
class UserPasswordResetView(AdminRequiredMixin, FormView):
    template_name = "accounts/user_password_reset.html"
    form_class = AdminPasswordResetForm
    success_url = reverse_lazy("accounts:user_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = get_object_or_404(User, pk=self.kwargs["pk"])
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["target_user"] = context["form"].user
        return context

    def form_valid(self, form):
        user = form.save()
        if user.pk == self.request.user.pk:
            update_session_auth_hash(self.request, user)
        messages.success(self.request, "Đã đặt lại mật khẩu thành công.")
        return super().form_valid(form)


class ProfileView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = ProfileForm
    template_name = "accounts/profile.html"
    success_url = reverse_lazy("accounts:profile")

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, "Đã cập nhật hồ sơ cá nhân.")
        return super().form_valid(form)


class SelfPasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    template_name = "accounts/password_change.html"
    form_class = SelfPasswordChangeForm
    success_url = reverse_lazy("accounts:profile")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Đã đổi mật khẩu thành công.")
        return response


def permission_denied(request, exception):
    return render(request, "403.html", status=403)
