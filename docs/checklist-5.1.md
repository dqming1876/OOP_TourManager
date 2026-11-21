# Minh chứng 5.1 — Thiết kế ca kiểm thử và Unit AAA

Chạy `npm run test:unit` hoặc `node --test test/unit-axis5.test.js`. Bộ Unit chạy bằng Node.js 24, chỉ nạp lớp miền và Service. Mock từ `node:test` tạo các port giả để điều khiển giá trị trả về và kiểm số lần gọi. Ngày nghiệp vụ cố định qua `fakeClock()`, đi qua constructor như ngày do root truyền khi chạy thật.

## Ma trận truy vết Rule ↔ TC-ID ↔ code

Mã R01–R07 đối chiếu với [quy tắc nghiệp vụ ở trục 3](checklist-3.3.md). Các mã R08–R11 bổ sung quy tắc hỗ trợ cho bộ Unit.

| Ca | Quy tắc và kỹ thuật | Dữ liệu và kết quả mong đợi | Nhánh code |
| --- | --- | --- | --- |
| UT-01 | R02 · BVA người lớn | 0 và 101 lỗi `adults`; 1 và 100 hợp lệ | [Booking.request](../worker/domain/booking.js) → `integerBetween` |
| UT-02 | R02 · BVA trẻ em | −1 và 100 lỗi `children`; 0 và 99 hợp lệ | [Booking.request](../worker/domain/booking.js) → `integerBetween` |
| UT-03 | R08 · EP liên hệ | Số có gạch và khoảng trắng ngoài hợp lệ sau khi chuẩn hóa. Số có chữ hoặc chỉ 7 chữ số bị loại. | [Booking.request](../worker/domain/booking.js) → kiểm tra `phone` |
| UT-04 | R01 · EP có giá chốt | Đơn 2 người lớn và 1 trẻ em theo giá chốt 500.000 ₫ là 1.500.000 ₫. Bản nháp chưa có giá trả 409 khi đọc tổng. | [Booking.total](../worker/domain/booking.js) |
| UT-05 | R03 · BVA sức chứa | 0 và 101 lỗi `capacity`; 1 và 100 hợp lệ | [Departure constructor](../worker/domain/departure.js) |
| UT-06 | R03 · BVA ngày | Tại 29/02/2028, ngày 28 bị từ chối vì đã qua, ngày 30 bị từ chối vì không tồn tại, chính ngày 29 được chuyển tới port đúng một lần. | [TourCatalogService.saveDeparture](../worker/service/tour-catalog-service.js) → [Departure](../worker/domain/departure.js) |
| UT-07 | R05/R07 · Ngoại lệ quyền | Khách ghi thu nhận 403 và DAL có 0 lần gọi. | [BookingService.updateBooking](../worker/service/booking-service.js) → `AccessPolicy.requireRole` |
| UT-08 | R02 · Ngoại lệ hết chỗ | Stub ghi đơn trả `false` nên Service trả 409 cho trường ngày. Mock nhận đúng 3 khách, ID chủ phiếu và ngày đã tiêm. | [BookingService.placeBooking](../worker/service/booking-service.js) |
| UT-09 | R06 · State và chủ đơn | Lệnh hủy của khách truyền guard từ `pending` sang `cancelled`, chưa thu và có ID chủ đơn. | [Booking.transition](../worker/domain/booking.js) và [BookingService.updateBooking](../worker/service/booking-service.js) |
| UT-10 | R05 · State thanh toán | Thu từ `confirmed / false` sang `confirmed / true`, hoàn đảo lại, cả hai do admin. | [Booking.transition](../worker/domain/booking.js) |
| UT-11 | R09 · BVA khoảng ngày | Một ngày đúng biên được chuyển nguyên vẹn tới port. Khoảng đảo bị từ chối trước lần gọi port. | [ReportsService.load](../worker/service/reports-service.js) |
| UT-12 | R10 · EP lịch trình | Tour 2 ngày sinh hai dòng điểm ghé theo đúng thứ tự. Thiếu một hoạt động bị từ chối. | [Tour.#buildItinerary](../worker/domain/tour.js) |
| UT-13 | R11 · EP bút toán | Thu 1.000.000 ₫ có dấu dương, hoàn 400.000 ₫ có dấu âm, số tiền 0 bị từ chối. | [PaymentEvent](../worker/domain/payment-event.js) |

## Đọc một ca theo AAA

UT-08 **Arrange** tạo tài khoản khách, ngày cố định và stub `placeBooking` trả thất bại. **Act** gửi yêu cầu đặt cho 2 người lớn và 1 trẻ em. **Assert** kiểm 409, trường ngày, đúng một lần gọi port, giá trị 3 khách và ID đã lấy từ phiên. Kết quả mong đợi là hằng từ tình huống và quy tắc, không gọi lại hàm sản phẩm để sinh expected. [Bộ Unit](../test/unit-axis5.test.js)
