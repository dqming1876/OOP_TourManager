# Mã nguồn đầy đủ của nhánh feature/catalog

Tài liệu chứa nguyên vẹn 30 tệp thêm/sửa, gồm cả kiểm thử và hướng dẫn. Mỗi khối code có đường dẫn tương ứng. Không có thay đổi model hoặc tệp khung.

## Cây thư mục các tệp thêm/sửa

```text
tourManager/
├── catalog/
│   ├── README.md
│   ├── crud.py
│   ├── forms.py
│   ├── management/
│   │   ├── __init__.py
│   │   └── commands/
│   │       ├── __init__.py
│   │       └── seed_catalog.py
│   ├── static/
│   │   └── catalog/
│   │       └── tourForm.js
│   ├── templates/
│   │   └── catalog/
│   │       ├── booking_table.html
│   │       ├── departure_detail.html
│   │       ├── departure_list.html
│   │       ├── entity_confirm_delete.html
│   │       ├── entity_detail.html
│   │       ├── entity_form.html
│   │       ├── entity_list.html
│   │       ├── field.html
│   │       ├── module_base.html
│   │       ├── pagination.html
│   │       ├── tour_detail.html
│   │       └── tour_form.html
│   ├── tests.py
│   ├── urls.py
│   └── views.py
└── customers/
    ├── forms.py
    ├── templates/
    │   └── customers/
    │       ├── customer_confirm_delete.html
    │       ├── customer_detail.html
    │       ├── customer_form.html
    │       └── customer_list.html
    ├── tests.py
    ├── urls.py
    └── views.py
```

## tourManager/catalog/README.md

````markdown
# Nhánh feature/catalog

## Phạm vi

CRUD Supplier, Service, Guide, Vehicle, Tour, Departure, Customer. Chỉ thay đổi tệp trong catalog và customers; không thay model, migration, settings, accounts, config/urls.py hoặc templates/base.html.

- Class-based views, ModelForm, inline formset cho TourItinerary.
- Tìm kiếm qua `?q=`, phân trang 10 dòng; các liên kết phân trang giữ nguyên điều kiện lọc.
- Lịch khởi hành lọc theo trạng thái và ngày khởi hành trong khoảng `start_date`–`end_date` (bao gồm hai đầu).
- Booking trong chi tiết chuyến/khách hàng chỉ đọc qua related_name `bookings`, phân trang 10 dòng; không phụ thuộc URL của nhánh operations.
- Xóa phải POST sau trang xác nhận, có CSRF; dữ liệu được FK PROTECT bảo vệ nhận thông báo bằng messages.

## Chạy

Kích hoạt môi trường ảo và cấu hình MySQL theo README của bộ khung, sau đó:

```bash
python manage.py migrate
python manage.py setup_roles
python manage.py seed_base
python manage.py seed_catalog
python manage.py test
python manage.py runserver
```

Không cần makemigrations vì schema không đổi. Dùng tài khoản demo do seed_base đã tạo; mật khẩu in khi tạo lần đầu. `seed_catalog` không tạo user, booking, payment, phân công hay chi phí.

Nếu đã chạy seed_base, seed_catalog bổ sung để có 5 nhà cung cấp, 10 dịch vụ, 4 HDV, 4 xe, 4 tour, 10 ngày lịch trình, 8 lịch khởi hành, 10 khách hàng. Chạy lại không trùng, không ghi đè dữ liệu đã sửa. Trên database đã có thêm dữ liệu người dùng, tổng số có thể lớn hơn bộ mẫu; command không xóa dữ liệu để ép số lượng. Địa danh/tuyến đi có thật; liên hệ, con người và giá là mô phỏng. Mốc khởi hành cố định tháng 12/2026 để seed chạy nhiều ngày vẫn không trùng.

## Phân quyền ở view

| Tác nhân | Supplier/Service/Guide/Vehicle | Tour/Departure | Customer |
|---|---|---|---|
| Admin hoặc superuser | CRUD | CRUD | CRUD |
| Operator | CRUD | CRUD | 403 |
| Sales | 403 | Danh sách, chi tiết | CRUD |
| Chưa đăng nhập | Chuyển tới login | Chuyển tới login | Chuyển tới login |
| Chưa có nhóm quyền | 403 | 403 | 403 |

Dùng RoleRequiredMixin của khung; không thêm PermissionRequiredMixin vì model permissions của Operator trong khung chưa theo ma trận mới. Mọi route tạo/sửa/xóa kiểm tra phía server, kể cả POST trực tiếp. Nút sửa/xóa được ẩn với người chỉ có quyền xem. Quyền của nhiều nhóm được hợp lại theo mixin hiện có.

## Lịch trình và dữ liệu liên quan

Tour và toàn bộ lịch trình chỉ được lưu sau khi cả ModelForm và inline formset hợp lệ. Mỗi ngày từ 1 đến Tour.days phải có đúng một lịch trình, không chấp nhận thiếu ngày hoặc trùng ngày. Số đêm phải nhỏ hơn số ngày.

Lưu trong transaction.atomic. Vì TourItinerary không có bảng khác tham chiếu trong schema hiện tại, tập lịch trình được thay bằng các dòng đã xác thực mỗi lần lưu tour. Cách này hỗ trợ đổi số thứ tự ngày trên MySQL mà không va ràng buộc unique(tour, day_number); khóa chính dòng lịch trình sẽ thay đổi, khóa chính Tour vẫn giữ nguyên. Nếu tương lai có bảng tham chiếu TourItinerary, cần xem lại cách lưu trước khi đổi schema.

Departure kiểm tra ngày kết thúc không trước ngày bắt đầu; khi sửa không cho đặt max_seats nhỏ hơn số khách đã đặt chưa hủy. Danh sách dùng SUM có điều kiện để tính chỗ như property booked_seats mà không phát sinh một truy vấn riêng cho mỗi dòng. Không tự đổi trạng thái, tính giá booking hoặc thực hiện điều hành đoàn.

Các CBV và template dùng chung nằm trong catalog/crud.py và catalog/templates/catalog/. Customer có ModelForm, CBV, namespace và template riêng; template kế thừa phần dùng chung để tránh lặp mã. Đây là hai app cùng thuộc nhánh catalog.

## Kiểm thử

Đã chạy trên Python 3.14.3, Django 5.2.19, MySQL 8.4.7 (utf8mb4):

```text
python manage.py test --noinput
Ran 55 tests
OK
```

Trong đó 40 test mới thuộc catalog/customers, 15 test có sẵn. Kiểm tra quyền GET/POST; CRUD và messages; CSRF; tìm kiếm/phân trang; formset thiếu/trùng ngày, đổi thứ tự, xóa ngày, gửi ID lịch trình khác tour; rollback; ngày lọc sai; số chỗ chưa hủy; FK PROTECT; booking chỉ đọc; seed từ DB trống và seed nối tiếp seed_base. `check` không có lỗi, `makemigrations --check --dry-run` không có thay đổi.

## Git

Nhánh đã được chuẩn bị từ main:

```bash
git checkout -b feature/catalog
```

Sau khi thêm mã nguồn (không chạy lại checkout -b nếu nhánh đã tồn tại):

```bash
git status
git add catalog customers
git diff --cached --name-only
git commit -m "Implement catalog and customer management"
git push -u origin feature/catalog
```

Chỉ merge vào main sau khi hai nhóm kiểm tra tích hợp. Không sửa hoặc đẩy vào feature/operations từ nhánh này.

## ĐỀ XUẤT THAY ĐỔI KHUNG

Chưa áp dụng các thay đổi bên dưới vì vượt phạm vi hai app:

1. accounts/context_processors.py và templates/base.html: tách quyền hiển thị menu Supplier/Service/Guide/Vehicle khỏi Tour/Departure, để Sales chỉ nhìn thấy hai menu tour và lịch khởi hành. Hiện sidebar của khung vẫn hiện bốn menu bị cấm với Sales; truy cập chúng nhận trang 403. Thanh điều hướng bổ sung trong module này đã lọc đúng vai trò.
2. accounts/management/commands/setup_roles.py: đồng bộ model permissions theo ma trận mới — Operator CRUD danh mục, Sales chỉ view Tour/Departure và CRUD Customer. Giữ nguyên phần quyền booking/operations theo thỏa thuận với nhóm còn lại.
3. README.md và docs/teamWorkflow.md của khung: cập nhật tên nhánh feature/catalog, feature/operations và ma trận quyền mới sau khi hai nhóm thống nhất.

Không cần thay schema, cấu hình database hay root URL để sử dụng nhánh này.

## Tài liệu Django

