from django.contrib import admin

from .models import Customer


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("full_name", "phone", "email", "id_number")
    search_fields = ("full_name", "phone", "email")
    list_per_page = 10
