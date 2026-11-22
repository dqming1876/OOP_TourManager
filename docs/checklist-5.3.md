# Minh chứng 5.3 — Tiêm lỗi logic, debugger và hồi quy

## Ca đã thực hiện

Chạy `python3 -m scripts.verify_axis5`. Script sao chép nguồn cần thiết vào thư mục tạm, thay đúng một toán tử trong điều kiện giữ chỗ và chạy lại **IT-01**. Repo làm việc và DB thật không bị sửa. Script đọc Call Stack và Watch bằng `sys.settrace` trong tiến trình kiểm thử.

| Lượt | Điều kiện còn chỗ | Kết quả IT-01 |
| --- | --- | --- |
| Baseline | `d.capacity - d.reserved >= ?` | PASS, HTTP 201 khi còn đúng 3 chỗ |
| Tiêm lỗi | `d.capacity - d.reserved > ?` | FAIL tại assert HTTP 201, nhận 409 |
| Khôi phục | `d.capacity - d.reserved >= ?` | PASS lại đúng ca IT-01 |

[Script tiêm lỗi có kiểm chứng](../scripts/verify_axis5.py) · [Ca hồi quy](../tests/test_integration_axis5.py)

## Tìm nguyên nhân bằng Call Stack và Watch

[Script debugger](../scripts/debug_axis5.py) đặt breakpoint trước lệnh INSERT trong `BookingRepository.place_booking`. Stack ghi được ở bản bị tiêm lỗi là `BookingRepository.place_booking → BookingService.place_booking → operations_route`. Watch ghi `requested = 3`, `capacity = 3`, `reserved = 0`. Chỗ còn đúng 3, nên điều kiện lớn hơn nghiêm ngặt loại sai trường hợp biên. Điều kiện đúng cho phép bằng nhau và vẫn trả 409 khi số chỗ không đủ.

## Trình diễn trong IDE

1. Chạy `python3 -m unittest discover` và `node --test tests/frontend/*.test.js` để kiểm tra backend và frontend.
2. Chạy `python3 -m scripts.verify_axis5` để lặp lại PASS → FAIL đúng lý do → PASS trên bản sao.
3. Khi giảng viên đưa lỗi khác, khoanh test bằng `python3 -m unittest tests.test_integration_axis5.IntegrationAxis5.test_it01_last_seats` và thay tên mẫu theo ca. Chạy fixture dưới debugger, dừng ở dòng chuẩn bị cập nhật SQL và xem đầu vào guard cùng trạng thái trước ghi. Nếu bộ test chưa bắt lỗi, thêm một tình huống nhỏ với expected tính tay, xác minh đỏ rồi sửa nguyên nhân và chạy toàn bộ.

## Ma trận hồi quy và tiêm lỗi

Chạy `python3 -m unittest tests.test_session_and_schedule` để kiểm tra lượt đi, thời hạn phiên và thời gian khóa đăng nhập. Chạy `python3 -m scripts.verify_mutations` để kiểm tra 11 biến thể độc lập. Mỗi biến thể chạy trong một bản sao tạm. Bộ test gốc PASS và phát hiện 11/11 biến thể. Tính cả ca giữ đúng ba chỗ của `verify_axis5`, hai script kiểm tra 12 ca tiêm lỗi.

| Ca | Điều kiện | Kết quả kiểm chứng |
| --- | --- | --- |
| RG-01 | Đợt trước ngày nghiệp vụ | HTTP 409, không sinh đơn và không giữ chỗ. |
| RG-02 | Phiên quanh mốc 8 giờ | Hợp lệ trước mốc và hết hiệu lực sau mốc. |
| RG-03 | Hạn mức theo cửa sổ 5 phút | Lượt sau 12 lần sai trả 429. Đăng nhập lại được khi cửa sổ hết hạn. |
| MU-01 | Bỏ kiểm tra quyền ở `save_tour` | Phát hiện bởi kiểm thử quyền trực tiếp. |
| MU-02 | Bỏ kiểm tra quyền ở `set_visibility` | Phát hiện bởi kiểm thử quyền trực tiếp. |
| MU-03 | Bỏ kiểm tra quyền ở `remove_departure` | Phát hiện bởi kiểm thử quyền trực tiếp. |
| MU-04 | Bỏ kiểm tra quyền ở `payment_history` | Phát hiện bởi kiểm thử quyền trực tiếp. |
| MU-05 | Cho phép đơn chờ có `paid=True` | Phát hiện bởi kiểm thử bất biến trạng thái. |
| MU-06 | Từ chối sức chứa bằng số chỗ giữ | Phát hiện bởi ca biên sức chứa. |
| MU-07 | Tính đơn chờ đi hôm nay là quá hạn | Phát hiện bởi ca biên ngày báo cáo. |
| MU-08 | Tính đơn đã thu đi hôm nay là hoàn thành | Phát hiện bởi ca biên ngày báo cáo. |
| MU-09 | Chấp nhận mật khẩu 5 ký tự | Phát hiện bởi ca biên đăng ký. |
| MU-10 | Cho phép lượt đăng nhập sai thứ 13 | Phát hiện bởi ca kiểm tra hạn mức. |
| MU-11 | Đếm ghi D1 qua `meta.changes` | Phát hiện bởi test adapter với trigger thanh toán. |
