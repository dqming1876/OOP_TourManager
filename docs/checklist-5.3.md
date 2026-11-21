# Minh chứng 5.3 — Tiêm lỗi logic, debugger và hồi quy

## Ca đã thực hiện

Chạy `npm run test:mutation`. Script sao chép nguồn cần thiết vào thư mục tạm, thay đúng một toán tử trong điều kiện giữ chỗ và chạy lại **IT-01**. Repo làm việc và DB thật không bị sửa. Phiên debugger dùng Node Inspector trong tiến trình kiểm thử.

| Lượt | Điều kiện còn chỗ | Kết quả IT-01 |
| --- | --- | --- |
| Baseline | `d.capacity - d.reserved >= ?` | PASS, HTTP 201 khi còn đúng 3 chỗ |
| Tiêm lỗi | `d.capacity - d.reserved > ?` | FAIL tại assert HTTP 201, nhận 409 |
| Khôi phục | `d.capacity - d.reserved >= ?` | PASS lại đúng ca IT-01 |

[Script tiêm lỗi có kiểm chứng](../scripts/verify-axis5.mjs) · [Ca hồi quy](../test/integration-axis5.test.js)

## Tìm nguyên nhân bằng Call Stack và Watch

[Script debugger](../scripts/debug-axis5.mjs) đặt breakpoint trước lệnh INSERT trong `BookingRepository.placeBooking`. Stack ghi được ở bản bị tiêm lỗi là `BookingRepository.placeBooking → BookingService.placeBooking → operationsRoute`. Watch ghi `requested = 3`, `capacity = 3`, `reserved = 0`. Chỗ còn đúng 3, nên điều kiện lớn hơn nghiêm ngặt loại sai trường hợp biên. Điều kiện đúng cho phép bằng nhau và vẫn trả 409 khi số chỗ không đủ.

## Trình diễn trong IDE

1. Chạy `npm test` để thấy toàn bộ bộ test xanh.
2. Chạy `npm run test:mutation` để lặp lại PASS → FAIL đúng lý do → PASS trên bản sao.
3. Khi giảng viên đưa lỗi khác, khoanh test bằng `node --test --test-name-pattern='IT-01' test/integration-axis5.test.js` và thay tên mẫu theo ca. Chạy fixture dưới debugger, dừng ở dòng chuẩn bị cập nhật SQL và xem đầu vào guard cùng trạng thái trước ghi. Nếu bộ test chưa bắt lỗi, thêm một tình huống nhỏ với expected tính tay, xác minh đỏ rồi sửa nguyên nhân và chạy toàn bộ.
