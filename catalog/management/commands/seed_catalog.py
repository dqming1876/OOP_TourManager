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
