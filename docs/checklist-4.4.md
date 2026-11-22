# Minh chứng 4.4 — Bất biến miền, kế thừa và LSP

| Bất biến | Bảo vệ trong lớp | Thử phá |
| --- | --- | --- |
| Lịch trình gửi lên đủ số ngày, không chèn ngẫu nhiên một điểm ghé sau khi tạo | Cả `__post_init__` và `Tour.request` kiểm số dòng, kiểu `MappingProxyType` và thứ tự `TourStop`. `stops` là `tuple` chỉ đọc; `TourStop` và `Destination` tự kiểm tra dữ liệu trong `__post_init__` và đóng băng bằng `@dataclass(frozen=True)`. | Tạo tour 2 ngày với một hoạt động hoặc gọi trực tiếp `TourStop(0, "Đi", place)` / `Tour("t", MappingProxyType({}), ())` trả lỗi 400; sửa `tour.details["days"]` ném `TypeError`; sửa thuộc tính trực tiếp ném `FrozenInstanceError`. |
| Chỗ đã giữ thuộc `[0, capacity]` | `__post_init__` của `Departure` kiểm giới hạn trước khi đóng băng. Trạng thái DB dùng CHECK và câu SQL kiểm lại lúc ghi. | `Departure("t", "2028-02-29", 3, 4)` trả lỗi 400. |
| Giá chốt của đơn ổn định, chỉ đơn xác nhận mới có thể đã thu | `__post_init__` của `Booking` kiểm cặp `status`/`paid`. Bản chụp đóng băng, `total` tính theo `people * unit_price`. Đơn mới yêu cầu giá khớp chính sách tại câu INSERT. | Sửa `booking.unit_price` trực tiếp ném `FrozenInstanceError`; tạo `pending` hoặc `cancelled` với `paid=True` trả lỗi 400. |
| Bút toán có loại thu hoặc hoàn và số tiền nguyên dương | `PaymentEvent.__post_init__` kiểm ngày, `PaymentKind` và số tiền nguyên dương. Property `signed_amount` gắn dấu theo loại. | `PaymentEvent(day, "refund", 0)` bị từ chối với lỗi 400. |

Mảng không thể thêm/xóa phần tử (`tuple`) và bản ghi chi tiết chỉ đọc (`MappingProxyType`); cập nhật qua yêu cầu tạo đối tượng hợp lệ mới. Điểm vào BLL và ràng buộc DB tiếp tục kiểm tra khi dữ liệu bị truy cập đồng thời. [Domain](../backend/domain.py) · [Kiểm thử](../tests/test_architecture.py)

## Kế thừa, dynamic binding và LSP

`CustomerAccount` và `AdministratorAccount` đều kế thừa `Account`. Hợp đồng `booking_scope() -> str | None` trả ID khi giới hạn theo chủ đơn và `None` khi đọc toàn bộ. Hai lớp con cùng cung cấp `public()`, `manages_catalog`, `cancellation_owner()`; khách mở rộng `public()` với dữ liệu hồ sơ công khai. `AccessPolicy.booking_scope()` gọi phương thức trên `actor` lấy từ phiên; lớp cụ thể quyết định cách trả scope tại runtime. Bên gọi `BookingService.bookings` chuyển trực tiếp giá trị đúng hợp đồng xuống `BookingPort.list_bookings`, không `isinstance` hay ép kiểu.

Đổi instance khách sang admin thay đổi phạm vi theo vai trò vẫn giữ kiểu trả về và các tiền/hậu điều kiện của API. Bài test `test_immutability_and_polymorphic_scope` chạy cùng `AccessPolicy(actor).booking_scope()` cho hai đối tượng và nhận ID khách hoặc `None`. Thử sửa `GUEST.actor.role = "admin"` bị chặn bằng `FrozenInstanceError` vì instance đã đóng băng. [domain.py](../backend/domain.py) · [services.py](../backend/services.py)
