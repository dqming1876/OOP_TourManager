# Schema cuối cùng của giai đoạn 0

Mọi model dùng khóa chính `id` kiểu BigAutoField do Django tự tạo. Tiền VNĐ có `max_digits=14`, `decimal_places=0`.

Supplier.supplier_type và Vehicle.vehicle_type là văn bản tự do; Vehicle.status chọn ACTIVE/INACTIVE. Chuỗi tùy chọn dùng blank=True, không dùng null.

## catalog.Supplier

Nhãn: Nhà cung cấp. Sắp xếp: `['name', 'pk']`.

| Field | Kiểu | Cấu hình |
|---|---|---|
| `id` | BigAutoField | Khóa chính tự tăng, null=False, blank=True |
| `name` | CharField | max_length=200, null=False, blank=False |
| `supplier_type` | CharField | max_length=100, null=False, blank=False |
| `phone` | CharField | max_length=20, null=False, blank=False |
| `email` | CharField | max_length=254, null=False, blank=True |
| `address` | CharField | max_length=255, null=False, blank=True |

## catalog.Service

Nhãn: Dịch vụ. Sắp xếp: `['name', 'pk']`.

| Field | Kiểu | Cấu hình |
|---|---|---|
| `id` | BigAutoField | Khóa chính tự tăng, null=False, blank=True |
| `name` | CharField | max_length=200, null=False, blank=False |
| `service_type` | CharField | max_length=10, null=False, blank=False, LODGING: Lưu trú; TRANSPORT: Vận chuyển; MEAL: Ăn uống; TICKET: Vé tham quan; GUIDE: Hướng dẫn |
| `supplier` | ForeignKey | FK catalog.Supplier, on_delete=PROTECT, related_name=services, null=False, blank=False |
| `unit_price` | DecimalField | max_digits=14, decimal_places=0, null=False, blank=False |
| `unit` | CharField | max_length=50, null=False, blank=False |
| `description` | TextField | null=False, blank=True |

## catalog.Guide

Nhãn: Hướng dẫn viên. Sắp xếp: `['full_name', 'pk']`.

| Field | Kiểu | Cấu hình |
|---|---|---|
| `id` | BigAutoField | Khóa chính tự tăng, null=False, blank=True |
| `full_name` | CharField | max_length=150, null=False, blank=False |
| `phone` | CharField | max_length=20, null=False, blank=False |
| `languages` | CharField | max_length=200, null=False, blank=False, default=Tiếng Việt |
| `status` | CharField | max_length=8, null=False, blank=False, ACTIVE: Đang hoạt động; INACTIVE: Ngừng hoạt động, default=ACTIVE |

## catalog.Vehicle

Nhãn: Xe. Sắp xếp: `['plate_number']`.

| Field | Kiểu | Cấu hình |
|---|---|---|
| `id` | BigAutoField | Khóa chính tự tăng, null=False, blank=True |
| `plate_number` | CharField | max_length=20, unique=True, null=False, blank=False |
| `vehicle_type` | CharField | max_length=100, null=False, blank=False |
| `seats` | PositiveSmallIntegerField | null=False, blank=False |
| `driver_name` | CharField | max_length=150, null=False, blank=False |
| `driver_phone` | CharField | max_length=20, null=False, blank=False |
| `status` | CharField | max_length=8, null=False, blank=False, ACTIVE: Đang hoạt động; INACTIVE: Ngừng hoạt động, default=ACTIVE |

## catalog.Tour

Nhãn: Tour. Sắp xếp: `['code']`.

| Field | Kiểu | Cấu hình |
|---|---|---|
| `id` | BigAutoField | Khóa chính tự tăng, null=False, blank=True |
| `code` | CharField | max_length=30, unique=True, null=False, blank=False |
| `name` | CharField | max_length=200, null=False, blank=False |
| `days` | PositiveSmallIntegerField | null=False, blank=False |
| `nights` | PositiveSmallIntegerField | null=False, blank=False, default=0 |
| `destination` | CharField | max_length=200, null=False, blank=False |
| `base_price` | DecimalField | max_digits=14, decimal_places=0, null=False, blank=False |
| `description` | TextField | null=False, blank=True |
| `status` | CharField | max_length=7, null=False, blank=False, ACTIVE: Đang kinh doanh; STOPPED: Ngừng kinh doanh, default=ACTIVE |

