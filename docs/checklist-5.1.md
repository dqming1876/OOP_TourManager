# Minh chứng 5.1 — Thiết kế ca kiểm thử và Unit AAA

Chạy `python3 -m unittest tests.test_unit_axis5`. Bộ Unit chạy bằng Python 3.12 và dùng các port giả; không khởi tạo DB. Mock từ `unittest.mock` tạo các port giả để điều khiển giá trị trả về và kiểm số lần gọi. Ngày nghiệp vụ cố định qua giá trị ngày cố định, đi qua constructor như ngày do root truyền khi chạy thật.

## Ma trận truy vết Rule ↔ TC-ID ↔ code

Mã R01–R07 đối chiếu với [quy tắc nghiệp vụ ở trục 3](checklist-3.3.md). Các mã R08–R11 bổ sung quy tắc hỗ trợ cho bộ Unit.

| Ca | Quy tắc và kỹ thuật | Dữ liệu và kết quả mong đợi | Nhánh code |
| --- | --- | --- | --- |
| UT-01 | R02 · BVA người lớn | 0 và 101 lỗi `adults`; 1 và 100 hợp lệ | [Booking.request](../backend/domain.py) → `integer_between` |
| UT-02 | R02 · BVA trẻ em | −1 và 100 lỗi `children`; 0 và 99 hợp lệ | [Booking.request](../backend/domain.py) → `integer_between` |
| UT-03 | R08 · EP liên hệ | Số có gạch và khoảng trắng ngoài hợp lệ sau khi chuẩn hóa. Số có chữ hoặc chỉ 7 chữ số bị loại. | [Booking.request](../backend/domain.py) → kiểm tra `phone` |
| UT-04 | R01 · EP có giá chốt | Đơn 2 người lớn và 1 trẻ em theo giá chốt 500.000 ₫ là 1.500.000 ₫. Bản nháp chưa có giá trả 409 khi đọc tổng. | [Booking.total](../backend/domain.py) |
| UT-05 | R03 · BVA sức chứa | 0 và 101 lỗi `capacity`; 1 và 100 hợp lệ | [Departure constructor](../backend/domain.py) |
| UT-06 | R03 · BVA ngày | Tại 29/02/2028, ngày 28 bị từ chối vì đã qua, ngày 30 bị từ chối vì không tồn tại, chính ngày 29 được chuyển tới port đúng một lần. | [TourCatalogService.save_departure](../backend/services.py) → [Departure](../backend/domain.py) |
| UT-07 | R05/R07 · Ngoại lệ quyền | Khách ghi thu nhận 403 và DAL có 0 lần gọi. | [BookingService.update_booking](../backend/services.py) → `AccessPolicy.require_role` |
| UT-08 | R02 · Ngoại lệ hết chỗ | Stub ghi đơn trả `false` nên Service trả 409 cho trường ngày. Mock nhận đúng 3 khách, ID chủ phiếu và ngày đã tiêm. | [BookingService.place_booking](../backend/services.py) |
| UT-09 | R06 · State và chủ đơn | Lệnh hủy của khách truyền guard từ `pending` sang `cancelled`, chưa thu và có ID chủ đơn. | [Booking.transition](../backend/domain.py) và [BookingService.update_booking](../backend/services.py) |
| UT-10 | R05 · State thanh toán | Thu từ `confirmed / false` sang `confirmed / true`, hoàn đảo lại, cả hai do admin. | [Booking.transition](../backend/domain.py) |
| UT-11 | R09 · BVA khoảng ngày | Một ngày đúng biên được chuyển nguyên vẹn tới port. Khoảng đảo bị từ chối trước lần gọi port. | [ReportsService.load](../backend/services.py) |
| UT-12 | R10 · EP lịch trình | Tour 2 ngày sinh hai dòng điểm ghé theo đúng thứ tự. Thiếu một hoạt động bị từ chối. | [Tour.request](../backend/domain.py) |
| UT-13 | R11 · EP bút toán | Thu 1.000.000 ₫ có dấu dương, hoàn 400.000 ₫ có dấu âm, số tiền 0 bị từ chối. | [PaymentEvent](../backend/domain.py) |

Các ca biên dưới đây gồm kiểm thử miền độc lập và ca đi qua API hoặc SQLite. Chạy `python3 -m unittest tests.test_domain_boundaries tests.test_login_limits`.

| Ca | Quy tắc và kỹ thuật | Dữ liệu và kết quả mong đợi | Nhánh code |
| --- | --- | --- | --- |
| UT-14 | R05/R07 · Quyền trực tiếp | Khách nhận 403, người chưa đăng nhập nhận 401 ở cả bốn phương thức. Repository có 0 lần gọi. | [Service](../backend/services.py) → `save_tour`, `set_visibility`, `remove_departure`, `payment_history` |
| UT-15 | R05 · Bất biến trạng thái | `pending` và `cancelled` từ chối `paid=True`. `confirmed` chấp nhận. | [Booking](../backend/domain.py) |
| BV-01 | R03 · Sức chứa bằng chỗ giữ | Sức chứa bằng `reserved` được chấp nhận. Sức chứa thấp hơn trả 409. | [Repository lịch](../backend/repositories.py) |
| BV-02 | Báo cáo · Ngày khởi hành bằng hôm nay | Đơn chờ chưa quá hạn. Đơn đã thu chưa hoàn thành. Cả hai đổi trạng thái báo cáo vào ngày kế tiếp. | [ReportsRepository](../backend/repositories.py) |
| BV-03 | Đăng ký · Độ dài mật khẩu | Mật khẩu 5 ký tự trả 400, 6 ký tự được chấp nhận. | [AccountsService](../backend/services.py) |
| BV-04 | Đăng nhập · Ngưỡng hạn mức | Lần sai thứ 12 trả 401. Lượt tiếp theo trả 429 đến khi cửa sổ 5 phút kết thúc. | [Test hạn mức](../tests/test_login_limits.py) |

## Đọc một ca theo AAA

UT-08 **Arrange** tạo tài khoản khách, ngày cố định và stub `place_booking` trả thất bại. **Act** gửi yêu cầu đặt cho 2 người lớn và 1 trẻ em. **Assert** kiểm 409, trường ngày, đúng một lần gọi port, giá trị 3 khách và ID đã lấy từ phiên. Kết quả mong đợi là hằng từ tình huống và quy tắc, không gọi lại hàm sản phẩm để sinh expected. [Bộ Unit](../tests/test_unit_axis5.py)
