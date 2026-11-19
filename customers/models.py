from django.db import models


class Customer(models.Model):
    full_name = models.CharField("Họ tên", max_length=150)
    phone = models.CharField("Số điện thoại", max_length=20)
    email = models.EmailField("Email", blank=True)
    id_number = models.CharField("Số CCCD/hộ chiếu", max_length=30, blank=True)
    address = models.CharField("Địa chỉ", max_length=255, blank=True)
    note = models.TextField("Ghi chú", blank=True)

    class Meta:
        ordering = ["full_name", "pk"]
        verbose_name = "Khách hàng"
        verbose_name_plural = "Khách hàng"

    def __str__(self):
        return f"{self.full_name} - {self.phone}"