## catalog.TourItinerary

Nhãn: Lịch trình tour. Sắp xếp: `['tour', 'day_number']`.

| Field | Kiểu | Cấu hình |
|---|---|---|
| `id` | BigAutoField | Khóa chính tự tăng, null=False, blank=True |
| `tour` | ForeignKey | FK catalog.Tour, on_delete=CASCADE, related_name=itineraries, null=False, blank=False |
| `day_number` | PositiveSmallIntegerField | null=False, blank=False |
| `title` | CharField | max_length=200, null=False, blank=False |
| `content` | TextField | null=False, blank=False |

Ràng buộc `unique_tour_day`: duy nhất trên `tour, day_number`.

## catalog.Departure

Nhãn: Lịch khởi hành. Sắp xếp: `['-start_date', 'pk']`.

| Field | Kiểu | Cấu hình |
|---|---|---|
| `id` | BigAutoField | Khóa chính tự tăng, null=False, blank=True |
| `tour` | ForeignKey | FK catalog.Tour, on_delete=PROTECT, related_name=departures, null=False, blank=False |
| `start_date` | DateField | null=False, blank=False |
| `end_date` | DateField | null=False, blank=False |
| `max_seats` | PositiveSmallIntegerField | null=False, blank=False |
| `price` | DecimalField | max_digits=14, decimal_places=0, null=False, blank=False |
| `status` | CharField | max_length=9, null=False, blank=False, OPEN: Đang mở bán; FULL: Đã đủ chỗ; DEPARTED: Đã khởi hành; FINISHED: Đã kết thúc; CANCELLED: Đã hủy, default=OPEN |

## customers.Customer

Nhãn: Khách hàng. Sắp xếp: `['full_name', 'pk']`.

| Field | Kiểu | Cấu hình |
|---|---|---|
| `id` | BigAutoField | Khóa chính tự tăng, null=False, blank=True |
| `full_name` | CharField | max_length=150, null=False, blank=False |
| `phone` | CharField | max_length=20, null=False, blank=False |
| `email` | CharField | max_length=254, null=False, blank=True |
| `id_number` | CharField | max_length=30, null=False, blank=True |
| `address` | CharField | max_length=255, null=False, blank=True |
| `note` | TextField | null=False, blank=True |

## bookings.Booking

Nhãn: Đặt tour. Sắp xếp: `['-created_at', 'pk']`.

| Field | Kiểu | Cấu hình |
|---|---|---|
| `id` | BigAutoField | Khóa chính tự tăng, null=False, blank=True |
| `code` | CharField | max_length=30, unique=True, null=False, blank=False |
| `customer` | ForeignKey | FK customers.Customer, on_delete=PROTECT, related_name=bookings, null=False, blank=False |
| `departure` | ForeignKey | FK catalog.Departure, on_delete=PROTECT, related_name=bookings, null=False, blank=False |
| `num_adults` | PositiveSmallIntegerField | null=False, blank=False, default=1 |
| `num_children` | PositiveSmallIntegerField | null=False, blank=False, default=0 |
| `total_amount` | DecimalField | max_digits=14, decimal_places=0, null=False, blank=False |
| `status` | CharField | max_length=9, null=False, blank=False, PENDING: Chờ xác nhận; CONFIRMED: Đã xác nhận; COMPLETED: Đã hoàn thành; CANCELLED: Đã hủy, default=PENDING |
| `note` | TextField | null=False, blank=True |
| `created_by` | ForeignKey | FK auth.User, on_delete=PROTECT, related_name=created_bookings, null=False, blank=False |
| `created_at` | DateTimeField | null=False, blank=True, auto_now_add=True |

