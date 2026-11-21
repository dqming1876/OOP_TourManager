# Mingo — Minh chứng tiêu chí 1.2 đến 1.4

## 1.2 — Master–Detail, bộ lọc và báo cáo

- **Quản lý tour → Sửa tour** tự nạp các điểm ghé và hoạt động theo ngày. Đổi số ngày cập nhật số dòng chi tiết. Lưu tour và các dòng chi tiết trong một batch D1. Mở lại để kiểm tra danh sách đã lưu.
- **Xử lý đơn / Thu tiền → Mở phiếu** nạp lịch sử thu và hoàn của đúng đơn. Phiếu hiển thị số khách, giá lịch sử, thu ròng và phần còn phải thu. Ghi thu hoặc hoàn tạo sự kiện trong cùng giao dịch với cập nhật đơn.
- **Báo cáo** có dòng tiền theo tháng, tình hình đặt tour theo trạng thái và sức chứa từng đợt. Có biểu đồ dòng tiền, ngày bắt đầu/kết thúc, lọc theo tour và nút xóa lọc. Chọn **Tải Excel** để lưu XLSX hoặc **In / Lưu PDF** và chọn **Lưu dưới dạng PDF** trong hộp thoại trình duyệt. Hai bản xuất dùng cùng dữ liệu với bảng đang xem.

Dòng tiền lọc theo ngày ghi nhận. Hai báo cáo còn lại lọc theo ngày khởi hành. Đơn quá hạn là đơn còn chờ xác nhận sau ngày đi. Đơn hoàn thành là đơn đã xác nhận, đã thu và đã qua ngày đi. Đơn hủy được đếm theo trạng thái, nhưng không giữ chỗ. Nếu áp migration vào dữ liệu 1.1 đã có thu tiền, số dư mở đầu mang ngày migration vì dữ liệu cũ không ghi ngày thu.

## 1.3 — Seed, quan hệ và số đối chiếu

`scripts/demo-data.mjs` tạo bộ mẫu liên thông từ khóa ngoại thật. `node scripts/demo.mjs` nạp tự động vào SQLite tạm. Dùng `node scripts/seed-demo.mjs mingo-demo.sql` để tạo SQL cho D1 cục bộ mới. Mỗi bộ seed có 92 dòng nghiệp vụ. Danh mục khởi tạo trong migration 0002 không tính vào 92 dòng này.

| Bảng | Số dòng mẫu |
| --- | ---: |
| Tài khoản | 8 |
| Tour | 3 |
| Điểm đến | 6 |
| Lịch trình tour | 6 |
| Đợt khởi hành | 9 |
| Đơn đặt | 36 |
| Phiếu thu và hoàn | 24 |

Mỗi tour có đợt ở hai tháng đã qua và một tháng sau. Ví dụ, lọc **Hà Nội – Phố cổ và Hồ Gươm** trong tháng liền trước:

- Giá 1.200.000 ₫/khách. Thu hai khách ở đơn hoàn thành và một khách ở đơn hủy có hoàn tiền. Tổng thu 3.600.000 ₫, hoàn 1.200.000 ₫, thu ròng 2.400.000 ₫.
- Có bốn đơn, bảy khách gồm hai khách hoàn thành, một khách hủy, hai khách quá hạn và hai khách xác nhận chưa thu.
- Có tám chỗ, sáu chỗ đã giữ và hai chỗ trống. Tháng sau cùng tour chỉ còn một chỗ.

`test/reports-seed.test.js` so sánh các con số này với API, kiểm tra khóa ngoại, quyền xem báo cáo và thay đổi báo cáo ngay sau ghi thu/hoàn.

## 1.4 — Bàn giao và kiểm tra

- Xem [README](../README.md) để chạy bản demo, đăng nhập, tạo lại dữ liệu mẫu và chạy kiểm thử.
- `node scripts/package-demo.mjs mingo-demo.zip` đóng gói nguồn và tài nguyên. Giải nén rồi chạy `node scripts/demo.mjs` bằng Node.js 24. Máy chấm cần sẵn Node.js 24 và trình duyệt. Bản demo dùng dữ liệu tạm, dựng lại mỗi khi khởi động.
- Dùng bộ slide và video demo đi kèm để trình bày luồng. Lịch sử Git được giữ nguyên. Tiêu chí ≥12 commit có nội dung qua ≥3 tuần cần đánh giá theo lịch sử làm việc thực tế.
