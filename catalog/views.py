from django.contrib import messages
from django.db import transaction
from django.db.models import BigIntegerField, F, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.http import HttpResponseRedirect

from .crud import EntityCreateView, EntityDeleteView, EntityDetailView, EntityListView, EntityUpdateView, paginate_related
from .forms import DepartureFilterForm, DepartureForm, GuideForm, ServiceForm, SupplierForm, TourForm, TourItineraryFormSet, VehicleForm
from .models import Departure, Guide, Service, Supplier, Tour, TourItinerary, Vehicle


class SupplierConfig:
    model = Supplier
    form_class = SupplierForm
    route_prefix = "catalog:supplier"
    search_fields = ("name", "supplier_type", "phone", "email", "address")
    list_fields = ("name", "supplier_type", "phone", "email")


class SupplierListView(SupplierConfig, EntityListView):
    pass


class SupplierDetailView(SupplierConfig, EntityDetailView):
    pass


class SupplierCreateView(SupplierConfig, EntityCreateView):
    pass


class SupplierUpdateView(SupplierConfig, EntityUpdateView):
    pass


class SupplierDeleteView(SupplierConfig, EntityDeleteView):
    pass


class ServiceConfig:
    model = Service
    form_class = ServiceForm
    route_prefix = "catalog:service"
    search_fields = ("name", "supplier__name", "unit", "description")
    select_related_fields = ("supplier",)
    list_fields = ("name", "service_type", "supplier", "unit_price", "unit")


class ServiceListView(ServiceConfig, EntityListView):
    pass


class ServiceDetailView(ServiceConfig, EntityDetailView):
    def get_queryset(self):
        return super().get_queryset().select_related("supplier")


class ServiceCreateView(ServiceConfig, EntityCreateView):
    pass


class ServiceUpdateView(ServiceConfig, EntityUpdateView):
    pass


class ServiceDeleteView(ServiceConfig, EntityDeleteView):
    pass


class GuideConfig:
    model = Guide
    form_class = GuideForm
    route_prefix = "catalog:guide"
    search_fields = ("full_name", "phone", "languages")
    list_fields = ("full_name", "phone", "languages", "status")


class GuideListView(GuideConfig, EntityListView):
    pass


class GuideDetailView(GuideConfig, EntityDetailView):
    pass


class GuideCreateView(GuideConfig, EntityCreateView):
    pass


class GuideUpdateView(GuideConfig, EntityUpdateView):
    pass


class GuideDeleteView(GuideConfig, EntityDeleteView):
    pass


class VehicleConfig:
    model = Vehicle
    form_class = VehicleForm
    route_prefix = "catalog:vehicle"
    search_fields = ("plate_number", "vehicle_type", "driver_name", "driver_phone")
    list_fields = ("plate_number", "vehicle_type", "seats", "driver_name", "status")


class VehicleListView(VehicleConfig, EntityListView):
    pass


class VehicleDetailView(VehicleConfig, EntityDetailView):
    pass


class VehicleCreateView(VehicleConfig, EntityCreateView):
    pass


class VehicleUpdateView(VehicleConfig, EntityUpdateView):
    pass


class VehicleDeleteView(VehicleConfig, EntityDeleteView):
    pass


class TourConfig:
    model = Tour
    form_class = TourForm
    route_prefix = "catalog:tour"
    search_fields = ("code", "name", "destination", "description")
    list_fields = ("code", "name", "days", "nights", "destination", "base_price", "status")


class TourListView(TourConfig, EntityListView):
    allowed_roles = ("Operator", "Sales")


class TourDetailView(TourConfig, EntityDetailView):
    allowed_roles = ("Operator", "Sales")
    template_name = "catalog/tour_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["itineraries"] = self.object.itineraries.all()
        context["departures"] = paginate_related(context, self.object.departures.all(), self.request)
        return context


