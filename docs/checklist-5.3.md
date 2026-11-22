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

## Ba ca hồi quy bổ sung

Chạy `python3 -m unittest tests.test_review_regressions` với SQLite tạm và thời gian kiểm soát trong test.

| Ca | Kết quả kiểm chứng |
| --- | --- |
| IT-05 | Đợt ở trước ngày nghiệp vụ trả HTTP 409, không tạo đơn hay giữ chỗ. Fixture nhận `day_offset` theo cách đặt tên Python. |
| IT-06 | Phiên đăng nhập hợp lệ trước mốc 8 giờ và hết hiệu lực sau mốc này. |
| IT-07 | Sau 12 lần sai, yêu cầu tiếp theo bị khóa với HTTP 429. Đăng nhập lại được khi đủ 5 phút. Test dùng bộ đếm D1 qua SQLite và kiểm tra nhiều instance `Application`. |

Ba ca trên kiểm tra hành vi hiện hành. Ca tiêm lỗi đã chạy là IT-01 ở phần trước.

## Bổ sung sau rà soát

Chạy `python3 -m scripts.verify_review`: 11 biến thể độc lập (4 guard quyền, pending/paid, sức chứa, 2 biên ngày, mật khẩu, ngưỡng đăng nhập, số dòng D1). Mỗi biến thể chạy trong bản sao tạm; baseline phải PASS và từng mutant phải bị test phát hiện. Đây là tập thử xác định trong repo, không phải bộ 16 mutant của công cụ bên ngoài.
