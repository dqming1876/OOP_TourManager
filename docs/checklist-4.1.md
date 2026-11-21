# Minh chứng 4.1 — UML lớp, vòng đời và CSDL

## Lớp miền và chính sách truy cập

```mermaid
classDiagram
    direction TB
    class Tour {
        +id
        +details
        +stops
        +request()
    }
    class TourStop {
        +dayNumber
        +activity
        +destination
        +write_row()
    }
    class Destination {
        +province
        +name
    }
    class Booking {
        +id
        +tourId
        +day
        +unitPrice
        +status
        +paid
        +request()$
        +transition()$
        +people()
        +total()
    }
    class Departure {
        +tourId
        +day
        +capacity
        +reserved
        +requireOpenDate()
        +remaining()
    }
    class Account {
        +id
        +role
        +toPublic()
        +bookingScope()
    }
    class CustomerAccount {
        +profile
        +validateUpdate()
        +toPublic()
    }
    class AdministratorAccount {
        +bookingScope()
    }
    class AccessPolicy {
        +actor
        +requireRole()
        +bookingScope()
    }
    Tour "1" *-- "0..30" TourStop : chứa
    TourStop "*" --> "1" Destination : điểm ghé
    Booking "*" --> "1" Departure : tourId và day
    Account <|-- CustomerAccount
    Account <|-- AdministratorAccount
    AccessPolicy o--> "0..1" Account : nhận qua constructor
```

Các ký hiệu `details()`, `stops()`, `people()`, `total()`, `remaining()` chỉ getter JavaScript. Trường miền công khai ở sơ đồ là chỉ đọc trên instance đã đóng băng. `Tour` tạo và sở hữu các `TourStop`. Số phần tử là số ngày khi người dùng gửi lịch trình; `null` biểu thị lệnh sửa tour không gửi phần lịch trình.

## Service, port và lưu trữ

```mermaid
classDiagram
    direction TB
    class BookingPort {
        <<interface>>
        +listBookings(ownerId)
        +place_booking(booking, today)
        +update_booking(id, rule, ownerId, today)
        +payment_history(id)
    }
    class BookingService {
        +bookings()
        +place_booking(input)
        +update_booking(id, action)
        +payment_history(id)
    }
    class BookingRepository {
        +listBookings(ownerId)
        +place_booking(booking, today)
        +update_booking(id, rule, ownerId, today)
        +payment_history(bookingId)
    }
    class PaymentEvent {
        +date
        +kind
        +amount
        +signedAmount()
    }
    BookingService --> BookingPort : constructor
    BookingRepository ..|> BookingPort : hiện thực
    BookingService ..> Booking : kiểm và tạo
    BookingRepository ..> PaymentEvent : ánh xạ sự kiện
```

Tổng cộng sơ đồ có **12 lớp chạy thật** sau khi loại interface `BookingPort`. Sáu loại quan hệ và đối chiếu mã:

| Quan hệ UML | Ví dụ | Đọc từ code hoặc SQL |
| --- | --- | --- |
| Association | `Booking → Departure` | Đơn lưu `tourId` và `day`. FK ghép trỏ đúng đợt. |
| Aggregation | `AccessPolicy ◇→ Account` | Root tạo danh tính từ phiên rồi truyền vào policy. Policy có thể bỏ đi sau request trong khi tài khoản và dữ liệu còn nguyên. |
| Composition | `Tour ◆→ TourStop` | Tour tạo riêng phần tử qua constructor, giữ mảng chỉ đọc. Điểm ghé của tour bị xóa theo tour ở DB. |
| Generalization | `CustomerAccount / AdministratorAccount → Account` | Hai lớp con dùng `extends Account` và có cùng hợp đồng phạm vi đọc. |
| Realization | `BookingRepository → BookingPort` | `@implements` khai báo hợp đồng cấu trúc. Điểm lắp đặt dùng cùng hợp đồng cho adapter lưu trữ và bộ nhớ. |
| Dependency | `BookingService → Booking` | Dùng tạm `Booking.request/transition` để xử lý yêu cầu. Service không sở hữu một instance Booking dài hạn. |

