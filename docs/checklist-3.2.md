# Minh chứng 3.2 — ERD và mô hình thực thể

## Hai liên kết nhiều–nhiều có thuộc tính

```mermaid
erDiagram
    TOUR ||--o{ TOUR_STOP : "lên lịch"
    DESTINATION ||--o{ TOUR_STOP : "được ghé"
    TOUR_STOP {
        string tour_id PK,FK
        int day_number PK
        int destination_id FK
        string activity
    }
```

Tour có nhiều điểm ghé và một địa danh xuất hiện ở nhiều tour. `TourStop` giữ **ngày thứ mấy** và **hoạt động** riêng của mỗi liên kết. Cùng địa danh có thể xuất hiện nhiều ngày trong một tour. Khóa là `(tour_id, day_number)`; `destination_id` trỏ đến địa danh dùng chung. [Migration 0003](../Database/0003_reporting_details.sql)

```mermaid
erDiagram
    CUSTOMER ||--o{ BOOKING : "đặt"
    DEPARTURE ||--o{ BOOKING : "nhận"
    BOOKING {
        string id PK
        string user_id FK
        string tour_id FK
        string day FK
        int adults
        int children
        int unit_price
        string status
        int paid
    }
```

Một khách có thể đặt nhiều đợt, một đợt nhận nhiều khách. `Booking` là thực thể giao dịch nối hai phía. Khóa ngoại `(tour_id, day)` trỏ đúng đợt. Mã đơn độc lập cho phép giữ nhiều lần đặt hợp lệ hoặc lịch sử các đơn đã hủy của cùng khách và đợt. [Migration 0001](../Database/0001_tour_operations.sql)

## Tám lớp có hành vi tham gia luồng chạy

| Lớp | Thực thể hoặc nguồn | Hành vi và nơi gọi |
| --- | --- | --- |
| `Tour` | `tours` | Ràng buộc giá, số ngày, ảnh; tạo tập `TourStop` đủ số ngày. Dùng khi `TourCatalogService.save_tour`. |
| `Destination` | `destinations` | Chuẩn hóa tên địa danh và tỉnh theo quy tắc chiều dài trước khi ghi điểm ghé. `Tour` dùng khi dựng liên kết. |
| `TourStop` | `tour_stops` | Kiểm ngày thứ mấy và nội dung. Cung cấp ngày/điểm/hoạt động để repository ghi trong cùng batch với tour. |
| `Departure` | `departures` | Kiểm ngày và sức chứa trước ghi. Tính chỗ còn từ sức chứa trừ chỗ đã giữ khi dựng danh mục. |
| `Booking` | `bookings` | Kiểm số khách và thông tin liên hệ, tính tổng tiền từ giá chốt, quyết định trạng thái/ngày/tiền được phép chuyển. |
| `PaymentEvent` | `payment_events` | Tính trị giá có dấu của khoản thu/hoàn. DTO khoản tiền có dấu được phiếu admin cộng thành thu ròng. |
| `CustomerAccount` | `accounts` | Kiểm dữ liệu cập nhật hồ sơ. `booking_scope()` trả ID chủ đơn để giới hạn phạm vi đọc. |
| `AdministratorAccount` | Bảng `accounts` có FK `role` tới `roles`; cấu hình chỉ khởi tạo admin lần đầu | `booking_scope()` cho phạm vi quản trị toàn bộ đơn. `public()` chỉ đưa danh tính công khai ra HTTP. |

`Account` là lớp cơ sở nội bộ cho hai loại tài khoản, không tính vào tám lớp cụ thể. Python kiểm tra các tập giá trị trạng thái đơn (pending, confirmed, cancelled), loại giao dịch (collect, refund) và vai trò (admin, customer). Trạng thái báo cáo “quá hạn/hoàn thành” là giá trị suy ra từ ngày, trạng thái và thanh toán. [Mã miền](../backend/domain.py) · [Repository tour](../backend/repositories.py) · [Repository đơn](../backend/repositories.py)

## Đọc ngược thuộc tính lịch sử

`bookings.unit_price` được lấy từ `tours.price` ngay trong câu lệnh tạo đơn. `Booking.total` tính `(adults + children) × unitPrice` từ bản chụp trên phiếu. Ví dụ test đặt 3 người lúc giá 1.200.000 ₫, rồi sửa tour lên 5.000.000 ₫. Giá trị đơn cũ vẫn là 3.600.000 ₫. `bookings.title` cũng là bản chụp để tên hiển thị trên phiếu cũ giữ được ý nghĩa lịch sử. [Kiểm thử](../tests/test_operations.py)

Nếu đổi quan hệ Tour–Đợt từ 1–n sang n–n thì đợt có định danh riêng và cần bảng nối có khóa `(tour_id, departure_id)`. Cần quyết định chỗ giữ dùng chung cho đợt hay theo tour. Khi đó `Departure`, khóa ngoại của `Booking`, trigger giữ/trả chỗ và truy vấn sức chứa đều cần sửa theo lựa chọn đó. Trước khi đổi, phải ánh xạ các đơn lịch sử sang khóa mới để giữ chính xác ngày và tour đã đặt.

## Bổ sung sau rà soát

Ba kiểu `StrEnum`: `Role`, `BookingStatus`, `PaymentKind`. Booking và PaymentEvent chuyển đầu vào về Enum và từ chối giá trị không hợp lệ; JSON vẫn dùng giá trị chuỗi tương thích giao diện.
