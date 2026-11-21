# Minh chứng 4.2 — Sequence, máy trạng thái và debugger

## Lưu tour và nhiều điểm ghé

```mermaid
sequenceDiagram
    participant F as "Form sửa tour"
    participant S as "TourCatalogService"
    participant T as "Tour"
    participant R as "TourCatalogRepository"
    participant DB as "D1"
    F->>S: submitTour và POST qua operations_route
    S->>T: new Tour(id,input)
    loop Mỗi ngày trong itinerary
        T->>T: tạo TourStop cho ngày index + 1
    end
    S->>R: save_tour(tour,create)
    alt Có lịch trình mới
        R->>DB: batch ghi tour, điểm dùng chung và các dòng lịch trình
        DB-->>R: commit hoặc rollback cả batch
    else Không gửi lịch trình
        R->>DB: ghi riêng tour
    end
    S-->>F: trả mã tour hoặc lỗi
```

## Đặt giữ chỗ

```mermaid
sequenceDiagram
    participant F as "Form đặt tour"
    participant S as "BookingService"
    participant B as "Booking"
    participant R as "BookingRepository"
    participant DB as "D1"
    F->>S: placeOrder và POST qua operations_route
    S->>B: request(id,userId,input)
    B-->>S: đơn chờ với số người hợp lệ
    S->>R: place_booking(booking,today)
    R->>DB: INSERT SELECT kiểm ngày, bán và sức chứa
    alt Còn đủ chỗ và ghi thành công
        DB->>DB: trigger reserve_booking_seats
        DB-->>R: một dòng được tạo
        S-->>F: HTTP 201 và mã đơn
    else Không khớp điều kiện
        DB-->>R: không tạo dòng
        S-->>F: HTTP 409
    else Lỗi khi ghi đơn hoặc tăng chỗ
        DB-->>R: rollback câu lệnh
        S-->>F: HTTP 500 qua bộ xử lý lỗi
    end
```

## Trạng thái lưu của đơn

```mermaid
stateDiagram-v2
    direction TB
    [*] --> Pending: "đặt [đợt mở và đủ chỗ]"
    Pending --> ConfirmedUnpaid: "xác nhận [admin và đến hạn ngày đi]"
    Pending --> Cancelled: "hủy [chủ đơn hoặc admin]"
    ConfirmedUnpaid --> ConfirmedPaid: "thu [admin]"
    ConfirmedPaid --> ConfirmedUnpaid: "hoàn [admin]"
    ConfirmedUnpaid --> Cancelled: "hủy [admin]"
    Cancelled --> [*]
```

Hai trạng thái xác nhận dùng cùng `bookings.status = confirmed` và được phân biệt bằng `paid`. Trong sơ đồ, “đến hạn ngày đi” nghĩa là ngày hiện tại ≤ ngày đi theo giờ Việt Nam. Guard nằm ở `Booking.transition()` và mệnh đề `WHERE` của `BookingRepository.update_booking()`. Đơn chờ không thể thu tiền. Đơn đã thu phải hoàn trước khi hủy. [domain.py](../backend/domain.py) · [repositories.py](../backend/repositories.py)

## Call Stack và Watch đã xác minh

Chạy `python3 -m scripts.debug_axis4` với Python 3.12. Script dùng `sys.settrace` trong cùng tiến trình, gọi lớp HTTP của Worker và xác nhận các frame và giá trị tại các điểm dừng.

| Breakpoint | Call Stack quan sát được | Watch |
| --- | --- | --- |
| `Tour.request`, dòng tạo `TourStop` | `__init__ → <genexpr> → request → save_tour → operations_route` | `index + 1` lần lượt 1 và 2 |
| `BookingService.place_booking`, sau `Booking.request` | `place_booking → operations_route` | `adults + children = 3` |
| `BookingRepository.place_booking`, trước INSERT | `place_booking → place_booking → operations_route` | `booking.people = 3` |
| `BookingRepository.update_booking`, trước UPDATE khi thử thu đơn chờ | `update_booking → update_booking → operations_route` | Guard yêu cầu `confirmed`, ghi `next_paid = true`, admin không giới hạn chủ đơn. Đơn thực tế `pending`; HTTP 409, `paid = 0`, không có bút toán. |

Khi vấn đáp, có thể mở `python3 -m pdb -m scripts.demo` trong IDE, đặt breakpoint tương ứng và thao tác qua Form. Cửa sổ máy chủ sẽ hiện thông tin tài khoản thử sau khi tiếp tục chạy. Browser call stack có `placeOrder/submitTour`; Python call stack bắt đầu ở Worker vì đi qua HTTP. [Script xác minh](../scripts/debug_axis4.py)
