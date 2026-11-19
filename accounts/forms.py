from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm, SetPasswordForm, UserCreationForm
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError

from .roles import ROLE_NAMES
from .services import is_pending_user, save_user_account

User = get_user_model()


def style_fields(form):
    for field in form.fields.values():
        widget = field.widget
        if isinstance(widget, forms.CheckboxInput):
            widget.attrs["class"] = "form-check-input"
        elif isinstance(widget, forms.Select):
            widget.attrs["class"] = "form-select"
        else:
            widget.attrs["class"] = "form-control"


def set_full_name(user, data):
    user.first_name = data.get("full_name", "").strip()
    user.last_name = ""


def available_roles():
    return Group.objects.filter(name__in=ROLE_NAMES).order_by("name")


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "Tên đăng nhập"
        self.fields["password"].label = "Mật khẩu"
        self.fields["username"].widget.attrs.update({"autocomplete": "username", "autofocus": True})
        self.fields["password"].widget.attrs["autocomplete"] = "current-password"
        self.error_messages = self.error_messages.copy()
        self.error_messages["invalid_login"] = "Tên đăng nhập hoặc mật khẩu không đúng."
        self.error_messages["inactive"] = "Tài khoản đã bị khóa."
        style_fields(self)

    def clean(self):
        try:
            return super().clean()
        except ValidationError:
            username = self.cleaned_data.get("username")
            password = self.cleaned_data.get("password")
            user = User.objects.filter(username=username).first() if username else None
            # Chỉ giải thích trạng thái khi mật khẩu đúng, không tiết lộ qua tên tài khoản.
            if user is not None and not user.is_active and password and user.check_password(password):
                message = "Tài khoản đang chờ Admin duyệt" if is_pending_user(user) else "Tài khoản đã bị khóa, vui lòng liên hệ Admin"
                raise ValidationError(message, code="inactive")
            raise


class BaseCreateUserForm(UserCreationForm):
    full_name = forms.CharField(label="Họ tên", max_length=150)
    email = forms.EmailField(label="Email", max_length=254)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "full_name", "email", "password1", "password2")
        labels = {"username": "Tên đăng nhập"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password1"].label = "Mật khẩu"
        self.fields["password2"].label = "Nhập lại mật khẩu"
        style_fields(self)

    def _post_clean(self):
        # Để password validators kiểm tra cả họ tên vừa nhập.
        set_full_name(self.instance, self.cleaned_data)
        super()._post_clean()


class RegistrationForm(BaseCreateUserForm):
    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_active = False
        user.is_staff = False
        user.is_superuser = False
        if commit:
            user.save()
        return user


class AdminUserCreateForm(BaseCreateUserForm):
    role = forms.ModelChoiceField(label="Vai trò", queryset=Group.objects.none(), empty_label="Chọn vai trò")
    is_active = forms.BooleanField(label="Kích hoạt tài khoản", required=False, initial=True)

    class Meta(BaseCreateUserForm.Meta):
        fields = (*BaseCreateUserForm.Meta.fields, "role", "is_active")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["role"].queryset = available_roles()

    def save(self, commit=True):
        if not commit:
            raise ValueError("Form quản lý người dùng phải được lưu cùng vai trò.")
        user = super().save(commit=False)
        return save_user_account(user, self.cleaned_data["role"], self.cleaned_data["is_active"])


class ProfileForm(forms.ModelForm):
    full_name = forms.CharField(label="Họ tên", max_length=150)
    email = forms.EmailField(label="Email", max_length=254)

    class Meta:
        model = User
        fields = ("full_name", "email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.initial["full_name"] = self.instance.get_full_name()
        style_fields(self)

    def save(self, commit=True):
        user = super().save(commit=False)
        set_full_name(user, self.cleaned_data)
        if commit:
            # Không ghi đè cờ quyền nếu Admin vừa khóa tài khoản ở yêu cầu khác.
            user.save(update_fields=["first_name", "last_name", "email"])
        return user


class AdminUserUpdateForm(ProfileForm):
    role = forms.ModelChoiceField(label="Vai trò", queryset=Group.objects.none(), empty_label="Chọn vai trò")
    is_active = forms.BooleanField(label="Kích hoạt tài khoản", required=False)

    class Meta(ProfileForm.Meta):
        fields = ("full_name", "email", "role", "is_active")

    def __init__(self, *args, actor, **kwargs):
        self.actor = actor
        super().__init__(*args, **kwargs)
        self.fields["role"].queryset = available_roles()
        current = self.instance.groups.filter(name__in=ROLE_NAMES).first()
        self.initial["role"] = current.pk if current else None
        if self.instance.is_superuser:
            self.initial["role"] = Group.objects.filter(name="Admin").values_list("pk", flat=True).first()

    def save(self, commit=True):
        if not commit:
            raise ValueError("Form quản lý người dùng phải được lưu cùng vai trò.")
        self.instance = save_user_account(
            self.instance, self.cleaned_data["role"], self.cleaned_data["is_active"],
            actor=self.actor, full_name=self.cleaned_data["full_name"], email=self.cleaned_data["email"],
        )
        return self.instance


class ApproveUserForm(forms.Form):
    role = forms.ModelChoiceField(label="Vai trò", queryset=Group.objects.none(), empty_label="Chọn vai trò")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["role"].queryset = available_roles()
        style_fields(self)


class UserFilterForm(forms.Form):
    q = forms.CharField(label="Tìm kiếm", required=False)
    role = forms.ChoiceField(label="Vai trò", required=False, choices=[("", "Tất cả vai trò"), *((name, name) for name in ROLE_NAMES)])
    status = forms.ChoiceField(label="Trạng thái", required=False, choices=[("", "Tất cả trạng thái"), ("active", "Đang hoạt động"), ("pending", "Chờ duyệt"), ("locked", "Bị khóa")])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_fields(self)


class ConfirmationForm(forms.Form):
    pass


class PasswordOnlySaveMixin:
    def save(self, commit=True):
        self.user.set_password(self.cleaned_data["new_password1"])
        if commit:
            self.user.save(update_fields=["password"])
        return self.user


class AdminPasswordResetForm(PasswordOnlySaveMixin, SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_fields(self)


class SelfPasswordChangeForm(PasswordOnlySaveMixin, PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_fields(self)
