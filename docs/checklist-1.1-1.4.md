# Mingo — Minh chứng checklist 1.1–1.4

Đề tài nhóm 1 người MI4090. Mingo quản lý từ khi mở tour đến khi khách giữ chỗ và quản trị xử lý phiếu. Tiền thu và hoàn được ghi nhận thủ công trong đồ án.

## 1.1 — Chức năng và phân quyền

### BFD

| Cấp 1 | Cấp 2 | Cấp 3 |
| --- | --- | --- |
| Mingo | 1. Danh mục tour | Thêm hoặc sửa tour, ẩn hoặc hiện, tra cứu tour |
| Mingo | 2. Lịch khởi hành | Mở đợt, đổi sức chứa, xem số chỗ, xóa đợt chưa từng có đơn |
| Mingo | 3. Đặt và xử lý đơn | Đặt giữ chỗ, xem đơn, xác nhận, hủy trả chỗ |
| Mingo | 4. Thanh toán | Ghi nhận thu tiền, ghi nhận hoàn tiền |
| Mingo | 5. Hồ sơ khách | Xem và cập nhật thông tin liên hệ của chính mình |

### Use case, form và phân quyền

| UC | Nhánh | Người dùng | Form hoặc màn hình | Điểm xử lý |
| --- | --- | --- | --- | --- |
| UC01 Quản lý tour | 1 | Admin | Quản lý tour → biên tập tour | `TourCatalogService.save_tour/set_visibility` |
| UC02 Quản lý lịch | 2 | Admin | Lịch khởi hành → chọn tour và lưu đợt | `TourCatalogService.save_departure/remove_departure` |
| UC03 Đặt tour và giữ chỗ | 3 | Khách | Chi tiết tour → form đặt chuyến đi | `BookingService.place_booking` |
| UC04 Xem đơn của mình | 3 | Khách | Hành trình của tôi | `BookingService.bookings` |
| UC05 Xác nhận đơn | 3 | Admin | Xử lý đơn → phiếu xử lý đơn | `BookingService.update_booking('confirm')` |
| UC06 Hủy đơn và trả chỗ | 3 | Khách với đơn chờ của mình, hoặc Admin với đơn chưa thu tiền | Hành trình của tôi hoặc phiếu xử lý đơn | `BookingService.update_booking('cancel')` |
| UC07 Ghi nhận thu hoặc hoàn | 4 | Admin | Thu tiền / hoàn tiền → phiếu thanh toán | `BookingService.update_booking('collect'/'refund')` |
| UC08 Cập nhật hồ sơ | 5 | Khách | Thông tin cá nhân | `accounts_route('/api/profile')` |

Sáu form nghiệp vụ gồm biên tập tour, lịch khởi hành, đặt chuyến đi, xử lý đơn, thanh toán và thông tin cá nhân. Trong đó, biên tập tour và hồ sơ có thể tính là form đơn giản, chiếm 2/6. Khách chưa đăng nhập có thể xem tour đang mở bán. Vai trò lấy từ phiên phía Worker. Khách chỉ đọc đơn của mình. Admin đọc toàn bộ đơn để xử lý và không thể đặt tour bằng tài khoản admin.

### Hai giao dịch phức hợp

1. **Đặt tour và giữ chỗ (UC03).** Máy chủ kiểm vai trò, ngày, số khách, tour đang mở bán và số chỗ. Repository lấy giá niêm yết, áp dụng chính sách giá và ghi giá chốt vào đơn. Câu INSERT kiểm tra lại giá niêm yết chưa đổi. Trigger tăng số chỗ đã giữ ở đợt tương ứng trong cùng câu lệnh. Khi chỗ đã hết, yêu cầu sau không tạo thêm đơn.
2. **Hủy đơn và trả chỗ (UC06).** Câu lệnh kiểm tra trạng thái, thanh toán và chủ đơn khi người dùng là khách. Trigger trả chỗ về lịch khởi hành trong cùng câu lệnh. Hủy lại không trả chỗ lần thứ hai. Nếu cập nhật bị lỗi, thay đổi ở cả đơn và đợt đều được hoàn tác.

### Cách kiểm chứng

- `npm test` với Python 3.12. Bộ kiểm thử đi qua Worker với SQLite tạm, gồm tranh chỗ, quyền hai vai trò, trạng thái, giá lịch sử và lỗi giữa lúc giữ chỗ.
- Demo qua UI trên môi trường cục bộ: admin tạo tour và đợt, khách đặt, admin mở phiếu xác nhận/thu và hoàn, admin hủy, khách thấy chỗ được trả lại. Khi khách khác mở Hành trình của tôi, đơn của khách đặt không xuất hiện.
- Tệp triển khai D1 nằm ở `Database/0001_tour_operations.sql` và `Database/0002_initial_catalog.sql`. Dữ liệu nghiệp vụ từ localStorage của bản cũ cần được rà soát trước khi chuyển sang CSDL dùng chung.