## bookings.Payment

Nhãn: Thanh toán. Sắp xếp: `['-paid_at', 'pk']`.

| Field | Kiểu | Cấu hình |
|---|---|---|
| `id` | BigAutoField | Khóa chính tự tăng, null=False, blank=True |
| `booking` | ForeignKey | FK bookings.Booking, on_delete=PROTECT, related_name=payments, null=False, blank=False |
| `amount` | DecimalField | max_digits=14, decimal_places=0, null=False, blank=False |
| `payment_type` | CharField | max_length=11, null=False, blank=False, DEPOSIT: Đặt cọc; INSTALLMENT: Thanh toán từng phần; FULL: Thanh toán đủ |
| `method` | CharField | max_length=8, null=False, blank=False, CASH: Tiền mặt; TRANSFER: Chuyển khoản |
| `paid_at` | DateTimeField | null=False, blank=False, default=now |
| `note` | TextField | null=False, blank=True |
| `received_by` | ForeignKey | FK auth.User, on_delete=PROTECT, related_name=received_payments, null=False, blank=False |

## operations.GuideAssignment

Nhãn: Phân công hướng dẫn viên. Sắp xếp: `['-departure__start_date', 'pk']`.

| Field | Kiểu | Cấu hình |
|---|---|---|
| `id` | BigAutoField | Khóa chính tự tăng, null=False, blank=True |
| `departure` | ForeignKey | FK catalog.Departure, on_delete=CASCADE, related_name=guide_assignments, null=False, blank=False |
| `guide` | ForeignKey | FK catalog.Guide, on_delete=PROTECT, related_name=assignments, null=False, blank=False |
| `note` | TextField | null=False, blank=True |

Ràng buộc `unique_departure_guide`: duy nhất trên `departure, guide`.

## operations.VehicleAssignment

Nhãn: Phân công xe. Sắp xếp: `['-departure__start_date', 'pk']`.

| Field | Kiểu | Cấu hình |
|---|---|---|
| `id` | BigAutoField | Khóa chính tự tăng, null=False, blank=True |
| `departure` | ForeignKey | FK catalog.Departure, on_delete=CASCADE, related_name=vehicle_assignments, null=False, blank=False |
| `vehicle` | ForeignKey | FK catalog.Vehicle, on_delete=PROTECT, related_name=assignments, null=False, blank=False |
| `note` | TextField | null=False, blank=True |

Ràng buộc `unique_departure_vehicle`: duy nhất trên `departure, vehicle`.

## operations.TourExpense

Nhãn: Chi phí tour. Sắp xếp: `['-expense_date', 'pk']`.

| Field | Kiểu | Cấu hình |
|---|---|---|
| `id` | BigAutoField | Khóa chính tự tăng, null=False, blank=True |
| `departure` | ForeignKey | FK catalog.Departure, on_delete=PROTECT, related_name=expenses, null=False, blank=False |
| `service` | ForeignKey | FK catalog.Service, on_delete=SET_NULL, related_name=expenses, null=True, blank=True |
| `description` | CharField | max_length=255, null=False, blank=False |
| `amount` | DecimalField | max_digits=14, decimal_places=0, null=False, blank=False |
| `expense_date` | DateField | null=False, blank=False, default=localdate |

## Lưu ý quan hệ

- PROTECT bảo vệ danh mục và dữ liệu tài chính đang được tham chiếu.
- Xóa Tour chưa có Departure sẽ xóa lịch trình con (CASCADE).
- Phân công HDV/xe là bảng liên kết; xóa Departure sẽ xóa phân công con nếu không bị booking/chi phí bảo vệ.
- Xóa Service đặt TourExpense.service thành NULL, vẫn giữ nội dung và số tiền đã ghi.
- Một tour không có hai lịch trình cùng day_number; một chuyến không có hai bản phân công cùng HDV/xe.
- Không bổ sung model cho reports hoặc accounts. User/Group/Permission do Django cung cấp.
