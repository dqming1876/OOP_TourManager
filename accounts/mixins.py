from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied

from .roles import get_user_roles


class RoleRequiredMixin(LoginRequiredMixin):
    """Đặt mixin trước view; khai báo allowed_roles = ("Sales", ...)."""

    allowed_roles = ()

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        roles = get_user_roles(request.user)
        if "Admin" not in roles and not set(roles).intersection(self.allowed_roles):
            raise PermissionDenied("Bạn không có quyền truy cập chức năng này.")
        return super().dispatch(request, *args, **kwargs)
