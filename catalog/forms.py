"""Biểu mẫu danh mục và bộ lịch trình theo ngày."""
from django import forms
from django.core.exceptions import ValidationError
from django.forms import BaseInlineFormSet, inlineformset_factory

from .models import Departure, Guide, Service, Supplier, Tour, TourItinerary, Vehicle


class BootstrapModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css_class = "form-select" if isinstance(field.widget, forms.Select) else "form-control"
            field.widget.attrs["class"] = css_class
            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs["rows"] = 3


class SupplierForm(BootstrapModelForm):
    class Meta:
        model = Supplier
        fields = ("name", "supplier_type", "phone", "email", "address")


class ServiceForm(BootstrapModelForm):
    class Meta:
        model = Service
        fields = ("name", "service_type", "supplier", "unit_price", "unit", "description")


class GuideForm(BootstrapModelForm):
    class Meta:
        model = Guide
        fields = ("full_name", "phone", "languages", "status")


class VehicleForm(BootstrapModelForm):
    class Meta:
        model = Vehicle
        fields = ("plate_number", "vehicle_type", "seats", "driver_name", "driver_phone", "status")


class TourForm(BootstrapModelForm):
    class Meta:
        model = Tour
        fields = ("code", "name", "days", "nights", "destination", "base_price", "description", "status")

    def clean(self):
        data = super().clean()
        days, nights = data.get("days"), data.get("nights")
        if days is not None and nights is not None and nights >= days:
            self.add_error("nights", "Số đêm phải nhỏ hơn số ngày của tour.")
        return data


class TourItineraryForm(BootstrapModelForm):
    class Meta:
        model = TourItinerary
        fields = ("day_number", "title", "content")


class BaseTourItineraryFormSet(BaseInlineFormSet):
    def __init__(self, *args, tour_days=None, **kwargs):
        self.tour_days = tour_days
        super().__init__(*args, **kwargs)

    def clean(self):
        super().clean()
        if any(self.errors):
            return
        day_numbers = []
        for form in self.forms:
            data = form.cleaned_data
            if not data or data.get("DELETE"):
                continue
            item = data.get("id")
            if item is not None and item.tour_id != self.instance.pk:
                raise ValidationError("Lịch trình gửi lên không thuộc tour đang sửa.")
            day_numbers.append(data["day_number"])
        if self.tour_days is not None and sorted(day_numbers) != list(range(1, self.tour_days + 1)):
            raise ValidationError("Cần nhập đủ lịch trình từ ngày 1 đến số ngày của tour, mỗi ngày xuất hiện đúng một lần.")


TourItineraryFormSet = inlineformset_factory(
    Tour,
    TourItinerary,
    form=TourItineraryForm,
    formset=BaseTourItineraryFormSet,
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True,
    validate_max=True,
)


class DepartureForm(BootstrapModelForm):
    class Meta:
        model = Departure
        fields = ("tour", "start_date", "end_date", "max_seats", "price", "status")
        widgets = {
            "start_date": forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
            "end_date": forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
        }

    def clean(self):
        data = super().clean()
        start, end = data.get("start_date"), data.get("end_date")
        if start and end and end < start:
            self.add_error("end_date", "Ngày kết thúc không được trước ngày khởi hành.")
        if self.instance.pk and data.get("max_seats") is not None:
            if data["max_seats"] < self.instance.booked_seats:
                self.add_error("max_seats", "Số chỗ tối đa không được nhỏ hơn số khách đã đặt chưa hủy.")
        return data


class DepartureFilterForm(forms.Form):
    q = forms.CharField(label="Tìm kiếm", required=False, widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Mã tour, tên tour, điểm đến"}))
    status = forms.ChoiceField(label="Trạng thái", required=False, choices=[("", "Tất cả trạng thái"), *Departure.Status.choices], widget=forms.Select(attrs={"class": "form-select"}))
    start_date = forms.DateField(label="Khởi hành từ ngày", required=False, widget=forms.DateInput(format="%Y-%m-%d", attrs={"type": "date", "class": "form-control"}))
    end_date = forms.DateField(label="Khởi hành đến ngày", required=False, widget=forms.DateInput(format="%Y-%m-%d", attrs={"type": "date", "class": "form-control"}))

    def clean(self):
        data = super().clean()
        start, end = data.get("start_date"), data.get("end_date")
        if start and end and end < start:
            raise ValidationError("Ngày kết thúc khoảng lọc phải từ ngày bắt đầu trở đi.")
        return data
