# Được tạo tự động bởi Django 5.2.19 on 2026-11-12 09:27

import django.core.validators
import django.db.models.deletion
import django.utils.timezone
from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('catalog', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='TourExpense',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.CharField(max_length=255, verbose_name='Nội dung chi')),
                ('amount', models.DecimalField(decimal_places=0, max_digits=14, validators=[django.core.validators.MinValueValidator(Decimal('0'))], verbose_name='Số tiền (VNĐ)')),
                ('expense_date', models.DateField(default=django.utils.timezone.localdate, verbose_name='Ngày chi')),
                ('departure', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='expenses', to='catalog.departure', verbose_name='Lịch khởi hành')),
                ('service', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='expenses', to='catalog.service', verbose_name='Dịch vụ')),
            ],
            options={
                'verbose_name': 'Chi phí tour',
                'verbose_name_plural': 'Chi phí tour',
                'ordering': ['-expense_date', 'pk'],
            },
        ),
        migrations.CreateModel(
            name='GuideAssignment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('note', models.TextField(blank=True, verbose_name='Ghi chú')),
                ('departure', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='guide_assignments', to='catalog.departure', verbose_name='Lịch khởi hành')),
                ('guide', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='assignments', to='catalog.guide', verbose_name='Hướng dẫn viên')),
            ],
            options={
                'verbose_name': 'Phân công hướng dẫn viên',
                'verbose_name_plural': 'Phân công hướng dẫn viên',
                'ordering': ['-departure__start_date', 'pk'],
                'constraints': [models.UniqueConstraint(fields=('departure', 'guide'), name='unique_departure_guide')],
            },
        ),
        migrations.CreateModel(
            name='VehicleAssignment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('note', models.TextField(blank=True, verbose_name='Ghi chú')),
                ('departure', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='vehicle_assignments', to='catalog.departure', verbose_name='Lịch khởi hành')),
                ('vehicle', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='assignments', to='catalog.vehicle', verbose_name='Xe')),
            ],
            options={
                'verbose_name': 'Phân công xe',
                'verbose_name_plural': 'Phân công xe',
                'ordering': ['-departure__start_date', 'pk'],
                'constraints': [models.UniqueConstraint(fields=('departure', 'vehicle'), name='unique_departure_vehicle')],
            },
        ),
    ]
