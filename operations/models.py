from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


class GuideAssignment(models.Model):
    departure = models.ForeignKey("catalog.Departure", on_delete=models.CASCADE, related_name="guide_assignments", verbose_name="Lịch khởi hành")
    guide = models.ForeignKey("catalog.Guide", on_delete=models.PROTECT, related_name="assignments", verbose_name="Hướng dẫn viên")
    note = models.TextField("Ghi chú", blank=True)

    class Meta:
        ordering = ["-departure__start_date", "pk"]
        verbose_name = "Phân công hướng dẫn viên"
        verbose_name_plural = "Phân công hướng dẫn viên"
        constraints = [models.UniqueConstraint(fields=["departure", "guide"], name="unique_departure_guide")]

    def __str__(self):
        return f"{self.departure} - {self.guide.full_name}"


class VehicleAssignment(models.Model):
    departure = models.ForeignKey("catalog.Departure", on_delete=models.CASCADE, related_name="vehicle_assignments", verbose_name="Lịch khởi hành")
    vehicle = models.ForeignKey("catalog.Vehicle", on_delete=models.PROTECT, related_name="assignments", verbose_name="Xe")
    note = models.TextField("Ghi chú", blank=True)

    class Meta:
        ordering = ["-departure__start_date", "pk"]
        verbose_name = "Phân công xe"
        verbose_name_plural = "Phân công xe"
        constraints = [models.UniqueConstraint(fields=["departure", "vehicle"], name="unique_departure_vehicle")]

    def __str__(self):
        return f"{self.departure} - {self.vehicle.plate_number}"


class TourExpense(models.Model):
    departure = models.ForeignKey("catalog.Departure", on_delete=models.PROTECT, related_name="expenses", verbose_name="Lịch khởi hành")
    service = models.ForeignKey("catalog.Service", on_delete=models.SET_NULL, null=True, blank=True, related_name="expenses", verbose_name="Dịch vụ")
    description = models.CharField("Nội dung chi", max_length=255)
    amount = models.DecimalField("Số tiền (VNĐ)", max_digits=14, decimal_places=0, validators=[MinValueValidator(Decimal("0"))])
    expense_date = models.DateField("Ngày chi", default=timezone.localdate)

    class Meta:
        ordering = ["-expense_date", "pk"]
        verbose_name = "Chi phí tour"
        verbose_name_plural = "Chi phí tour"

    def __str__(self):
        return f"{self.departure} - {self.description}"
