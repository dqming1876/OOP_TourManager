# Được tạo tự động bởi Django 5.2.19 on 2026-11-12 09:27

import django.core.validators
import django.db.models.deletion
from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Guide',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('full_name', models.CharField(max_length=150, verbose_name='Họ tên')),
                ('phone', models.CharField(max_length=20, verbose_name='Số điện thoại')),
                ('languages', models.CharField(default='Tiếng Việt', max_length=200, verbose_name='Ngôn ngữ')),
                ('status', models.CharField(choices=[('ACTIVE', 'Đang hoạt động'), ('INACTIVE', 'Ngừng hoạt động')], default='ACTIVE', max_length=8, verbose_name='Trạng thái')),
            ],
            options={
                'verbose_name': 'Hướng dẫn viên',
                'verbose_name_plural': 'Hướng dẫn viên',
                'ordering': ['full_name', 'pk'],
            },
        ),
        migrations.CreateModel(
            name='Supplier',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='Tên nhà cung cấp')),
                ('supplier_type', models.CharField(max_length=100, verbose_name='Loại nhà cung cấp')),
                ('phone', models.CharField(max_length=20, verbose_name='Số điện thoại')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='Email')),
                ('address', models.CharField(blank=True, max_length=255, verbose_name='Địa chỉ')),
            ],
            options={
                'verbose_name': 'Nhà cung cấp',
                'verbose_name_plural': 'Nhà cung cấp',
                'ordering': ['name', 'pk'],
            },
        ),
        migrations.CreateModel(
            name='Tour',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=30, unique=True, verbose_name='Mã tour')),
                ('name', models.CharField(max_length=200, verbose_name='Tên tour')),
                ('days', models.PositiveSmallIntegerField(validators=[django.core.validators.MinValueValidator(1)], verbose_name='Số ngày')),
                ('nights', models.PositiveSmallIntegerField(default=0, verbose_name='Số đêm')),
                ('destination', models.CharField(max_length=200, verbose_name='Điểm đến')),
                ('base_price', models.DecimalField(decimal_places=0, max_digits=14, validators=[django.core.validators.MinValueValidator(Decimal('0'))], verbose_name='Giá cơ bản (VNĐ)')),
                ('description', models.TextField(blank=True, verbose_name='Mô tả')),
                ('status', models.CharField(choices=[('ACTIVE', 'Đang kinh doanh'), ('STOPPED', 'Ngừng kinh doanh')], default='ACTIVE', max_length=7, verbose_name='Trạng thái')),
            ],
            options={
                'verbose_name': 'Tour',
                'verbose_name_plural': 'Tour',
                'ordering': ['code'],
            },
        ),
        migrations.CreateModel(
            name='Vehicle',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('plate_number', models.CharField(max_length=20, unique=True, verbose_name='Biển số xe')),
                ('vehicle_type', models.CharField(max_length=100, verbose_name='Loại xe')),
                ('seats', models.PositiveSmallIntegerField(validators=[django.core.validators.MinValueValidator(1)], verbose_name='Số chỗ')),
                ('driver_name', models.CharField(max_length=150, verbose_name='Tên tài xế')),
                ('driver_phone', models.CharField(max_length=20, verbose_name='Điện thoại tài xế')),
                ('status', models.CharField(choices=[('ACTIVE', 'Đang hoạt động'), ('INACTIVE', 'Ngừng hoạt động')], default='ACTIVE', max_length=8, verbose_name='Trạng thái')),
            ],
            options={
                'verbose_name': 'Xe',
                'verbose_name_plural': 'Xe',
                'ordering': ['plate_number'],
            },
        ),
        migrations.CreateModel(
            name='Service',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='Tên dịch vụ')),
                ('service_type', models.CharField(choices=[('LODGING', 'Lưu trú'), ('TRANSPORT', 'Vận chuyển'), ('MEAL', 'Ăn uống'), ('TICKET', 'Vé tham quan'), ('GUIDE', 'Hướng dẫn')], max_length=10, verbose_name='Loại dịch vụ')),
                ('unit_price', models.DecimalField(decimal_places=0, max_digits=14, validators=[django.core.validators.MinValueValidator(Decimal('0'))], verbose_name='Đơn giá (VNĐ)')),
                ('unit', models.CharField(max_length=50, verbose_name='Đơn vị tính')),
                ('description', models.TextField(blank=True, verbose_name='Mô tả')),
                ('supplier', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='services', to='catalog.supplier', verbose_name='Nhà cung cấp')),
            ],
            options={
                'verbose_name': 'Dịch vụ',
                'verbose_name_plural': 'Dịch vụ',
                'ordering': ['name', 'pk'],
            },
        ),
        migrations.CreateModel(
            name='Departure',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_date', models.DateField(verbose_name='Ngày khởi hành')),
                ('end_date', models.DateField(verbose_name='Ngày kết thúc')),
                ('max_seats', models.PositiveSmallIntegerField(validators=[django.core.validators.MinValueValidator(1)], verbose_name='Số chỗ tối đa')),
                ('price', models.DecimalField(decimal_places=0, max_digits=14, validators=[django.core.validators.MinValueValidator(Decimal('0'))], verbose_name='Giá bán (VNĐ)')),
                ('status', models.CharField(choices=[('OPEN', 'Đang mở bán'), ('FULL', 'Đã đủ chỗ'), ('DEPARTED', 'Đã khởi hành'), ('FINISHED', 'Đã kết thúc'), ('CANCELLED', 'Đã hủy')], default='OPEN', max_length=9, verbose_name='Trạng thái')),
                ('tour', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='departures', to='catalog.tour', verbose_name='Tour')),
            ],
            options={
                'verbose_name': 'Lịch khởi hành',
                'verbose_name_plural': 'Lịch khởi hành',
                'ordering': ['-start_date', 'pk'],
            },
        ),
        migrations.CreateModel(
            name='TourItinerary',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('day_number', models.PositiveSmallIntegerField(validators=[django.core.validators.MinValueValidator(1)], verbose_name='Ngày thứ')),
                ('title', models.CharField(max_length=200, verbose_name='Tiêu đề')),
                ('content', models.TextField(verbose_name='Nội dung lịch trình')),
                ('tour', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='itineraries', to='catalog.tour', verbose_name='Tour')),
            ],
            options={
                'verbose_name': 'Lịch trình tour',
                'verbose_name_plural': 'Lịch trình tour',
                'ordering': ['tour', 'day_number'],
                'constraints': [models.UniqueConstraint(fields=('tour', 'day_number'), name='unique_tour_day')],
            },
        ),
    ]
