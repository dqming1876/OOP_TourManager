"""Tên nhóm quyền dùng thống nhất giữa view, template và dữ liệu mẫu."""
ROLE_NAMES = ("Admin", "Sales", "Operator")


def get_user_roles(user):
    if not user.is_authenticated:
        return ()
    if user.is_superuser:
        return ("Admin",)
    groups = set(user.groups.filter(name__in=ROLE_NAMES).values_list("name", flat=True))
    return tuple(role for role in ROLE_NAMES if role in groups)
