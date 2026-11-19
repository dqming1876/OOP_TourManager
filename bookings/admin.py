from django.contrib import admin

from .models import Booking, Payment


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("code", "customer", "departure", "total_amount", "status", "created_by", "created_at")
    search_fields = ("code", "customer__full_name", "customer__phone")
    list_filter = ("status",)
    list_select_related = ("customer", "departure__tour", "created_by")
    readonly_fields = ("created_at",)
    list_per_page = 10


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("booking", "amount", "payment_type", "method", "paid_at", "received_by")
    search_fields = ("booking__code",)
    list_filter = ("payment_type", "method")
    list_select_related = ("booking__customer", "received_by")
    list_per_page = 10