- [ModelForm và inline formset](https://docs.djangoproject.com/en/5.2/topics/forms/modelforms/).
- [Transaction atomic](https://docs.djangoproject.com/en/5.2/topics/db/transactions/).
- [Generic editing views](https://docs.djangoproject.com/en/5.2/ref/class-based-views/generic-editing/).
````

## tourManager/catalog/crud.py

```python
"""Các CBV dùng lại cho danh mục và khách hàng, không sửa khung chung."""
from datetime import date, datetime
from decimal import Decimal

from django import forms
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.db.models.deletion import ProtectedError
from django.urls import reverse
from django.utils import formats, timezone
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from accounts.mixins import RoleRequiredMixin
from accounts.roles import get_user_roles


def display_value(obj, name):
    value = getattr(obj, name)
    get_label = getattr(obj, f"get_{name}_display", None)
    if get_label:
        return get_label()
    if value is None or value == "":
        return "—"
    if isinstance(value, datetime):
        return formats.date_format(timezone.localtime(value), "d/m/Y H:i")
    if isinstance(value, date):
        return formats.date_format(value, "d/m/Y")
    if isinstance(value, Decimal):
        return formats.number_format(value, decimal_pos=0, force_grouping=True)
    return str(value)


def paginate_related(context, queryset, request):
    page = Paginator(queryset, 10).get_page(request.GET.get("page"))
    query = request.GET.copy()
    query.pop("page", None)
    context.update(page_obj=page, paginator=page.paginator, is_paginated=page.has_other_pages(), pagination_query=query.urlencode())
    return page


class EntityContextMixin:
    route_prefix = ""
    manager_roles = ("Operator",)
    list_fields = ()
    detail_fields = ()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        roles = get_user_roles(self.request.user)
        context.update({
            "entity_name": self.model._meta.verbose_name,
            "list_url": reverse(f"{self.route_prefix}_list"),
            "create_url": reverse(f"{self.route_prefix}_create"),
            "can_manage": "Admin" in roles or bool(set(roles).intersection(self.manager_roles)),
            "save_verb": getattr(self, "save_verb", ""),
        })
        obj = getattr(self, "object", None)
        if obj is not None:
            context["detail_url"] = reverse(f"{self.route_prefix}_detail", args=[obj.pk])
            context["update_url"] = reverse(f"{self.route_prefix}_update", args=[obj.pk])
            context["delete_url"] = reverse(f"{self.route_prefix}_delete", args=[obj.pk])
            names = self.detail_fields or tuple(field.name for field in self.model._meta.fields if field.name != "id")
            context["details"] = [(self.model._meta.get_field(name).verbose_name, display_value(obj, name)) for name in names]
        return context


class EntityListView(EntityContextMixin, RoleRequiredMixin, ListView):
    allowed_roles = ("Operator",)
    template_name = "catalog/entity_list.html"
    paginate_by = 10
    search_fields = ()
    select_related_fields = ()

    def get_queryset(self):
        queryset = super().get_queryset().select_related(*self.select_related_fields)
        q = self.request.GET.get("q", "").strip()
        if q:
            condition = Q()
            for name in self.search_fields:
                condition |= Q(**{f"{name}__icontains": q})
            queryset = queryset.filter(condition)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.copy()
        query.pop("page", None)
        context["pagination_query"] = query.urlencode()
        context["q"] = self.request.GET.get("q", "").strip()
        context["headers"] = [self.model._meta.get_field(name).verbose_name for name in self.list_fields]
        context["rows"] = [{
            "values": [display_value(obj, name) for name in self.list_fields],
            "detail_url": reverse(f"{self.route_prefix}_detail", args=[obj.pk]),
            "update_url": reverse(f"{self.route_prefix}_update", args=[obj.pk]),
            "delete_url": reverse(f"{self.route_prefix}_delete", args=[obj.pk]),
        } for obj in context["object_list"]]
        return context


class EntityDetailView(EntityContextMixin, RoleRequiredMixin, DetailView):
    allowed_roles = ("Operator",)
    template_name = "catalog/entity_detail.html"


class SavedMessageMixin:
    def get_success_url(self):
        return reverse(f"{self.route_prefix}_detail", args=[self.object.pk])

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Đã {self.save_verb.lower()} {self.model._meta.verbose_name.lower()} thành công.")
        return response


class EntityCreateView(EntityContextMixin, RoleRequiredMixin, SavedMessageMixin, CreateView):
    allowed_roles = ("Operator",)
    template_name = "catalog/entity_form.html"
    save_verb = "Thêm"


class EntityUpdateView(EntityContextMixin, RoleRequiredMixin, SavedMessageMixin, UpdateView):
    allowed_roles = ("Operator",)
    template_name = "catalog/entity_form.html"
    save_verb = "Cập nhật"


class EntityDeleteView(EntityContextMixin, RoleRequiredMixin, DeleteView):
    allowed_roles = ("Operator",)
    template_name = "catalog/entity_confirm_delete.html"

    def get_form_class(self):
        # Form xóa chỉ cần xác nhận, không dùng ModelForm của trang thêm/sửa.
        return forms.Form

    def get_success_url(self):
        return reverse(f"{self.route_prefix}_list")

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
        except ProtectedError:
            messages.error(self.request, "Không thể xóa vì bản ghi đang được dữ liệu khác tham chiếu. Hãy xử lý dữ liệu liên quan trước.")
            return self.render_to_response(self.get_context_data(form=form))
        messages.success(self.request, f"Đã xóa {self.model._meta.verbose_name.lower()} thành công.")
        return response
```

## tourManager/catalog/forms.py

```python
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
```

## tourManager/catalog/management/__init__.py

Tệp rỗng để nhận diện Python package.

```python
```

## tourManager/catalog/management/commands/__init__.py

Tệp rỗng để nhận diện Python package.

```python
```

## tourManager/catalog/management/commands/seed_catalog.py

```python
"""Bổ sung bộ dữ liệu cố định, tương thích với seed_base của bộ khung."""
from datetime import date
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from catalog.models import Departure, Guide, Service, Supplier, Tour, TourItinerary, Vehicle
from customers.models import Customer


class Command(BaseCommand):
    help = "Bổ sung bộ mẫu 5 NCC, 10 dịch vụ, 4 HDV, 4 xe, 4 tour, 8 chuyến, 10 khách."

    @transaction.atomic
    def handle(self, *args, **options):
        # Tuyến đi/địa danh có thật; liên hệ, nhân sự và giá là dữ liệu mô phỏng.
        suppliers = []
        for name, kind, phone, email, address in [
            ("Khách sạn Hạ Long Xanh (mẫu)", "Lưu trú", "0900000001", "halong@example.com", "Bãi Cháy, Quảng Ninh"),
            ("Dịch vụ du lịch Việt Bắc (mẫu)", "Dịch vụ tổng hợp", "0900000002", "vietbac@example.com", "Hoàn Kiếm, Hà Nội"),
            ("Nhà hàng Cơm Việt Hội An (mẫu)", "Ăn uống và tham quan", "0900000003", "hoian@example.com", "Phố cổ Hội An, Đà Nẵng"),
            ("Khách sạn Mường Hoa Sa Pa (mẫu)", "Lưu trú", "0900000004", "sapa@example.com", "Sa Pa, Lào Cai"),
            ("Dịch vụ du lịch Tràng An (mẫu)", "Tham quan và hướng dẫn", "0900000005", "trangan@example.com", "Khu du lịch Tràng An, Ninh Bình"),
        ]:
            item, _ = Supplier.objects.get_or_create(name=name, defaults={
                "supplier_type": kind, "phone": phone, "email": email, "address": address,
            })
            suppliers.append(item)

        for name, kind, supplier_index, price, unit, description in [
            ("Phòng đôi Bãi Cháy", "LODGING", 0, "800000", "phòng/đêm", "Phòng đôi cho 2 khách, gồm bữa sáng."),
            ("Xe du lịch Hà Nội - Hạ Long", "TRANSPORT", 1, "3500000", "xe/ngày", "Xe 29 chỗ phục vụ đoàn."),
            ("Suất ăn đặc sản địa phương", "MEAL", 1, "180000", "suất", "Thực đơn đoàn gồm món địa phương."),
            ("Vé tham quan vịnh Hạ Long", "TICKET", 1, "310000", "khách", "Giá mẫu cho đồ án, không phải báo giá thương mại."),
            ("Phòng đôi Mường Hoa", "LODGING", 3, "650000", "phòng/đêm", "Lưu trú tại Sa Pa, phòng cho 2 khách."),
            ("Suất ăn phố Hội", "MEAL", 2, "160000", "suất", "Cơm đoàn với món ăn đặc trưng Hội An."),
            ("Vé thuyền Tràng An", "TICKET", 4, "250000", "khách", "Tham quan cảnh quan bằng thuyền, giá mô phỏng."),
            ("Hướng dẫn viên tuyến Ninh Bình", "GUIDE", 4, "1000000", "ngày", "Hướng dẫn đoàn nói tiếng Việt."),
            ("Xe Hà Nội - Sa Pa", "TRANSPORT", 1, "4500000", "xe/ngày", "Xe du lịch 16 chỗ theo tuyến Nội Bài - Lào Cai."),
            ("Vé tham quan phố cổ Hội An", "TICKET", 2, "120000", "khách", "Giá mẫu phục vụ việc nhập và kiểm tra dữ liệu."),
        ]:
            Service.objects.get_or_create(name=name, supplier=suppliers[supplier_index], defaults={
                "service_type": kind, "unit_price": Decimal(price), "unit": unit, "description": description,
            })

        for name, phone, languages in [
            ("Nguyễn Minh Anh", "0900000011", "Tiếng Việt, Tiếng Anh"),
            ("Trần Hoàng Nam", "0900000012", "Tiếng Việt, Tiếng Trung"),
            ("Lê Thảo Nguyên", "0900000013", "Tiếng Việt, Tiếng Anh"),
            ("Phạm Quốc Bảo", "0900000014", "Tiếng Việt, Tiếng Pháp"),
        ]:
            Guide.objects.get_or_create(full_name=name, phone=phone, defaults={"languages": languages})
        for plate, kind, seats, driver, phone in [
            ("29B-900.01", "Thaco Town 29 chỗ", 29, "Lê Văn Hùng", "0900000021"),
            ("29B-900.02", "Ford Transit 16 chỗ", 16, "Phạm Văn Hải", "0900000022"),
            ("43B-900.03", "Hyundai Universe 45 chỗ", 45, "Nguyễn Đức Sơn", "0900000023"),
            ("29B-900.04", "Ford Transit 16 chỗ", 16, "Trần Việt Dũng", "0900000024"),
        ]:
            Vehicle.objects.get_or_create(plate_number=plate, defaults={
                "vehicle_type": kind, "seats": seats, "driver_name": driver, "driver_phone": phone,
            })

        tours = {}
        for code, name, days, nights, destination, price, itinerary in [
            ("HNHL2N1D", "Hà Nội - Hạ Long 2 ngày 1 đêm", 2, 1, "Vịnh Hạ Long, Quảng Ninh", "2450000", [
                ("Hà Nội - Hạ Long", "Đón khách tại Hà Nội, đi cao tốc đến Hạ Long. Ăn trưa, nhận phòng và tham quan Bãi Cháy."),
                ("Tham quan vịnh - Hà Nội", "Tham quan hang Sửng Sốt, đảo Ti Tốp. Ăn trưa trên tàu và trở về Hà Nội."),
            ]),
            ("HNSP3N2D", "Hà Nội - Sa Pa 3 ngày 2 đêm", 3, 2, "Sa Pa, Lào Cai", "3650000", [
                ("Hà Nội - Sa Pa", "Đi theo cao tốc Nội Bài - Lào Cai. Nhận phòng và thăm nhà thờ đá Sa Pa."),
                ("Fansipan - bản Cát Cát", "Tham quan khu du lịch Fansipan và tìm hiểu văn hóa tại bản Cát Cát."),
                ("Sa Pa - Hà Nội", "Mua đặc sản, trả phòng và về Hà Nội bằng xe du lịch."),
            ]),
            ("HNTR2N1D", "Hà Nội - Ninh Bình 2 ngày 1 đêm", 2, 1, "Tràng An, Tam Cốc, Ninh Bình", "1950000", [
                ("Hà Nội - Tràng An", "Khởi hành từ Hà Nội, đi thuyền tại quần thể danh thắng Tràng An. Ăn tối và nghỉ tại Ninh Bình."),
                ("Tam Cốc - Hà Nội", "Tham quan Tam Cốc và thưởng thức ẩm thực địa phương. Buổi chiều trở về Hà Nội."),
            ]),
            ("DNHA3N2D", "Đà Nẵng - Hội An 3 ngày 2 đêm", 3, 2, "Đà Nẵng, Hội An", "3250000", [
                ("Đón khách - bán đảo Sơn Trà", "Đón khách tại Đà Nẵng, tham quan chùa Linh Ứng và nghỉ tại khách sạn."),
                ("Ngũ Hành Sơn - phố cổ Hội An", "Thăm Ngũ Hành Sơn, đi bộ trong phố cổ Hội An và tìm hiểu các làng nghề."),
                ("Biển Mỹ Khê - tiễn khách", "Dạo biển Mỹ Khê, mua đặc sản và tiễn khách tại sân bay hoặc ga Đà Nẵng."),
            ]),
        ]:
            tour, _ = Tour.objects.get_or_create(code=code, defaults={
                "name": name, "days": days, "nights": nights, "destination": destination,
                "base_price": Decimal(price), "description": f"Tour trọn gói {days} ngày {nights} đêm. Dữ liệu mô phỏng phục vụ đồ án.",
            })
            tours[code] = tour
            # Không ghi đè tour/lịch trình mà người học đã chỉnh sửa.
            if tour.days == days:
                for day, (title, content) in enumerate(itinerary, start=1):
                    TourItinerary.objects.get_or_create(tour=tour, day_number=day, defaults={"title": title, "content": content})
        for code, start, end, seats, price in [
            ("HNHL2N1D", "2026-12-05", "2026-12-06", 29, "2450000"),
            ("HNHL2N1D", "2026-12-12", "2026-12-13", 29, "2550000"),
            ("HNSP3N2D", "2026-12-19", "2026-12-21", 16, "3650000"),
            ("HNHL2N1D", "2026-12-19", "2026-12-20", 29, "2450000"),
            ("HNHL2N1D", "2026-12-26", "2026-12-27", 29, "2550000"),
            ("HNSP3N2D", "2026-12-26", "2026-12-28", 16, "3750000"),
            ("HNTR2N1D", "2026-12-12", "2026-12-13", 29, "1950000"),
            ("DNHA3N2D", "2026-12-19", "2026-12-21", 45, "3250000"),
        ]:
            Departure.objects.get_or_create(tour=tours[code], start_date=date.fromisoformat(start), defaults={
                "end_date": date.fromisoformat(end), "max_seats": seats, "price": Decimal(price),
            })
        for name, phone, email, address in [
            ("Nguyễn Thu Hà", "0900000031", "thuha@example.com", "Cầu Giấy, Hà Nội"),
            ("Trần Đức Long", "0900000032", "duclong@example.com", "Lê Chân, Hải Phòng"),
            ("Lê Ngọc Mai", "0900000033", "ngocmai@example.com", "Hải Châu, Đà Nẵng"),
            ("Hoàng Minh Đức", "0900000034", "minhduc@example.com", "Đống Đa, Hà Nội"),
            ("Phạm Thanh Hương", "0900000035", "thanhhuong@example.com", "Ninh Kiều, Cần Thơ"),
            ("Đỗ Hải Yến", "0900000036", "haiyen@example.com", "Thành phố Hồ Chí Minh"),
            ("Vũ Anh Tuấn", "0900000037", "anhtuan@example.com", "Hạ Long, Quảng Ninh"),
            ("Bùi Thu Trang", "0900000038", "thutrang@example.com", "Phú Xuân, Huế"),
            ("Ngô Gia Bảo", "0900000039", "giabao@example.com", "Nha Trang, Khánh Hòa"),
            ("Đặng Khánh Linh", "0900000040", "khanhlinh@example.com", "Sa Pa, Lào Cai"),
        ]:
            Customer.objects.get_or_create(full_name=name, phone=phone, defaults={
                "email": email, "address": address, "note": "Khách hàng mô phỏng phục vụ đồ án.",
            })
        models = (Supplier, Service, Guide, Vehicle, Tour, TourItinerary, Departure, Customer)
        for model in models:
            self.stdout.write(f"{model._meta.verbose_name}: {model.objects.count()}")
        self.stdout.write(self.style.SUCCESS("Đã bổ sung danh mục; không tạo booking, thanh toán hoặc phân công."))
```

## tourManager/catalog/static/catalog/tourForm.js

```javascript
document.addEventListener("DOMContentLoaded", () => {
  const addButton = document.getElementById("addItinerary");
  const rows = document.getElementById("itineraryRows");
  const totalForms = document.getElementById("id_itineraries-TOTAL_FORMS");
  const emptyForm = document.getElementById("emptyItinerary");
  if (!addButton || !rows || !totalForms || !emptyForm) return;

  addButton.addEventListener("click", () => {
    const index = Number(totalForms.value);
    const fragment = emptyForm.content.cloneNode(true);
    fragment.querySelectorAll("[name], [id], [for]").forEach((element) => {
      ["name", "id", "for"].forEach((attribute) => {
        if (element.hasAttribute(attribute)) {
          element.setAttribute(attribute, element.getAttribute(attribute).replaceAll("__prefix__", String(index)));
        }
      });
    });
    rows.appendChild(fragment);
    totalForms.value = String(index + 1);
    rows.lastElementChild.querySelector("input:not([type='hidden'])")?.focus();
  });
});
```

## tourManager/catalog/templates/catalog/booking_table.html

```html
<div class="table-responsive">
  <table class="table align-middle">
    <thead><tr><th>Mã đặt tour</th><th>Khách hàng</th><th>Lịch khởi hành</th><th>Người lớn</th><th>Trẻ em</th><th>Tổng tiền (VNĐ)</th><th>Trạng thái</th></tr></thead>
    <tbody>
      {% for booking in bookings %}
      <tr><td>{{ booking.code }}</td><td>{{ booking.customer.full_name }}</td><td>{{ booking.departure }}</td><td>{{ booking.num_adults }}</td><td>{{ booking.num_children }}</td><td>{{ booking.total_amount|floatformat:"0g" }}</td><td>{{ booking.get_status_display }}</td></tr>
      {% empty %}<tr><td colspan="7" class="text-center text-secondary py-4">Chưa có booking nào.</td></tr>{% endfor %}
    </tbody>
  </table>
</div>
{% include "catalog/pagination.html" %}
```

## tourManager/catalog/templates/catalog/departure_detail.html

```html
{% extends "catalog/entity_detail.html" %}
{% block related_content %}
<section class="page-card p-3 p-md-4 mb-4">
  <h2 class="h5">Tình trạng chỗ</h2>
  <p class="mb-1">Đã đặt: <strong>{{ booked_seats }}/{{ object.max_seats }}</strong> · Còn lại: <strong>{{ available_seats }}</strong></p>
  <p class="small text-secondary mb-0">Chỉ loại booking đã hủy khi tính số chỗ đã đặt.</p>
</section>
<section class="page-card p-3 p-md-4">
  <h2 class="h5 mb-3">Danh sách booking — chỉ đọc</h2>
  {% include "catalog/booking_table.html" %}
</section>
{% endblock %}
```

## tourManager/catalog/templates/catalog/departure_list.html

```html
{% extends "catalog/entity_list.html" %}
{% block filters %}
<form method="get" class="row g-3 align-items-end mb-4">
  {% if filter_form.non_field_errors %}<div class="col-12"><div class="alert alert-danger mb-0">{{ filter_form.non_field_errors }}</div></div>{% endif %}
  {% for field in filter_form %}
  <div class="col-sm-6 col-lg-3"><label class="form-label" for="{{ field.id_for_label }}">{{ field.label }}</label>{{ field }}{% for error in field.errors %}<div class="small text-danger mt-1">{{ error }}</div>{% endfor %}</div>
  {% endfor %}
  <div class="col-12 d-flex gap-2"><button class="btn btn-primary" type="submit">Lọc lịch khởi hành</button><a class="btn btn-outline-secondary" href="{{ list_url }}">Đặt lại</a></div>
</form>
<p class="small text-secondary">Khoảng ngày được tính theo ngày khởi hành. Số chỗ đã đặt không bao gồm booking đã hủy.</p>
{% endblock %}
```

## tourManager/catalog/templates/catalog/entity_confirm_delete.html

```html
{% extends "catalog/module_base.html" %}
{% block module_content %}
<section class="page-card p-4 mx-auto" style="max-width: 700px;">
  <h1 class="h3">Xác nhận xóa {{ entity_name|lower }}</h1>
  <p>Bạn có chắc muốn xóa <strong>{{ object }}</strong>?</p>
  <p class="text-secondary">Thao tác chỉ thực hiện sau khi bạn bấm xác nhận. Dữ liệu đang được tham chiếu sẽ được bảo vệ.</p>
  <form method="post">
    {% csrf_token %}
    {{ form.non_field_errors }}
    <button class="btn btn-danger" type="submit">Xác nhận xóa</button>
    <a class="btn btn-outline-secondary" href="{{ detail_url }}">Hủy</a>
  </form>
</section>
{% endblock %}
```

## tourManager/catalog/templates/catalog/entity_detail.html

```html
{% extends "catalog/module_base.html" %}
{% block module_content %}
<a class="text-decoration-none" href="{{ list_url }}">← Danh sách {{ entity_name|lower }}</a>
<div class="d-flex flex-wrap justify-content-between align-items-center gap-3 my-4">
  <div><p class="text-secondary small mb-1">Chi tiết {{ entity_name|lower }}</p><h1 class="h3 mb-0">{{ object }}</h1></div>
  {% if can_manage %}
  <div class="d-flex gap-2"><a class="btn btn-primary" href="{{ update_url }}">Sửa thông tin</a><a class="btn btn-outline-danger" href="{{ delete_url }}">Xóa</a></div>
  {% endif %}
</div>
<section class="page-card p-3 p-md-4 mb-4">
  <dl class="row mb-0">
    {% for label, value in details %}<dt class="col-sm-4 col-lg-3 mb-2">{{ label }}</dt><dd class="col-sm-8 col-lg-9 mb-3">{{ value|linebreaksbr }}</dd>{% endfor %}
  </dl>
</section>
{% block related_content %}{% endblock %}
{% endblock %}
```

## tourManager/catalog/templates/catalog/entity_form.html

```html
{% extends "catalog/module_base.html" %}
{% block module_content %}
<a class="text-decoration-none" href="{{ list_url }}">← Danh sách {{ entity_name|lower }}</a>
<h1 class="h3 mt-3 mb-4">{{ save_verb }} {{ entity_name|lower }}</h1>
<form method="post" class="page-card p-3 p-md-4" novalidate>
  {% csrf_token %}
  {% if form.errors %}<div class="alert alert-danger" role="alert">Vui lòng kiểm tra các trường được báo lỗi.</div>{% endif %}
  {% if form.non_field_errors %}<div class="alert alert-danger">{{ form.non_field_errors }}</div>{% endif %}
  {% for field in form %}{% include "catalog/field.html" with field=field %}{% endfor %}
  {% block extra_form_content %}{% endblock %}
  <div class="d-flex gap-2 mt-4">
    <button class="btn btn-primary" type="submit">Lưu thông tin</button>
    <a class="btn btn-outline-secondary" href="{% if object %}{{ detail_url }}{% else %}{{ list_url }}{% endif %}">Hủy</a>
  </div>
</form>
{% endblock %}
```

## tourManager/catalog/templates/catalog/entity_list.html

```html
{% extends "catalog/module_base.html" %}
{% block module_content %}
<div class="d-flex flex-wrap align-items-center justify-content-between gap-3 mb-4">
  <div><h1 class="h3 mb-1">{{ entity_name }}</h1><p class="text-secondary mb-0">Tổng số: {{ paginator.count }} bản ghi</p></div>
  {% if can_manage %}<a class="btn btn-primary" href="{{ create_url }}">Thêm {{ entity_name|lower }}</a>{% endif %}
</div>
<section class="page-card p-3 p-md-4">
  {% block filters %}
  <form method="get" class="row g-2 align-items-end mb-4">
    <div class="col-sm-8 col-lg-5">
      <label class="form-label" for="searchQuery">Tìm kiếm</label>
      <input class="form-control" type="search" id="searchQuery" name="q" value="{{ q }}" placeholder="Nhập từ khóa">
    </div>
    <div class="col-auto"><button class="btn btn-primary" type="submit">Tìm kiếm</button></div>
    <div class="col-auto"><a class="btn btn-outline-secondary" href="{{ list_url }}">Đặt lại</a></div>
  </form>
  {% endblock %}
  <div class="table-responsive">
    <table class="table table-hover align-middle mb-0">
      <thead class="table-light"><tr>{% for header in headers %}<th scope="col" class="text-nowrap">{{ header }}</th>{% endfor %}<th scope="col" class="text-end">Thao tác</th></tr></thead>
      <tbody>
        {% for row in rows %}
        <tr>
          {% for value in row.values %}<td>{{ value }}</td>{% endfor %}
          <td class="text-end text-nowrap">
            <a class="btn btn-sm btn-outline-primary" href="{{ row.detail_url }}">Chi tiết</a>
            {% if can_manage %}
            <a class="btn btn-sm btn-outline-secondary" href="{{ row.update_url }}">Sửa</a>
            <a class="btn btn-sm btn-outline-danger" href="{{ row.delete_url }}">Xóa</a>
            {% endif %}
          </td>
        </tr>
        {% empty %}
        <tr><td colspan="{{ headers|length|add:'1' }}" class="text-center text-secondary py-5">Chưa có dữ liệu phù hợp.</td></tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
  {% include "catalog/pagination.html" %}
</section>
{% endblock %}
```

## tourManager/catalog/templates/catalog/field.html

```html
{% if field.is_hidden %}
  {{ field }}
  {% for error in field.errors %}<div class="text-danger small">{{ error }}</div>{% endfor %}
{% elif field.field.widget.input_type == "checkbox" %}
  <div class="form-check mb-3">{{ field }} <label class="form-check-label" for="{{ field.id_for_label }}">{{ field.label }}</label></div>
{% else %}
  <div class="mb-3">
    <label class="form-label fw-semibold" for="{{ field.id_for_label }}">{{ field.label }}{% if field.field.required %} <span class="text-danger" aria-label="bắt buộc">*</span>{% endif %}</label>
    {{ field }}
    {% if field.help_text %}<div class="form-text">{{ field.help_text }}</div>{% endif %}
    {% for error in field.errors %}<div class="text-danger small mt-1" role="alert">{{ error }}</div>{% endfor %}
  </div>
{% endif %}
```

## tourManager/catalog/templates/catalog/module_base.html

```html
{% extends "base.html" %}
{% block title %}{{ entity_name }}{% endblock %}
{% block content %}
<nav class="d-flex flex-wrap gap-2 mb-4" aria-label="Danh mục và khách hàng">
  {% if "Admin" in user_roles or "Operator" in user_roles %}
  <a class="btn btn-sm btn-outline-secondary" href="{% url 'catalog:supplier_list' %}">Nhà cung cấp</a>
  <a class="btn btn-sm btn-outline-secondary" href="{% url 'catalog:service_list' %}">Dịch vụ</a>
  <a class="btn btn-sm btn-outline-secondary" href="{% url 'catalog:guide_list' %}">Hướng dẫn viên</a>
  <a class="btn btn-sm btn-outline-secondary" href="{% url 'catalog:vehicle_list' %}">Xe</a>
  {% endif %}
  <a class="btn btn-sm btn-outline-secondary" href="{% url 'catalog:tour_list' %}">Tour</a>
  <a class="btn btn-sm btn-outline-secondary" href="{% url 'catalog:departure_list' %}">Lịch khởi hành</a>
  {% if "Admin" in user_roles or "Sales" in user_roles %}
  <a class="btn btn-sm btn-outline-secondary" href="{% url 'customers:customer_list' %}">Khách hàng</a>
  {% endif %}
</nav>
{% block module_content %}{% endblock %}
{% endblock %}
```

## tourManager/catalog/templates/catalog/pagination.html

```html
{% if is_paginated %}
<nav class="d-flex flex-wrap align-items-center justify-content-between gap-3 mt-4" aria-label="Phân trang">
  <span class="small text-secondary">Hiển thị {{ page_obj.start_index }}–{{ page_obj.end_index }} / {{ paginator.count }} bản ghi</span>
  <ul class="pagination mb-0">
    {% if page_obj.has_previous %}
    <li class="page-item"><a class="page-link" href="?{% if pagination_query %}{{ pagination_query }}&amp;{% endif %}page=1">Đầu</a></li>
    <li class="page-item"><a class="page-link" href="?{% if pagination_query %}{{ pagination_query }}&amp;{% endif %}page={{ page_obj.previous_page_number }}">Trước</a></li>
    {% endif %}
    <li class="page-item active" aria-current="page"><span class="page-link">{{ page_obj.number }} / {{ paginator.num_pages }}</span></li>
    {% if page_obj.has_next %}
    <li class="page-item"><a class="page-link" href="?{% if pagination_query %}{{ pagination_query }}&amp;{% endif %}page={{ page_obj.next_page_number }}">Sau</a></li>
    <li class="page-item"><a class="page-link" href="?{% if pagination_query %}{{ pagination_query }}&amp;{% endif %}page={{ paginator.num_pages }}">Cuối</a></li>
    {% endif %}
  </ul>
</nav>
{% endif %}
```

## tourManager/catalog/templates/catalog/tour_detail.html

```html
{% extends "catalog/entity_detail.html" %}
{% block related_content %}
<section class="page-card p-3 p-md-4 mb-4">
  <h2 class="h5 mb-4">Lịch trình tour</h2>
  {% for itinerary in itineraries %}
  <article class="border-start border-3 border-primary ps-3 mb-4">
    <h3 class="h6">Ngày {{ itinerary.day_number }}: {{ itinerary.title }}</h3>
    <div>{{ itinerary.content|linebreaksbr }}</div>
  </article>
  {% empty %}<p class="text-secondary mb-0">Tour chưa có lịch trình.</p>{% endfor %}
</section>
<section class="page-card p-3 p-md-4">
  <h2 class="h5 mb-3">Lịch khởi hành</h2>
  <div class="table-responsive">
    <table class="table align-middle">
      <thead><tr><th>Khởi hành</th><th>Kết thúc</th><th>Số chỗ tối đa</th><th>Giá bán (VNĐ)</th><th>Trạng thái</th><th></th></tr></thead>
      <tbody>
        {% for departure in departures %}
        <tr><td>{{ departure.start_date|date:"d/m/Y" }}</td><td>{{ departure.end_date|date:"d/m/Y" }}</td><td>{{ departure.max_seats }}</td><td>{{ departure.price|floatformat:"0g" }}</td><td>{{ departure.get_status_display }}</td><td><a href="{% url 'catalog:departure_detail' departure.pk %}">Chi tiết</a></td></tr>
        {% empty %}<tr><td colspan="6" class="text-center text-secondary py-4">Tour chưa có lịch khởi hành.</td></tr>{% endfor %}
      </tbody>
    </table>
  </div>
  {% include "catalog/pagination.html" %}
</section>
{% endblock %}
```

## tourManager/catalog/templates/catalog/tour_form.html

```html
{% extends "catalog/entity_form.html" %}
{% load static %}
{% block extra_form_content %}
<hr class="my-4">
<div class="d-flex flex-wrap align-items-center justify-content-between gap-3 mb-3">
  <div><h2 class="h5 mb-1">Lịch trình theo ngày</h2><p class="text-secondary small mb-0">Nhập đủ ngày 1 đến số ngày của tour. Đánh dấu “Xóa” để bỏ một dòng.</p></div>
  <button class="btn btn-outline-primary btn-sm" type="button" id="addItinerary">Thêm ngày</button>
</div>
{{ itinerary_formset.management_form }}
{% if itinerary_formset.non_form_errors %}<div class="alert alert-danger" role="alert">{{ itinerary_formset.non_form_errors }}</div>{% endif %}
<div id="itineraryRows">
  {% for itinerary_form in itinerary_formset %}
  <fieldset class="border rounded-3 p-3 mb-3 itinerary-row">
    <legend class="float-none w-auto px-2 fs-6 fw-semibold">Lịch trình {{ forloop.counter }}</legend>
    {% if itinerary_form.non_field_errors %}<div class="alert alert-danger">{{ itinerary_form.non_field_errors }}</div>{% endif %}
    {% for field in itinerary_form %}{% include "catalog/field.html" with field=field %}{% endfor %}
  </fieldset>
  {% endfor %}
</div>
<template id="emptyItinerary">
  <fieldset class="border rounded-3 p-3 mb-3 itinerary-row">
    <legend class="float-none w-auto px-2 fs-6 fw-semibold">Ngày bổ sung</legend>
    {% for field in itinerary_formset.empty_form %}{% include "catalog/field.html" with field=field %}{% endfor %}
  </fieldset>
</template>
{% endblock %}
{% block extra_js %}{{ block.super }}<script src="{% static 'catalog/tourForm.js' %}"></script>{% endblock %}
```

## tourManager/catalog/tests.py

```python
from datetime import date
from decimal import Decimal
from io import StringIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.db import IntegrityError, connection
from django.test import Client, TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from bookings.models import Booking
from customers.models import Customer

from .models import Departure, Guide, Service, Supplier, Tour, TourItinerary, Vehicle


def make_user(username, role=None, superuser=False):
    user = get_user_model().objects.create_user(username, is_superuser=superuser, is_staff=superuser)
    if role:
        user.groups.add(Group.objects.get_or_create(name=role)[0])
    return user


def tour_payload(code="NEW", days=2, rows=None, initial=0):
    if rows is None:
        rows = [{"day_number": n, "title": f"Ngày {n}", "content": f"Tham quan ngày {n}"} for n in range(1, days + 1)]
    data = {
        "code": code, "name": "Tour thử nghiệm", "days": days, "nights": days - 1,
        "destination": "Hạ Long", "base_price": "2450000", "description": "Mô tả thử nghiệm", "status": "ACTIVE",
        "itineraries-TOTAL_FORMS": len(rows), "itineraries-INITIAL_FORMS": initial,
        "itineraries-MIN_NUM_FORMS": 1, "itineraries-MAX_NUM_FORMS": 1000,
    }
    for index, row in enumerate(rows):
        for name, value in row.items():
            data[f"itineraries-{index}-{name}"] = value
    return data


class CatalogFixture(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_catalog", stdout=StringIO())
        cls.operator = make_user("operatorTest", "Operator")
        cls.sales = make_user("salesTest", "Sales")
        cls.admin = make_user("adminTest", "Admin")
        cls.superuser = make_user("superTest", superuser=True)
        cls.no_role = make_user("noRole")

    def setUp(self):
        self.client.force_login(self.operator)


class CatalogAccessTests(CatalogFixture):
    def test_anonymous_redirects_for_every_catalog(self):
        self.client.logout()
        for name in ("supplier", "service", "guide", "vehicle", "tour", "departure"):
            response = self.client.get(reverse(f"catalog:{name}_list"))
            self.assertEqual(response.status_code, 302)
            self.assertIn("/login/?next=", response.url)

    def test_operator_can_open_every_catalog_action(self):
        for name, model in [("supplier", Supplier), ("service", Service), ("guide", Guide), ("vehicle", Vehicle), ("tour", Tour), ("departure", Departure)]:
            for action in ("list", "detail", "create", "update", "delete"):
                args = [model.objects.first().pk] if action in ("detail", "update", "delete") else []
                with self.subTest(name=name, action=action):
                    self.assertEqual(self.client.get(reverse(f"catalog:{name}_{action}", args=args)).status_code, 200)

    def test_sales_cannot_access_private_catalogs_even_by_post(self):
        self.client.force_login(self.sales)
        for name, model in [("supplier", Supplier), ("service", Service), ("guide", Guide), ("vehicle", Vehicle)]:
            for action in ("list", "detail", "create", "update", "delete"):
                args = [model.objects.first().pk] if action in ("detail", "update", "delete") else []
                url = reverse(f"catalog:{name}_{action}", args=args)
                with self.subTest(name=name, action=action):
                    self.assertEqual(self.client.get(url).status_code, 403)
                    self.assertEqual(self.client.post(url, {}).status_code, 403)

    def test_sales_only_reads_tours_and_departures(self):
        self.client.force_login(self.sales)
        for name, model in [("tour", Tour), ("departure", Departure)]:
            self.assertEqual(self.client.get(reverse(f"catalog:{name}_list")).status_code, 200)
            detail = self.client.get(reverse(f"catalog:{name}_detail", args=[model.objects.first().pk]))
            self.assertEqual(detail.status_code, 200)
            self.assertFalse(detail.context["can_manage"])
            for action in ("create", "update", "delete"):
                args = [] if action == "create" else [model.objects.first().pk]
                url = reverse(f"catalog:{name}_{action}", args=args)
                self.assertEqual(self.client.get(url).status_code, 403)
                self.assertEqual(self.client.post(url, {}).status_code, 403)

    def test_admin_group_and_superuser_bypass_restrictions(self):
        for user in (self.admin, self.superuser):
            self.client.force_login(user)
            for url in ("/suppliers/", "/tours/create/", "/customers/", "/customers/create/"):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_no_role_gets_custom_forbidden_page(self):
        self.client.force_login(self.no_role)
        response = self.client.get("/tours/")
        self.assertContains(response, "Bạn chưa được cấp quyền", status_code=403)

    def test_create_requires_csrf(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.operator)
        self.assertEqual(client.post("/suppliers/create/", {"name": "NCC"}).status_code, 403)

    def test_nonexistent_object_is_404(self):
        self.assertEqual(self.client.get("/tours/999999/").status_code, 404)


class CatalogCrudTests(CatalogFixture):
    def test_create_update_confirm_and_delete_for_simple_catalogs(self):
        cases = [
            ("supplier", Supplier, {"name": "Nhà cung cấp mới", "supplier_type": "Lưu trú", "phone": "0901234567", "email": "new@example.com", "address": "Hà Nội"}, "name"),
            ("service", Service, {"name": "Dịch vụ mới", "service_type": "MEAL", "supplier": Supplier.objects.first().pk, "unit_price": "123000", "unit": "suất", "description": "Thực đơn"}, "name"),
            ("guide", Guide, {"full_name": "HDV mới", "phone": "0901234567", "languages": "Tiếng Việt", "status": "ACTIVE"}, "full_name"),
            ("vehicle", Vehicle, {"plate_number": "29B-999.99", "vehicle_type": "Xe 16 chỗ", "seats": "16", "driver_name": "Tài xế mới", "driver_phone": "0901234567", "status": "ACTIVE"}, "driver_name"),
            ("departure", Departure, {"tour": Tour.objects.first().pk, "start_date": "2027-01-01", "end_date": "2027-01-03", "max_seats": "20", "price": "1230000", "status": "OPEN"}, "price"),
        ]
        for name, model, data, update_field in cases:
            with self.subTest(model=name):
                before = set(model.objects.values_list("pk", flat=True))
                response = self.client.post(reverse(f"catalog:{name}_create"), data)
                self.assertEqual(response.status_code, 302)
                obj = model.objects.exclude(pk__in=before).get()
                self.assertRedirects(response, reverse(f"catalog:{name}_detail", args=[obj.pk]))
                updated = dict(data)
                updated[update_field] = "2340000" if update_field == "price" else "Đã sửa"
                response = self.client.post(reverse(f"catalog:{name}_update", args=[obj.pk]), updated)
                self.assertEqual(response.status_code, 302)
                obj.refresh_from_db()
                self.assertEqual(str(getattr(obj, update_field)), updated[update_field])
                delete_url = reverse(f"catalog:{name}_delete", args=[obj.pk])
                self.assertContains(self.client.get(delete_url), "Xác nhận xóa")
                self.assertTrue(model.objects.filter(pk=obj.pk).exists())
                response = self.client.post(delete_url, follow=True)
                self.assertFalse(model.objects.filter(pk=obj.pk).exists())
                self.assertContains(response, "thành công")

    def test_search_and_pagination_preserve_query(self):
        for index in range(13):
            Supplier.objects.create(name=f"A&B {index:02}", supplier_type="Khác", phone="0901234567")
        response = self.client.get("/suppliers/", {"q": "A&B"})
        self.assertEqual(len(response.context["object_list"]), 10)
        self.assertEqual(response.context["paginator"].count, 13)
        self.assertContains(response, "q=A%26B&amp;page=2")
        response = self.client.get("/suppliers/", {"q": "A&B", "page": 2})
        self.assertEqual(len(response.context["object_list"]), 3)

    def test_service_searches_supplier_name(self):
        response = self.client.get("/services/", {"q": "Mường Hoa"})
        self.assertEqual(response.context["paginator"].count, 1)

    def test_empty_search_results_render(self):
        for url in ("/suppliers/", "/services/", "/guides/", "/vehicles/", "/tours/", "/departures/"):
            self.assertContains(self.client.get(url, {"q": "noMatchXYZ"}), "Chưa có dữ liệu phù hợp.")

    def test_protected_supplier_and_tour_cannot_be_deleted(self):
        for name, obj in [("supplier", Service.objects.first().supplier), ("tour", Departure.objects.first().tour)]:
            response = self.client.post(reverse(f"catalog:{name}_delete", args=[obj.pk]))
            self.assertContains(response, "Không thể xóa vì bản ghi")
            self.assertTrue(type(obj).objects.filter(pk=obj.pk).exists())

    def test_duplicate_plate_and_negative_price_are_invalid(self):
        vehicle = Vehicle.objects.first()
        data = {"plate_number": vehicle.plate_number, "vehicle_type": "Xe", "seats": 16, "driver_name": "Tài xế", "driver_phone": "0901234567", "status": "ACTIVE"}
        response = self.client.post("/vehicles/create/", data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("plate_number", response.context["form"].errors)
        response = self.client.post("/services/create/", {"name": "Giá âm", "service_type": "MEAL", "supplier": Supplier.objects.first().pk, "unit_price": "-1", "unit": "suất"})
        self.assertIn("unit_price", response.context["form"].errors)

    def test_user_text_is_escaped(self):
        supplier = Supplier.objects.create(name="<script>alert(1)</script>", supplier_type="Khác", phone="0901234567")
        response = self.client.get(reverse("catalog:supplier_detail", args=[supplier.pk]))
        self.assertContains(response, "&lt;script&gt;alert(1)&lt;/script&gt;")
        self.assertNotContains(response, "<script>alert(1)</script>")


class TourFormsetTests(CatalogFixture):
    def test_create_tour_with_every_day_and_delete_unused_tour(self):
        response = self.client.post("/tours/create/", tour_payload())
        self.assertEqual(response.status_code, 302)
        tour = Tour.objects.get(code="NEW")
        self.assertEqual(list(tour.itineraries.values_list("day_number", flat=True)), [1, 2])
        detail = self.client.get(response.url)
        self.assertContains(detail, "Tham quan ngày 1")
        self.assertContains(detail, "Tour chưa có lịch khởi hành.")
        self.assertEqual(self.client.post(reverse("catalog:tour_delete", args=[tour.pk])).status_code, 302)
        self.assertFalse(TourItinerary.objects.filter(tour_id=tour.pk).exists())

    def test_missing_duplicate_or_out_of_range_day_does_not_create_tour(self):
        for numbers in ([1], [1, 1], [1, 3], [0, 2]):
            rows = [{"day_number": n, "title": "Ngày", "content": "Nội dung"} for n in numbers]
            response = self.client.post("/tours/create/", tour_payload(rows=rows))
            self.assertEqual(response.status_code, 200)
            self.assertFalse(Tour.objects.filter(code="NEW").exists())
            self.assertTrue(response.context["itinerary_formset"].errors or response.context["itinerary_formset"].non_form_errors())

    def test_invalid_parent_keeps_bound_formset(self):
        data = tour_payload()
        data["name"] = ""
        response = self.client.post("/tours/create/", data)
        self.assertIn("name", response.context["form"].errors)
        self.assertTrue(response.context["itinerary_formset"].is_bound)
        self.assertContains(response, "Tham quan ngày 1")

    def test_management_form_is_required(self):
        data = tour_payload()
        del data["itineraries-TOTAL_FORMS"]
        response = self.client.post("/tours/create/", data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Tour.objects.filter(code="NEW").exists())

    def test_duplicate_tour_code_is_invalid(self):
        response = self.client.post("/tours/create/", tour_payload(code=Tour.objects.first().code))
        self.assertIn("code", response.context["form"].errors)

    def test_update_can_swap_day_numbers(self):
        tour = Tour.objects.get(code="HNHL2N1D")
        items = list(tour.itineraries.all())
        rows = [{"id": item.pk, "day_number": 2 - index, "title": f"Nội dung cũ {index}", "content": "Đã cập nhật"} for index, item in enumerate(items)]
        response = self.client.post(reverse("catalog:tour_update", args=[tour.pk]), tour_payload(code=tour.code, rows=rows, initial=2))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(list(tour.itineraries.values_list("title", flat=True)), ["Nội dung cũ 1", "Nội dung cũ 0"])

    def test_delete_row_and_reduce_number_of_days(self):
        tour = Tour.objects.get(code="HNHL2N1D")
        items = list(tour.itineraries.all())
        rows = [{"id": items[0].pk, "day_number": 1, "title": "Còn lại", "content": "Nội dung"}, {"id": items[1].pk, "DELETE": "on"}]
        response = self.client.post(reverse("catalog:tour_update", args=[tour.pk]), tour_payload(code=tour.code, days=1, rows=rows, initial=2))
        self.assertEqual(response.status_code, 302)
        tour.refresh_from_db()
        self.assertEqual(tour.days, 1)
        self.assertEqual(tour.itineraries.count(), 1)

    def test_cannot_submit_itinerary_id_of_another_tour(self):
        other_item = TourItinerary.objects.exclude(tour__code="HNHL2N1D").first()
        tour = Tour.objects.get(code="HNHL2N1D")
        rows = [{"id": other_item.pk, "day_number": 1, "title": "Thử", "content": "Thử"}]
        response = self.client.post(reverse("catalog:tour_update", args=[tour.pk]), tour_payload(code=tour.code, days=1, rows=rows, initial=1))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(tour.itineraries.count(), 2)
        self.assertTrue(TourItinerary.objects.filter(pk=other_item.pk).exists())

    def test_database_failure_rolls_back_parent_and_children(self):
        tour = Tour.objects.get(code="HNHL2N1D")
        original_name = tour.name
        original_items = list(tour.itineraries.values_list("day_number", "title", "content"))
        rows = [{"id": item.pk, "day_number": item.day_number, "title": "Đã sửa", "content": "Mới"} for item in tour.itineraries.all()]
        with patch("catalog.views.TourItinerary.objects.bulk_create", side_effect=IntegrityError("Kiểm tra rollback")):
            with self.assertRaises(IntegrityError):
                self.client.post(reverse("catalog:tour_update", args=[tour.pk]), tour_payload(code=tour.code, rows=rows, initial=2))
        tour.refresh_from_db()
        self.assertEqual(tour.name, original_name)
        self.assertEqual(list(tour.itineraries.values_list("day_number", "title", "content")), original_items)


class DepartureTests(CatalogFixture):
    def make_booking(self, code="BK1", status="PENDING", adults=2, children=1):
        departure = Departure.objects.get(tour__code="HNHL2N1D", start_date=date(2026, 12, 5))
        return Booking.objects.create(code=code, customer=Customer.objects.first(), departure=departure, num_adults=adults, num_children=children, total_amount=Decimal("5000000"), status=status, created_by=self.operator)

    def test_combined_filters_are_inclusive_on_start_date(self):
        departure = Departure.objects.get(tour__code="HNHL2N1D", start_date=date(2026, 12, 5))
        departure.status = "FULL"
        departure.save(update_fields=["status"])
        response = self.client.get("/departures/", {"q": "HNHL", "status": "FULL", "start_date": "2026-12-05", "end_date": "2026-12-05"})
        self.assertEqual([obj.pk for obj in response.context["object_list"]], [departure.pk])

    def test_invalid_date_range_value_or_status_does_not_crash(self):
        for params in ({"start_date": "2026-12-20", "end_date": "2026-12-01"}, {"start_date": "not-a-date"}, {"status": "INVALID"}):
            response = self.client.get("/departures/", params)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.context["filter_form"].errors)
            self.assertEqual(response.context["paginator"].count, 0)

    def test_seat_totals_and_related_bookings_are_read_only(self):
        first = self.make_booking()
        self.make_booking("BK2", "CONFIRMED", 1, 0)
        self.make_booking("BK3", "COMPLETED", 1, 0)
        self.make_booking("BK4", "CANCELLED", 8, 2)
        response = self.client.get("/departures/")
        self.assertContains(response, "5/29")
        detail = self.client.get(reverse("catalog:departure_detail", args=[first.departure_id]))
        self.assertEqual(detail.context["booked_seats"], first.departure.booked_seats)
        self.assertContains(detail, "BK4")
        self.assertContains(detail, "chỉ đọc")
        self.assertEqual(Booking.objects.count(), 4)

    def test_empty_booking_list_renders(self):
        response = self.client.get(reverse("catalog:departure_detail", args=[Departure.objects.first().pk]))
        self.assertContains(response, "Chưa có booking nào.")

    def test_departure_list_has_bounded_query_count(self):
        self.make_booking()
        with CaptureQueriesContext(connection) as captured:
            response = self.client.get("/departures/")
        self.assertEqual(response.status_code, 200)
        self.assertLessEqual(len(captured), 10)

    def test_end_date_and_existing_booked_capacity_are_validated(self):
        booking = self.make_booking()
        departure = booking.departure
        data = {"tour": departure.tour_id, "start_date": "2026-12-05", "end_date": "2026-12-04", "max_seats": 2, "price": "2450000", "status": "OPEN"}
        response = self.client.post(reverse("catalog:departure_update", args=[departure.pk]), data)
        self.assertIn("end_date", response.context["form"].errors)
        self.assertIn("max_seats", response.context["form"].errors)
        departure.refresh_from_db()
        self.assertEqual(departure.max_seats, 29)

    def test_booked_departure_is_protected_from_deletion(self):
        booking = self.make_booking()
        response = self.client.post(reverse("catalog:departure_delete", args=[booking.departure_id]))
        self.assertContains(response, "Không thể xóa")
        self.assertTrue(Departure.objects.filter(pk=booking.departure_id).exists())


class SeedCatalogTests(TestCase):
    def assert_counts(self):
        for model, count in [(Supplier, 5), (Service, 10), (Guide, 4), (Vehicle, 4), (Tour, 4), (TourItinerary, 10), (Departure, 8), (Customer, 10)]:
            self.assertEqual(model.objects.count(), count)
            for item in model.objects.all():
                item.full_clean()

    def test_seed_from_empty_database_is_repeatable_and_keeps_edits(self):
        call_command("seed_catalog", stdout=StringIO())
        self.assert_counts()
        service = Service.objects.first()
        service.unit_price = Decimal("999999")
        service.save(update_fields=["unit_price"])
        call_command("seed_catalog", stdout=StringIO())
        self.assert_counts()
        service.refresh_from_db()
        self.assertEqual(service.unit_price, Decimal("999999"))
        self.assertEqual(get_user_model().objects.count(), 0)
        self.assertEqual(Booking.objects.count(), 0)

    def test_seed_extends_base_without_duplicates(self):
        call_command("seed_base", stdout=StringIO())
        call_command("seed_catalog", stdout=StringIO())
        call_command("seed_catalog", stdout=StringIO())
        self.assert_counts()
        self.assertEqual(get_user_model().objects.count(), 3)
```

## tourManager/catalog/urls.py

```python
from django.urls import path

from . import views

app_name = "catalog"
urlpatterns = [
    path("suppliers/", views.SupplierListView.as_view(), name="supplier_list"),
    path("suppliers/create/", views.SupplierCreateView.as_view(), name="supplier_create"),
    path("suppliers/<int:pk>/", views.SupplierDetailView.as_view(), name="supplier_detail"),
    path("suppliers/<int:pk>/edit/", views.SupplierUpdateView.as_view(), name="supplier_update"),
    path("suppliers/<int:pk>/delete/", views.SupplierDeleteView.as_view(), name="supplier_delete"),
    path("services/", views.ServiceListView.as_view(), name="service_list"),
    path("services/create/", views.ServiceCreateView.as_view(), name="service_create"),
    path("services/<int:pk>/", views.ServiceDetailView.as_view(), name="service_detail"),
    path("services/<int:pk>/edit/", views.ServiceUpdateView.as_view(), name="service_update"),
    path("services/<int:pk>/delete/", views.ServiceDeleteView.as_view(), name="service_delete"),
    path("guides/", views.GuideListView.as_view(), name="guide_list"),
    path("guides/create/", views.GuideCreateView.as_view(), name="guide_create"),
    path("guides/<int:pk>/", views.GuideDetailView.as_view(), name="guide_detail"),
    path("guides/<int:pk>/edit/", views.GuideUpdateView.as_view(), name="guide_update"),
    path("guides/<int:pk>/delete/", views.GuideDeleteView.as_view(), name="guide_delete"),
    path("vehicles/", views.VehicleListView.as_view(), name="vehicle_list"),
    path("vehicles/create/", views.VehicleCreateView.as_view(), name="vehicle_create"),
    path("vehicles/<int:pk>/", views.VehicleDetailView.as_view(), name="vehicle_detail"),
    path("vehicles/<int:pk>/edit/", views.VehicleUpdateView.as_view(), name="vehicle_update"),
    path("vehicles/<int:pk>/delete/", views.VehicleDeleteView.as_view(), name="vehicle_delete"),
    path("tours/", views.TourListView.as_view(), name="tour_list"),
    path("tours/create/", views.TourCreateView.as_view(), name="tour_create"),
    path("tours/<int:pk>/", views.TourDetailView.as_view(), name="tour_detail"),
    path("tours/<int:pk>/edit/", views.TourUpdateView.as_view(), name="tour_update"),
    path("tours/<int:pk>/delete/", views.TourDeleteView.as_view(), name="tour_delete"),
    path("departures/", views.DepartureListView.as_view(), name="departure_list"),
    path("departures/create/", views.DepartureCreateView.as_view(), name="departure_create"),
    path("departures/<int:pk>/", views.DepartureDetailView.as_view(), name="departure_detail"),
    path("departures/<int:pk>/edit/", views.DepartureUpdateView.as_view(), name="departure_update"),
    path("departures/<int:pk>/delete/", views.DepartureDeleteView.as_view(), name="departure_delete"),
]
```

## tourManager/catalog/views.py

```python
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
```

## tourManager/customers/forms.py

```python
from catalog.forms import BootstrapModelForm

from .models import Customer


class CustomerForm(BootstrapModelForm):
    class Meta:
        model = Customer
        fields = ("full_name", "phone", "email", "id_number", "address", "note")
```

## tourManager/customers/templates/customers/customer_confirm_delete.html

```html
{% extends "catalog/entity_confirm_delete.html" %}
```

## tourManager/customers/templates/customers/customer_detail.html

```html
{% extends "catalog/entity_detail.html" %}
{% block related_content %}
<section class="page-card p-3 p-md-4">
  <h2 class="h5 mb-3">Lịch sử booking — chỉ đọc</h2>
  {% include "catalog/booking_table.html" %}
</section>
{% endblock %}
```

## tourManager/customers/templates/customers/customer_form.html

```html
{% extends "catalog/entity_form.html" %}
```

## tourManager/customers/templates/customers/customer_list.html

```html
{% extends "catalog/entity_list.html" %}
```

## tourManager/customers/tests.py

```python
from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from bookings.models import Booking
from catalog.models import Departure, Tour

from .models import Customer


class CustomerTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.sales = User.objects.create_user("customerSales")
        cls.sales.groups.add(Group.objects.get_or_create(name="Sales")[0])
        cls.operator = User.objects.create_user("customerOperator")
        cls.operator.groups.add(Group.objects.get_or_create(name="Operator")[0])
        cls.customer = Customer.objects.create(full_name="Khách hàng mẫu", phone="0901234567")
        tour = Tour.objects.create(code="CUST", name="Tour thử", days=2, nights=1, destination="Hạ Long", base_price=Decimal("2450000"))
        cls.departure = Departure.objects.create(tour=tour, start_date=date(2026, 12, 5), end_date=date(2026, 12, 6), max_seats=29, price=Decimal("2450000"))

    def setUp(self):
        self.client.force_login(self.sales)

    def test_sales_creates_updates_and_deletes_customer(self):
        data = {"full_name": "Khách mới", "phone": "0900000999", "email": "new@example.com", "id_number": "", "address": "Hà Nội", "note": "Ăn chay"}
        response = self.client.post("/customers/create/", data)
        self.assertEqual(response.status_code, 302)
        customer = Customer.objects.get(phone="0900000999")
        data["full_name"] = "Khách đã sửa"
        response = self.client.post(reverse("customers:customer_update", args=[customer.pk]), data, follow=True)
        self.assertContains(response, "Khách đã sửa")
        self.assertContains(response, "thành công")
        delete_url = reverse("customers:customer_delete", args=[customer.pk])
        self.assertContains(self.client.get(delete_url), "Xác nhận xóa")
        self.assertTrue(Customer.objects.filter(pk=customer.pk).exists())
        self.assertEqual(self.client.post(delete_url).status_code, 302)
        self.assertFalse(Customer.objects.filter(pk=customer.pk).exists())

    def test_operator_is_forbidden_for_all_customer_actions(self):
        self.client.force_login(self.operator)
        for action in ("list", "create", "detail", "update", "delete"):
            args = [self.customer.pk] if action in ("detail", "update", "delete") else []
            url = reverse(f"customers:customer_{action}", args=args)
            self.assertEqual(self.client.get(url).status_code, 403)
            self.assertEqual(self.client.post(url, {}).status_code, 403)

    def test_empty_history_is_valid(self):
        response = self.client.get(reverse("customers:customer_detail", args=[self.customer.pk]))
        self.assertContains(response, "Chưa có booking nào.")

    def test_history_is_paginated_scoped_to_customer_and_read_only(self):
        for index in range(12):
            Booking.objects.create(code=f"C{index:02}", customer=self.customer, departure=self.departure, total_amount=Decimal("2450000"), created_by=self.sales)
        other = Customer.objects.create(full_name="Khách khác", phone="0900000100")
        Booking.objects.create(code="OTHER", customer=other, departure=self.departure, total_amount=Decimal("2450000"), created_by=self.sales)
        url = reverse("customers:customer_detail", args=[self.customer.pk])
        response = self.client.get(url)
        self.assertEqual(response.context["paginator"].count, 12)
        self.assertEqual(len(response.context["bookings"]), 10)
        self.assertNotContains(response, "OTHER")
        self.assertEqual(len(self.client.get(url, {"page": 2}).context["bookings"]), 2)
        self.assertEqual(Booking.objects.count(), 13)

    def test_customer_with_booking_cannot_be_deleted(self):
        Booking.objects.create(code="PROTECTED", customer=self.customer, departure=self.departure, total_amount=Decimal("2450000"), created_by=self.sales)
        response = self.client.post(reverse("customers:customer_delete", args=[self.customer.pk]))
        self.assertContains(response, "Không thể xóa")
        self.assertTrue(Customer.objects.filter(pk=self.customer.pk).exists())

    def test_search_phone_and_paginate(self):
        for index in range(12):
            Customer.objects.create(full_name=f"Khách {index:02}", phone=f"08888888{index:02}")
        response = self.client.get("/customers/", {"q": "08888888"})
        self.assertEqual(response.context["paginator"].count, 12)
        self.assertEqual(len(response.context["object_list"]), 10)
        self.assertContains(response, "q=08888888&amp;page=2")
        self.assertEqual(len(self.client.get("/customers/", {"q": "08888888", "page": 2}).context["object_list"]), 2)

    def test_invalid_email_does_not_save(self):
        response = self.client.post("/customers/create/", {"full_name": "Khách mới", "phone": "0900000000", "email": "invalid"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("email", response.context["form"].errors)
        self.assertFalse(Customer.objects.filter(full_name="Khách mới").exists())
```

## tourManager/customers/urls.py

```python
from django.urls import path

from . import views

app_name = "customers"
urlpatterns = [
    path("customers/", views.CustomerListView.as_view(), name="customer_list"),
    path("customers/create/", views.CustomerCreateView.as_view(), name="customer_create"),
    path("customers/<int:pk>/", views.CustomerDetailView.as_view(), name="customer_detail"),
    path("customers/<int:pk>/edit/", views.CustomerUpdateView.as_view(), name="customer_update"),
    path("customers/<int:pk>/delete/", views.CustomerDeleteView.as_view(), name="customer_delete"),
]
```

## tourManager/customers/views.py

```python
from catalog.crud import EntityCreateView, EntityDeleteView, EntityDetailView, EntityListView, EntityUpdateView, paginate_related

from .forms import CustomerForm
from .models import Customer


class CustomerConfig:
    model = Customer
    form_class = CustomerForm
    route_prefix = "customers:customer"
    allowed_roles = ("Sales",)
    manager_roles = ("Sales",)
    search_fields = ("full_name", "phone", "email", "id_number", "address")
    list_fields = ("full_name", "phone", "email", "address")


class CustomerListView(CustomerConfig, EntityListView):
    template_name = "customers/customer_list.html"


class CustomerDetailView(CustomerConfig, EntityDetailView):
    template_name = "customers/customer_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        bookings = self.object.bookings.select_related("customer", "departure__tour")
        context["bookings"] = paginate_related(context, bookings, self.request)
        return context


class CustomerCreateView(CustomerConfig, EntityCreateView):
    template_name = "customers/customer_form.html"


class CustomerUpdateView(CustomerConfig, EntityUpdateView):
    template_name = "customers/customer_form.html"


class CustomerDeleteView(CustomerConfig, EntityDeleteView):
    template_name = "customers/customer_confirm_delete.html"
```
