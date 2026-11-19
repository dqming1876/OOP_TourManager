from django.contrib import admin

from .models import GuideAssignment, TourExpense, VehicleAssignment


@admin.register(GuideAssignment)
class GuideAssignmentAdmin(admin.ModelAdmin):
    list_display = ("departure", "guide", "note")
    search_fields = ("departure__tour__code", "guide__full_name")
    list_select_related = ("departure__tour", "guide")
    list_per_page = 10


@admin.register(VehicleAssignment)
class VehicleAssignmentAdmin(admin.ModelAdmin):
    list_display = ("departure", "vehicle", "note")
    search_fields = ("departure__tour__code", "vehicle__plate_number")
    list_select_related = ("departure__tour", "vehicle")
    list_per_page = 10


@admin.register(TourExpense)
class TourExpenseAdmin(admin.ModelAdmin):
    list_display = ("departure", "service", "description", "amount", "expense_date")
    search_fields = ("departure__tour__code", "description")
    list_filter = ("expense_date",)
    list_select_related = ("departure__tour", "service")
    list_per_page = 10