Lớp cơ sở `Account` chứa constructor và mã chạy dùng chung. Hợp đồng `BookingPort` được khai báo bằng `typing.Protocol` và xác minh bằng kiểm thử.

## Kiểm toán ngược ba lớp chọn ngẫu nhiên

| Lớp | Đối chiếu cấu trúc và quan hệ |
| --- | --- |
| `Tour` | `Tour` là dataclass bất biến. `details` là mapping chỉ đọc, `stops` là tuple. `Tour.request()` tạo các `TourStop` theo đúng thứ tự. [domain.py](../backend/domain.py) |
| `TourStop` | Constructor nhận thứ tự, hoạt động, tỉnh và điểm. Instance đóng băng ba thuộc tính trong UML. `write_row()` xuất đúng khóa ngày, điểm ghé, nội dung hoạt động. [domain.py](../backend/domain.py) |
| `BookingRepository` | Constructor nhận DB. Bốn phương thức trong port khớp chữ ký triển khai. `payment_history()` dựng `PaymentEvent`; `place_booking()` lấy khóa đợt từ đối tượng Booking và kiểm khóa trong SQL. [repositories.py](../backend/repositories.py) |

## Bảy bảng và phụ thuộc hàm

| Bảng | Khóa ứng viên và phụ thuộc chính | Ràng buộc |
| --- | --- | --- |
| `accounts` | `id` hoặc `username` → danh tính và hồ sơ | PK id, UNIQUE username |
| `tours` | `id` → giá, hiển thị và nội dung | PK, CHECK giá/hiển thị/JSON hợp lệ |
| `destinations` | `id` hoặc `(province,name)` xác định địa danh | PK, UNIQUE theo tỉnh/tên |
| `departures` | `(tour_id,day)` → sức chứa và chỗ giữ | PK ghép, FK tour, CHECK sức chứa và chỗ giữ |
| `tour_stops` | `(tour_id,day_number)` → điểm đến, hoạt động | PK ghép, FK tour/địa danh, CHECK ngày và hoạt động |
| `bookings` | `id` → người đặt, khóa đợt, liên hệ và giá chốt | FK khách và đợt, CHECK số người, giá, trạng thái/thu tiền |
| `payment_events` | `id` → đơn, ngày ghi, loại và số tiền | FK đơn, CHECK loại và số tiền |

Khóa ghép xác định thuộc tính liên kết theo toàn khóa. Tỉnh và tên địa danh đặt ở bảng địa danh; ngày/hoạt động của từng điểm ghé đặt ở bảng nối. Tên tour, liên hệ và giá trong đơn là dữ liệu lịch sử theo mã đơn. Hai danh mục đơn giản là tour và địa danh, chiếm 2/7. Các bảng còn lại phục vụ tài khoản, lịch, liên kết hoặc giao dịch. Nội dung giới thiệu tour đi trong một cột JSON; các thuộc tính nối, lịch trình và giao dịch đã tách thành bảng. `reserved` và `paid` là trạng thái vận hành cập nhật đồng bộ bằng trigger để truy vấn nhanh. [Schema](../Database)

**Thử hủy Whole.** Migration 0005 thêm `ON DELETE CASCADE` từ tour đến phần lịch trình. Xóa tour chưa có đợt/lịch sử chỉ xóa điểm ghé của tour đó, địa danh chung và điểm ghé của tour khác vẫn còn. Xóa tour có đợt bị FK chặn. Hai ca kiểm thử xác minh hành vi trên SQLite tạm và bảo toàn dữ liệu khi nâng schema. [Migration 0005](../Database/0005_tour_stop_ownership.sql) · [Kiểm thử](../tests/test_architecture.py)
