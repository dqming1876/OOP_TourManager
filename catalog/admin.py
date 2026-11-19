from django.contrib import admin

from .models import Departure, Guide, Service, Supplier, Tour, TourItinerary, Vehicle


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ("name", "supplier_type", "phone", "email")
    search_fields = ("name", "phone")
    list_filter = ("supplier_type",)
    list_per_page = 10


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("name", "service_type", "supplier", "unit_price", "unit")
    search_fields = ("name", "supplier__name")
    list_filter = ("service_type",)
    list_select_related = ("supplier",)
    list_per_page = 10


@admin.register(Guide)
class GuideAdmin(admin.ModelAdmin):
    list_display = ("full_name", "phone", "languages", "status")
    search_fields = ("full_name", "phone")
    list_filter = ("status",)
    list_per_page = 10


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ("plate_number", "vehicle_type", "seats", "driver_name", "status")
    search_fields = ("plate_number", "driver_name")
    list_filter = ("status",)
    list_per_page = 10


@admin.register(Tour)
class TourAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "days", "nights", "destination", "base_price", "status")
    search_fields = ("code", "name", "destination")
    list_filter = ("status",)
    list_per_page = 10


@admin.register(TourItinerary)
class TourItineraryAdmin(admin.ModelAdmin):
    list_display = ("tour", "day_number", "title")
    search_fields = ("tour__code", "title")
    list_select_related = ("tour",)
    list_per_page = 10


@admin.register(Departure)
class DepartureAdmin(admin.ModelAdmin):
    list_display = ("tour", "start_date", "end_date", "max_seats", "price", "status")
    search_fields = ("tour__code", "tour__name")
    list_filter = ("status", "start_date")
    list_select_related = ("tour",)
    list_per_page = 10
