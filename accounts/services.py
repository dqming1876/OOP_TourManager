"""Quy tắc tài khoản dùng chung cho form, view và lệnh quản trị."""
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.db.models.deletion import ProtectedError

from .roles import ROLE_NAMES


def pending_users():
    return get_user_model().objects.filter(is_active=False, is_superuser=False, groups__isnull=True)


def is_pending_user(user):
    return not user.is_active and not user.is_superuser and not list(user.groups.all())


def is_admin_user(user):
    return user.is_superuser or any(group.name == "Admin" for group in user.groups.all())


def role_label(user):
    if user.is_superuser:
        return "Admin"
    names = {group.name for group in user.groups.all()}
    return ", ".join(name for name in ROLE_NAMES if name in names) or "Chưa phân quyền"


def lock_admin_group():
    # Mọi thao tác đổi quyền/khóa/xóa khóa cùng một hàng để bảo vệ Admin cuối cùng.
    try:
        return Group.objects.select_for_update().get(name="Admin")
    except Group.DoesNotExist as exc:
        raise ValidationError("Chưa có nhóm Admin. Hãy chạy setup_roles trước.") from exc


def validate_access_change(target, actor, role, is_active, deleting=False):
    loses_admin_access = deleting or not is_active or role.name != "Admin"
    if target.is_active and is_admin_user(target) and loses_admin_access:
        admins = get_user_model().objects.filter(is_active=True).filter(Q(is_superuser=True) | Q(groups__name="Admin")).distinct()
        if admins.count() <= 1:
            raise ValidationError("Không thể khóa, xóa hoặc gỡ quyền Admin cuối cùng đang hoạt động.")
    if actor is not None and target.pk == actor.pk and loses_admin_access:
        raise ValidationError("Bạn không thể tự khóa, xóa hoặc gỡ quyền Admin của chính mình.")


@transaction.atomic
def save_user_account(user, role, is_active, *, actor=None, full_name=None, email=None, password=None, force_superuser=False):
    lock_admin_group()
    if role.name not in ROLE_NAMES:
        raise ValidationError("Vai trò không hợp lệ.")
    target = user
    if user.pk:
        target = get_user_model().objects.select_for_update().get(pk=user.pk)
        validate_access_change(target, actor, role, is_active)
    if full_name is not None:
        target.first_name = full_name.strip()
        target.last_name = ""
    if email is not None:
        target.email = email
    target.is_active = is_active
    target.is_staff = role.name == "Admin"
    if role.name != "Admin":
        target.is_superuser = False
    elif force_superuser:
        target.is_superuser = True
    if password is not None:
        target.set_password(password)
    target.save()
    target.groups.set([role])
    return target


@transaction.atomic
def approve_user(user_pk, role, actor):
    lock_admin_group()
    target = get_user_model().objects.select_for_update().get(pk=user_pk)
    if not is_pending_user(target):
        raise ValidationError("Tài khoản này đã được duyệt hoặc đã được phân quyền. Vui lòng kiểm tra lại.")
    return save_user_account(target, role, True, actor=actor)


@transaction.atomic
def delete_or_lock_user(user_pk, actor):
    admin_group = lock_admin_group()
    target = get_user_model().objects.select_for_update().get(pk=user_pk)
    validate_access_change(target, actor, admin_group, False, deleting=True)
    has_data = target.created_bookings.exists() or target.received_payments.exists()
    if not has_data:
        try:
            with transaction.atomic():
                target.delete()
            return "deleted"
        except ProtectedError:
            # Nếu có quan hệ PROTECT khác, giữ dữ liệu và chuyển sang khóa.
            pass
    target.is_active = False
    target.save(update_fields=["is_active"])
    return "locked"
