from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("accounts.urls")),
    path("", include("catalog.urls")),
    path("", include("customers.urls")),
    path("", include("bookings.urls")),
    path("", include("operations.urls")),
    path("", include("reports.urls")),
]
handler403 = "accounts.views.permission_denied"
admin.site.site_header = "Quản trị hệ thống du lịch"
admin.site.site_title = "tourManager"
admin.site.index_title = "Quản lý dữ liệu nền"
