"""Danh mục dùng chung; schema được chốt ở giai đoạn 0."""
from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Sum


class Supplier(models.Model):
    name = models.CharField("Tên nhà cung cấp", max_length=200)
    supplier_type = models.CharField("Loại nhà cung cấp", max_length=100)
    phone = models.CharField("Số điện thoại", max_length=20)
    email = models.EmailField("Email", blank=True)
    address = models.CharField("Địa chỉ", max_length=255, blank=True)

    class Meta:
        ordering = ["name", "pk"]
        verbose_name = "Nhà cung cấp"
        verbose_name_plural = "Nhà cung cấp"

    def __str__(self):
        return self.name


class Service(models.Model):
    class ServiceType(models.TextChoices):
        LODGING = "LODGING", "Lưu trú"
        TRANSPORT = "TRANSPORT", "Vận chuyển"
        MEAL = "MEAL", "Ăn uống"
        TICKET = "TICKET", "Vé tham quan"
        GUIDE = "GUIDE", "Hướng dẫn"

    name = models.CharField("Tên dịch vụ", max_length=200)
    service_type = models.CharField("Loại dịch vụ", max_length=10, choices=ServiceType.choices)
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name="services", verbose_name="Nhà cung cấp")
    unit_price = models.DecimalField("Đơn giá (VNĐ)", max_digits=14, decimal_places=0, validators=[MinValueValidator(Decimal("0"))])
    unit = models.CharField("Đơn vị tính", max_length=50)
    description = models.TextField("Mô tả", blank=True)

    class Meta:
        ordering = ["name", "pk"]
        verbose_name = "Dịch vụ"
        verbose_name_plural = "Dịch vụ"

    def __str__(self):
        return self.name


class Guide(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Đang hoạt động"
        INACTIVE = "INACTIVE", "Ngừng hoạt động"

    full_name = models.CharField("Họ tên", max_length=150)
    phone = models.CharField("Số điện thoại", max_length=20)
    languages = models.CharField("Ngôn ngữ", max_length=200, default="Tiếng Việt")
    status = models.CharField("Trạng thái", max_length=8, choices=Status.choices, default=Status.ACTIVE)

    class Meta:
        ordering = ["full_name", "pk"]
        verbose_name = "Hướng dẫn viên"
        verbose_name_plural = "Hướng dẫn viên"

    def __str__(self):
        return self.full_name


class Vehicle(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Đang hoạt động"
        INACTIVE = "INACTIVE", "Ngừng hoạt động"

    plate_number = models.CharField("Biển số xe", max_length=20, unique=True)
    vehicle_type = models.CharField("Loại xe", max_length=100)
    seats = models.PositiveSmallIntegerField("Số chỗ", validators=[MinValueValidator(1)])
    driver_name = models.CharField("Tên tài xế", max_length=150)
    driver_phone = models.CharField("Điện thoại tài xế", max_length=20)
    status = models.CharField("Trạng thái", max_length=8, choices=Status.choices, default=Status.ACTIVE)

    class Meta:
        ordering = ["plate_number"]
        verbose_name = "Xe"
        verbose_name_plural = "Xe"

    def __str__(self):
        return f"{self.plate_number} - {self.vehicle_type}"


class Tour(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Đang kinh doanh"
        STOPPED = "STOPPED", "Ngừng kinh doanh"

    code = models.CharField("Mã tour", max_length=30, unique=True)
    name = models.CharField("Tên tour", max_length=200)
    days = models.PositiveSmallIntegerField("Số ngày", validators=[MinValueValidator(1)])
    nights = models.PositiveSmallIntegerField("Số đêm", default=0)
    destination = models.CharField("Điểm đến", max_length=200)
    base_price = models.DecimalField("Giá cơ bản (VNĐ)", max_digits=14, decimal_places=0, validators=[MinValueValidator(Decimal("0"))])
    description = models.TextField("Mô tả", blank=True)
    status = models.CharField("Trạng thái", max_length=7, choices=Status.choices, default=Status.ACTIVE)

    class Meta:
        ordering = ["code"]
        verbose_name = "Tour"
        verbose_name_plural = "Tour"

    def __str__(self):
        return f"{self.code} - {self.name}"


class TourItinerary(models.Model):
    tour = models.ForeignKey(Tour, on_delete=models.CASCADE, related_name="itineraries", verbose_name="Tour")
    day_number = models.PositiveSmallIntegerField("Ngày thứ", validators=[MinValueValidator(1)])
    title = models.CharField("Tiêu đề", max_length=200)
    content = models.TextField("Nội dung lịch trình")

    class Meta:
        ordering = ["tour", "day_number"]
        verbose_name = "Lịch trình tour"
        verbose_name_plural = "Lịch trình tour"
        constraints = [models.UniqueConstraint(fields=["tour", "day_number"], name="unique_tour_day")]

    def __str__(self):
        return f"{self.tour.code} - Ngày {self.day_number}: {self.title}"


class Departure(models.Model):
    class Status(models.TextChoices):
        OPEN = "OPEN", "Đang mở bán"
        FULL = "FULL", "Đã đủ chỗ"
        DEPARTED = "DEPARTED", "Đã khởi hành"
        FINISHED = "FINISHED", "Đã kết thúc"
        CANCELLED = "CANCELLED", "Đã hủy"

    tour = models.ForeignKey(Tour, on_delete=models.PROTECT, related_name="departures", verbose_name="Tour")
    start_date = models.DateField("Ngày khởi hành")
    end_date = models.DateField("Ngày kết thúc")
    max_seats = models.PositiveSmallIntegerField("Số chỗ tối đa", validators=[MinValueValidator(1)])
    price = models.DecimalField("Giá bán (VNĐ)", max_digits=14, decimal_places=0, validators=[MinValueValidator(Decimal("0"))])
    status = models.CharField("Trạng thái", max_length=9, choices=Status.choices, default=Status.OPEN)

    class Meta:
        ordering = ["-start_date", "pk"]
        verbose_name = "Lịch khởi hành"
        verbose_name_plural = "Lịch khởi hành"

    def __str__(self):
        return f"{self.tour.code} - {self.start_date:%d/%m/%Y}"

    @property
    def booked_seats(self):
        # Booking chờ xử lý cũng giữ chỗ; chỉ loại booking đã hủy.
        totals = self.bookings.exclude(status="CANCELLED").aggregate(adults=Sum("num_adults"), children=Sum("num_children"))
        return (totals["adults"] or 0) + (totals["children"] or 0)

    @property
    def available_seats(self):
        return self.max_seats - self.booked_seats
