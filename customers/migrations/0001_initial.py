# Được tạo tự động bởi Django 5.2.19 on 2026-11-12 09:27

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Customer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('full_name', models.CharField(max_length=150, verbose_name='Họ tên')),
                ('phone', models.CharField(max_length=20, verbose_name='Số điện thoại')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='Email')),
                ('id_number', models.CharField(blank=True, max_length=30, verbose_name='Số CCCD/hộ chiếu')),
                ('address', models.CharField(blank=True, max_length=255, verbose_name='Địa chỉ')),
                ('note', models.TextField(blank=True, verbose_name='Ghi chú')),
            ],
            options={
                'verbose_name': 'Khách hàng',
                'verbose_name_plural': 'Khách hàng',
                'ordering': ['full_name', 'pk'],
            },
        ),
    ]
