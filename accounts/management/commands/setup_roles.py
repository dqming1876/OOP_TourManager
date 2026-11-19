from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q


class Command(BaseCommand):
    help = "Tạo hoặc đồng bộ ba nhóm quyền Admin, Sales, Operator."

    @transaction.atomic
    def handle(self, *args, **options):
        # Gán lại tập quyền để chạy nhiều lần vẫn cho cùng một kết quả.
        catalog_views = Q(content_type__app_label="catalog", codename__startswith="view_")
        role_permissions = {
            "Admin": Permission.objects.all(),
            "Sales": Permission.objects.filter(catalog_views | Q(content_type__app_label__in=["customers", "bookings"])),
            "Operator": Permission.objects.filter(catalog_views | Q(content_type__app_label="operations")),
        }
        for role, permissions in role_permissions.items():
            group, _ = Group.objects.get_or_create(name=role)
            group.permissions.set(permissions)
            self.stdout.write(self.style.SUCCESS(f"{role}: {group.permissions.count()} quyền."))
