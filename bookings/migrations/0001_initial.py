# Được tạo tự động bởi Django 5.2.19 on 2026-11-12 09:27

import django.core.validators
import django.db.models.deletion
import django.utils.timezone
from decimal import Decimal
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('catalog', '0001_initial'),
        ('customers', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Booking',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=30, unique=True, verbose_name='Mã đặt tour')),
                ('num_adults', models.PositiveSmallIntegerField(default=1, validators=[django.core.validators.MinValueValidator(1)], verbose_name='Số người lớn')),
                ('num_children', models.PositiveSmallIntegerField(default=0, verbose_name='Số trẻ em')),
                ('total_amount', models.DecimalField(decimal_places=0, max_digits=14, validators=[django.core.validators.MinValueValidator(Decimal('0'))], verbose_name='Tổng tiền (VNĐ)')),
                ('status', models.CharField(choices=[('PENDING', 'Chờ xác nhận'), ('CONFIRMED', 'Đã xác nhận'), ('COMPLETED', 'Đã hoàn thành'), ('CANCELLED', 'Đã hủy')], default='PENDING', max_length=9, verbose_name='Trạng thái')),
                ('note', models.TextField(blank=True, verbose_name='Ghi chú')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Ngày tạo')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='created_bookings', to=settings.AUTH_USER_MODEL, verbose_name='Người tạo')),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='bookings', to='customers.customer', verbose_name='Khách hàng')),
                ('departure', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='bookings', to='catalog.departure', verbose_name='Lịch khởi hành')),
            ],
            options={
                'verbose_name': 'Đặt tour',
                'verbose_name_plural': 'Đặt tour',
                'ordering': ['-created_at', 'pk'],
            },
        ),
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=0, max_digits=14, validators=[django.core.validators.MinValueValidator(Decimal('1'))], verbose_name='Số tiền (VNĐ)')),
                ('payment_type', models.CharField(choices=[('DEPOSIT', 'Đặt cọc'), ('INSTALLMENT', 'Thanh toán từng phần'), ('FULL', 'Thanh toán đủ')], max_length=11, verbose_name='Loại thanh toán')),
                ('method', models.CharField(choices=[('CASH', 'Tiền mặt'), ('TRANSFER', 'Chuyển khoản')], max_length=8, verbose_name='Phương thức')),
                ('paid_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Ngày thanh toán')),
                ('note', models.TextField(blank=True, verbose_name='Ghi chú')),
                ('booking', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='payments', to='bookings.booking', verbose_name='Đặt tour')),
                ('received_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='received_payments', to=settings.AUTH_USER_MODEL, verbose_name='Người thu')),
            ],
            options={
                'verbose_name': 'Thanh toán',
                'verbose_name_plural': 'Thanh toán',
                'ordering': ['-paid_at', 'pk'],
            },
        ),
    ]
