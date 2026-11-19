from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Sum
from django.utils import timezone


class Booking(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Chờ xác nhận"
        CONFIRMED = "CONFIRMED", "Đã xác nhận"
        COMPLETED = "COMPLETED", "Đã hoàn thành"
        CANCELLED = "CANCELLED", "Đã hủy"

    code = models.CharField("Mã đặt tour", max_length=30, unique=True)
    customer = models.ForeignKey("customers.Customer", on_delete=models.PROTECT, related_name="bookings", verbose_name="Khách hàng")
    departure = models.ForeignKey("catalog.Departure", on_delete=models.PROTECT, related_name="bookings", verbose_name="Lịch khởi hành")
    num_adults = models.PositiveSmallIntegerField("Số người lớn", default=1, validators=[MinValueValidator(1)])
    num_children = models.PositiveSmallIntegerField("Số trẻ em", default=0)
    total_amount = models.DecimalField("Tổng tiền (VNĐ)", max_digits=14, decimal_places=0, validators=[MinValueValidator(Decimal("0"))])
    status = models.CharField("Trạng thái", max_length=9, choices=Status.choices, default=Status.PENDING)
    note = models.TextField("Ghi chú", blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_bookings", verbose_name="Người tạo")
    created_at = models.DateTimeField("Ngày tạo", auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "pk"]
        verbose_name = "Đặt tour"
        verbose_name_plural = "Đặt tour"

    def __str__(self):
        return f"{self.code} - {self.customer.full_name}"

    @property
    def paid_amount(self):
        return self.payments.aggregate(total=Sum("amount"))["total"] or Decimal("0")

    @property
    def remaining_amount(self):
        return self.total_amount - self.paid_amount


class Payment(models.Model):
    class PaymentType(models.TextChoices):
        DEPOSIT = "DEPOSIT", "Đặt cọc"
        INSTALLMENT = "INSTALLMENT", "Thanh toán từng phần"
        FULL = "FULL", "Thanh toán đủ"

    class Method(models.TextChoices):
        CASH = "CASH", "Tiền mặt"
        TRANSFER = "TRANSFER", "Chuyển khoản"

    booking = models.ForeignKey(Booking, on_delete=models.PROTECT, related_name="payments", verbose_name="Đặt tour")
    amount = models.DecimalField("Số tiền (VNĐ)", max_digits=14, decimal_places=0, validators=[MinValueValidator(Decimal("1"))])
    payment_type = models.CharField("Loại thanh toán", max_length=11, choices=PaymentType.choices)
    method = models.CharField("Phương thức", max_length=8, choices=Method.choices)
    paid_at = models.DateTimeField("Ngày thanh toán", default=timezone.now)
    note = models.TextField("Ghi chú", blank=True)
    received_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="received_payments", verbose_name="Người thu")

    class Meta:
        ordering = ["-paid_at", "pk"]
        verbose_name = "Thanh toán"
        verbose_name_plural = "Thanh toán"

    def __str__(self):
        return f"{self.booking.code} - {self.amount:,.0f} VNĐ"
