# Minh chứng 4.4 — Bất biến miền, kế thừa và LSP

| Bất biến | Bảo vệ trong lớp | Thử phá |
| --- | --- | --- |
| Lịch trình gửi lên đủ số ngày, không chèn ngẫu nhiên một điểm ghé sau khi tạo | `Tour.#buildItinerary` kiểm số dòng. `#stops` là private; getter chỉ trả mảng đóng băng. Mỗi `TourStop` và `Destination` cũng đóng băng. | Tạo tour 2 ngày với một hoạt động trả lỗi 400; `tour.stops.push(...)` ném TypeError; sửa mảng bản sao không đổi tour. |
| Chỗ đã giữ thuộc `[0, capacity]` | Constructor `Departure` kiểm giới hạn trước khi đóng băng. Trạng thái DB dùng CHECK và câu SQL kiểm lại lúc ghi. | `new Departure(..., 3, 4)` trả lỗi 400. |
| Giá chốt của đơn ổn định, chỉ đơn xác nhận mới có thể đã thu | Constructor `Booking` kiểm cặp status/paid. Bản chụp đóng băng, `total` tính theo số người × giá chốt. Đơn mới yêu cầu giá hiện hành tại câu INSERT. | Sửa `unitPrice` trực tiếp ném TypeError; tạo `pending` với `paid=true` trả lỗi 400. |
| Bút toán có loại thu hoặc hoàn và số tiền nguyên dương | `PaymentEvent` kiểm ngày, `PaymentKind` và số tiền ở constructor. Getter `signedAmount` gắn dấu theo loại. | Khoản hoàn số tiền 0 bị từ chối. |

Mảng không thể thêm/xóa phần tử và bản ghi chi tiết chỉ đọc; cập nhật qua yêu cầu tạo đối tượng hợp lệ mới. Điểm vào BLL và ràng buộc DB tiếp tục kiểm tra khi dữ liệu bị truy cập đồng thời. [Domain](../worker/domain) · [Kiểm thử](../test/architecture.test.js)

## Kế thừa, dynamic binding và LSP

`CustomerAccount` và `AdministratorAccount` đều là `Account`. Hợp đồng `bookingScope(): string | null` trả ID khi giới hạn theo chủ đơn và `null` khi đọc toàn bộ. Hai lớp con cùng cung cấp `toPublic()`; khách mở rộng kết quả với dữ liệu hồ sơ công khai. `AccessPolicy.bookingScope()` gọi phương thức trên account lấy từ phiên; lớp cụ thể quyết định cách trả scope tại runtime. Bên gọi `BookingService.bookings` chuyển trực tiếp giá trị đúng hợp đồng xuống `BookingPort.listBookings`, không kiểm kiểu hay ép kiểu.

Đổi instance khách sang admin thay đổi phạm vi theo vai trò vẫn giữ kiểu trả về và các tiền/hậu điều kiện của API. Bài test chạy cùng hàm `getBookingScope(account)` cho hai đối tượng và nhận ID khách hoặc `null`. Thử sửa vai trò khách thành admin bị chặn vì instance đã đóng băng. [account.js](../worker/domain/account.js) · [access-policy.js](../worker/service/access-policy.js)
