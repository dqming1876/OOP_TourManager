"""User/Group chỉ xem trong Django Admin; sửa qua /users/ để giữ quy tắc bảo vệ."""
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import GroupAdmin, UserAdmin
from django.contrib.auth.models import Group


class ReadOnlyAccountsMixin:
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.unregister(get_user_model())
admin.site.unregister(Group)


@admin.register(get_user_model())
class ManagedUserAdmin(ReadOnlyAccountsMixin, UserAdmin):
    pass


@admin.register(Group)
class ManagedGroupAdmin(ReadOnlyAccountsMixin, GroupAdmin):
    pass
