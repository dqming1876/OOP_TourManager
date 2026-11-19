import secrets
from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction

from catalog.models import Departure, Guide, Service, Supplier, Tour, TourItinerary, Vehicle
from customers.models import Customer


class Command(BaseCommand):
    help = "Tạo dữ liệu du lịch Việt Nam mẫu; chạy lại không sinh bản ghi trùng."

    @transaction.atomic
    def handle(self, *args, **options):
        call_command("setup_roles", stdout=self.stdout)
        User = get_user_model()
        for username, role, first_name in [
            ("admin", "Admin", "Quản trị viên"),
            ("sales", "Sales", "Nhân viên kinh doanh"),
            ("operator", "Operator", "Nhân viên điều hành"),
        ]:
            user, created = User.objects.get_or_create(username=username, defaults={
                "first_name": first_name,
                "is_staff": username == "admin",
                "is_superuser": username == "admin",
                "is_active": True,
            })
            if created:
                password = secrets.token_urlsafe(12)
                user.set_password(password)
                user.save(update_fields=["password"])
                user.groups.set([Group.objects.get(name=role)])
                self.stdout.write(self.style.SUCCESS(f"Đã tạo tài khoản mẫu {username}. Dùng chức năng đặt lại mật khẩu trước khi đăng nhập."))
            else:
                self.stdout.write(f"Tài khoản {username} đã tồn tại; giữ nguyên mật khẩu và quyền.")

        # Địa danh và tuyến đi có thật; tên đối tác, liên hệ và nhân sự là dữ liệu mô phỏng.
        hotel, _ = Supplier.objects.get_or_create(name="Khách sạn Hạ Long Xanh (mẫu)", defaults={
            "supplier_type": "Lưu trú", "phone": "0900000001",
            "email": "halong@example.com", "address": "Bãi Cháy, Quảng Ninh",
        })
        partner, _ = Supplier.objects.get_or_create(name="Dịch vụ du lịch Việt Bắc (mẫu)", defaults={
            "supplier_type": "Dịch vụ tổng hợp", "phone": "0900000002",
            "email": "vietbac@example.com", "address": "Hoàn Kiếm, Hà Nội",
        })
        for name, kind, supplier, price, unit, description in [
            ("Phòng đôi Bãi Cháy", Service.ServiceType.LODGING, hotel, "800000", "phòng/đêm", "Phòng đôi, tiêu chuẩn 2 khách."),
            ("Xe du lịch Hà Nội - Hạ Long", Service.ServiceType.TRANSPORT, partner, "3500000", "xe/ngày", "Xe 29 chỗ phục vụ đoàn."),
            ("Suất ăn đặc sản địa phương", Service.ServiceType.MEAL, partner, "180000", "suất", "Thực đơn theo đoàn, đặt trước."),
            ("Vé tham quan vịnh Hạ Long", Service.ServiceType.TICKET, partner, "310000", "khách", "Giá mẫu phục vụ đồ án, không phải báo giá thương mại."),
        ]:
            Service.objects.get_or_create(name=name, supplier=supplier, defaults={
                "service_type": kind, "unit_price": Decimal(price), "unit": unit, "description": description,
            })

        for full_name, phone, languages in [
            ("Nguyễn Minh Anh", "0900000011", "Tiếng Việt, Tiếng Anh"),
            ("Trần Hoàng Nam", "0900000012", "Tiếng Việt, Tiếng Trung"),
        ]:
            Guide.objects.get_or_create(full_name=full_name, phone=phone, defaults={"languages": languages})
        for plate, kind, seats, driver, phone in [
            ("29B-900.01", "Thaco Town 29 chỗ", 29, "Lê Văn Hùng", "0900000021"),
            ("29B-900.02", "Ford Transit 16 chỗ", 16, "Phạm Văn Hải", "0900000022"),
        ]:
            Vehicle.objects.get_or_create(plate_number=plate, defaults={
                "vehicle_type": kind, "seats": seats, "driver_name": driver, "driver_phone": phone,
            })

        halong, _ = Tour.objects.get_or_create(code="HNHL2N1D", defaults={
            "name": "Hà Nội - Hạ Long 2 ngày 1 đêm", "days": 2, "nights": 1,
            "destination": "Vịnh Hạ Long, Quảng Ninh", "base_price": Decimal("2450000"),
            "description": "Tham quan vịnh Hạ Long, hang Sửng Sốt, đảo Ti Tốp và nghỉ tại Bãi Cháy.",
        })
        sapa, _ = Tour.objects.get_or_create(code="HNSP3N2D", defaults={
            "name": "Hà Nội - Sa Pa 3 ngày 2 đêm", "days": 3, "nights": 2,
            "destination": "Sa Pa, Lào Cai", "base_price": Decimal("3650000"),
            "description": "Khám phá Sa Pa, bản Cát Cát và khu du lịch Fansipan.",
        })
        for tour, day, title, content in [
            (halong, 1, "Hà Nội - Hạ Long", "Đón khách tại Hà Nội, đi cao tốc đến Hạ Long. Ăn trưa, nhận phòng và tham quan Bãi Cháy."),
            (halong, 2, "Tham quan vịnh - Hà Nội", "Lên tàu tham quan vịnh, hang Sửng Sốt và đảo Ti Tốp. Ăn trưa, trở về Hà Nội."),
            (sapa, 1, "Hà Nội - Sa Pa", "Khởi hành theo cao tốc Nội Bài - Lào Cai. Nhận phòng và thăm nhà thờ đá Sa Pa."),
            (sapa, 2, "Fansipan - bản Cát Cát", "Buổi sáng tham quan khu du lịch Fansipan. Buổi chiều đi bản Cát Cát, tìm hiểu văn hóa địa phương."),
            (sapa, 3, "Sa Pa - Hà Nội", "Tự do tham quan thị trấn, mua đặc sản. Trả phòng và lên xe về Hà Nội."),
        ]:
            TourItinerary.objects.get_or_create(tour=tour, day_number=day, defaults={"title": title, "content": content})
        # Giữ ngày cố định để chạy lại vào ngày khác cũng không sinh thêm chuyến.
        for tour, start, end, seats, price in [
            (halong, date(2026, 12, 5), date(2026, 12, 6), 29, "2450000"),
            (halong, date(2026, 12, 12), date(2026, 12, 13), 29, "2550000"),
            (sapa, date(2026, 12, 19), date(2026, 12, 21), 16, "3650000"),
        ]:
            Departure.objects.get_or_create(tour=tour, start_date=start, defaults={
                "end_date": end, "max_seats": seats, "price": Decimal(price),
            })
        for name, phone, email, address in [
            ("Nguyễn Thu Hà", "0900000031", "thuha@example.com", "Cầu Giấy, Hà Nội"),
            ("Trần Đức Long", "0900000032", "duclong@example.com", "Lê Chân, Hải Phòng"),
            ("Lê Ngọc Mai", "0900000033", "ngocmai@example.com", "Hải Châu, Đà Nẵng"),
        ]:
            Customer.objects.get_or_create(full_name=name, phone=phone, defaults={
                "email": email, "address": address, "note": "Khách hàng mô phỏng phục vụ đồ án.",
            })
        self.stdout.write(self.style.SUCCESS("Đã tạo dữ liệu nền. Không tạo booking, thanh toán, phân công hoặc chi phí."))