class TourFormsetMixin:
    template_name = "catalog/tour_form.html"

    def get_itinerary_formset(self, form):
        return TourItineraryFormSet(
            data=self.request.POST if self.request.method == "POST" else None,
            instance=form.instance,
            prefix="itineraries",
            tour_days=form.cleaned_data.get("days") if form.is_bound else form.instance.days,
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if "itinerary_formset" not in context:
            context["itinerary_formset"] = self.get_itinerary_formset(context["form"])
        return context

    def form_valid(self, form):
        formset = self.get_itinerary_formset(form)
        if not formset.is_valid():
            return self.render_to_response(self.get_context_data(form=form, itinerary_formset=formset))
        with transaction.atomic():
            self.object = form.save()
            # Lịch trình không có bảng khác tham chiếu. Thay cả tập lịch trình
            # để đổi thứ tự ngày không va vào unique(tour, day_number) của MySQL.
            self.object.itineraries.all().delete()
            items = [TourItinerary(
                tour=self.object,
                day_number=row.cleaned_data["day_number"],
                title=row.cleaned_data["title"],
                content=row.cleaned_data["content"],
            ) for row in formset.forms if row.cleaned_data and not row.cleaned_data.get("DELETE")]
            TourItinerary.objects.bulk_create(items)
        messages.success(self.request, f"Đã {self.save_verb.lower()} tour và lịch trình thành công.")
        return HttpResponseRedirect(self.get_success_url())


class TourCreateView(TourFormsetMixin, TourConfig, EntityCreateView):
    pass


class TourUpdateView(TourFormsetMixin, TourConfig, EntityUpdateView):
    pass


class TourDeleteView(TourConfig, EntityDeleteView):
    pass


class DepartureConfig:
    model = Departure
    form_class = DepartureForm
    route_prefix = "catalog:departure"
    search_fields = ("tour__code", "tour__name", "tour__destination")
    select_related_fields = ("tour",)
    list_fields = ("tour", "start_date", "end_date", "max_seats", "price", "status")

    def get_queryset(self):
        return super().get_queryset().select_related("tour").annotate(
            reserved_seats=Coalesce(
                Sum(F("bookings__num_adults") + F("bookings__num_children"), filter=~Q(bookings__status="CANCELLED")),
                Value(0),
                output_field=BigIntegerField(),
            ),
        ).order_by("-start_date", "pk")


class DepartureListView(DepartureConfig, EntityListView):
    allowed_roles = ("Operator", "Sales")
    template_name = "catalog/departure_list.html"

    def get_queryset(self):
        queryset = super().get_queryset()
        self.filter_form = DepartureFilterForm(self.request.GET)
        if not self.filter_form.is_valid():
            return queryset.none()
        data = self.filter_form.cleaned_data
        if data.get("status"):
            queryset = queryset.filter(status=data["status"])
        if data.get("start_date"):
            queryset = queryset.filter(start_date__gte=data["start_date"])
        if data.get("end_date"):
            queryset = queryset.filter(start_date__lte=data["end_date"])
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filter_form"] = self.filter_form
        context["headers"][3] = "Đã đặt / Tối đa"
        for row, departure in zip(context["rows"], context["object_list"]):
            row["values"][3] = f"{departure.reserved_seats}/{departure.max_seats}"
        return context


class DepartureDetailView(DepartureConfig, EntityDetailView):
    allowed_roles = ("Operator", "Sales")
    template_name = "catalog/departure_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["booked_seats"] = self.object.reserved_seats
        context["available_seats"] = self.object.max_seats - self.object.reserved_seats
        bookings = self.object.bookings.select_related("customer", "departure__tour")
        context["bookings"] = paginate_related(context, bookings, self.request)
        return context


class DepartureCreateView(DepartureConfig, EntityCreateView):
    pass


class DepartureUpdateView(DepartureConfig, EntityUpdateView):
    pass


class DepartureDeleteView(DepartureConfig, EntityDeleteView):
    pass
