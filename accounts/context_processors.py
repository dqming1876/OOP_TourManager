from .roles import get_user_roles
from .services import pending_users


def current_role(request):
    roles = get_user_roles(request.user)
    is_admin = "Admin" in roles
    return {
        "user_roles": roles,
        "current_role": ", ".join(roles) if roles else "Chưa phân quyền",
        "is_admin_role": is_admin,
        "pending_user_count": pending_users().count() if is_admin else 0,
        "can_view_catalog": bool(roles),
        "can_manage_customers": is_admin or "Sales" in roles,
        "can_manage_bookings": is_admin or "Sales" in roles,
        "can_manage_operations": is_admin or "Operator" in roles,
        "can_view_reports": bool(roles),
    }