## 1.2 — Master–Detail, bộ lọc và báo cáo

- **Quản lý tour → Sửa tour** tự nạp các điểm ghé và hoạt động theo ngày. Đổi số ngày cập nhật số dòng chi tiết. Lưu tour và các dòng chi tiết trong một batch D1. Mở lại để kiểm tra danh sách đã lưu.
- **Xử lý đơn / Thu tiền → Mở phiếu** nạp lịch sử thu và hoàn của đúng đơn. Phiếu hiển thị số khách, giá lịch sử, thu ròng và phần còn phải thu. Ghi thu hoặc hoàn tạo sự kiện trong cùng giao dịch với cập nhật đơn.
- **Báo cáo** có dòng tiền theo tháng, tình hình đặt tour theo trạng thái và sức chứa từng đợt. Có biểu đồ dòng tiền, ngày bắt đầu/kết thúc, lọc theo tour và nút xóa lọc. Chọn **Tải Excel** hoặc **Tải CSV** để lưu tệp. Dùng **In / Lưu PDF** và chọn **Lưu dưới dạng PDF** trong hộp thoại trình duyệt. Các định dạng dùng cùng dữ liệu với bảng đang xem.

Dòng tiền lọc theo ngày ghi nhận. Hai báo cáo còn lại lọc theo ngày khởi hành. Đơn quá hạn là đơn còn chờ xác nhận sau ngày đi. Đơn hoàn thành là đơn đã xác nhận, đã thu và đã qua ngày đi. Đơn hủy hiện thành dòng trạng thái riêng để đối chiếu. Dòng tổng không cộng đơn hủy, và đơn hủy không giữ chỗ. Nếu áp migration vào dữ liệu 1.1 đã có thu tiền, số dư mở đầu mang ngày migration vì dữ liệu cũ không ghi ngày thu.

## 1.3 — Seed, quan hệ và số đối chiếu

`scripts/demo_data.py` tạo bộ mẫu liên thông từ khóa ngoại thật. `python3 -m scripts.demo` nạp tự động vào SQLite tạm. Dùng `python3 -m scripts.seed_demo mingo-demo.sql` để tạo SQL cho D1 cục bộ mới. Mỗi bộ seed có 236 dòng nghiệp vụ ngoài danh mục khởi tạo trong migration 0002.

| Bảng | Số dòng mẫu |
| --- | ---: |
| Tài khoản | 8 |
| Tour | 3 |
| Điểm đến | 6 |
| Lịch trình tour | 6 |
| Đợt khởi hành | 18 |
| Đơn đặt | 126 |
| Phiếu thu và hoàn | 69 |

Mỗi tour có đợt ở ba tháng đã qua, tháng hiện tại và hai tháng tới. Bộ mẫu có đơn nhiều người lớn và trẻ em, đơn hủy trước khi thu, đơn hủy đã hoàn tiền và đợt kín chỗ. Khi lọc **Hà Nội – Phố cổ và Hồ Gươm** trong tháng liền trước, báo cáo hiện các số sau.

- Giá 1.200.000 ₫/khách. Thu hai khách ở đơn hoàn thành và một khách ở đơn hủy có hoàn tiền. Tổng thu 3.600.000 ₫, hoàn 1.200.000 ₫, thu ròng 2.400.000 ₫.
- Bảng chi tiết có bốn đơn, bảy khách gồm hai khách hoàn thành, một khách hủy, hai khách quá hạn và hai khách xác nhận chưa thu. Dòng tổng không gồm đơn hủy là ba đơn, sáu khách.
- Có tám chỗ, sáu chỗ đã giữ và hai chỗ trống. Tháng sau cùng tour chỉ còn một chỗ.

Khi lọc tour Hà Nội ở tháng thứ ba trước tháng hiện tại, có 10 đơn gồm 27 khách. Hai đơn hủy gồm ba khách nên còn 24 khách giữ chỗ trên 30 chỗ. Thu 12 lượt khách và hoàn một lượt khách, tương ứng **14.400.000 ₫ thu**, **1.200.000 ₫ hoàn** và **13.200.000 ₫ thu ròng**.

`tests/test_operations.py` so sánh các con số này với API, kiểm tra khóa ngoại, quyền xem báo cáo và thay đổi báo cáo ngay sau ghi thu/hoàn.

## 1.4 — Bàn giao và kiểm tra

- Xem [README](../README.md) để chạy bản demo, đăng nhập, tạo lại dữ liệu mẫu và chạy kiểm thử.
- `python3 -m scripts.package_demo mingo-demo.zip` đóng gói nguồn và tài nguyên. Giải nén rồi chạy `python3 -m scripts.demo` bằng Python 3.12. Máy chấm cần sẵn Python 3.12 và trình duyệt. Bản demo dùng dữ liệu tạm, dựng lại mỗi khi khởi động.
- Tiêu chí ≥12 commit có nội dung qua ≥3 tuần cần đánh giá theo lịch sử làm việc thực tế.
