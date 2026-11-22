# Minh chứng 1.1 — Chức năng và phân quyền

Đề tài nhóm 1 người MI4090. Mingo quản lý từ khi mở tour đến khi khách giữ chỗ và quản trị xử lý phiếu. Tiền thu và hoàn được ghi nhận thủ công trong đồ án.

## BFD

| Cấp 1 | Cấp 2 | Cấp 3 |
| --- | --- | --- |
| Mingo | 1. Danh mục tour | Thêm hoặc sửa tour, ẩn hoặc hiện, tra cứu tour |
| Mingo | 2. Lịch khởi hành | Mở đợt, đổi sức chứa, xem số chỗ, xóa đợt chưa từng có đơn |
| Mingo | 3. Đặt và xử lý đơn | Đặt giữ chỗ, xem đơn, xác nhận, hủy trả chỗ |
| Mingo | 4. Thanh toán | Ghi nhận thu tiền, ghi nhận hoàn tiền |
| Mingo | 5. Hồ sơ khách | Xem và cập nhật thông tin liên hệ của chính mình |

## Use case, form và phân quyền

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
| UC13 Quản lý địa danh và đặc sản | 1 | Admin | Điểm đến → `frm009_dm_diem_den` | `DestinationsService.save/remove` |

Các form chính gồm biên tập tour, lịch khởi hành, đặt chuyến đi, xử lý đơn, thanh toán, hồ sơ khách, báo cáo và địa danh. Form `frm009_dm_diem_den` ghi danh mục dùng chung lên D1 qua `/api/ops/destinations` và kiểm tra `version` khi sửa hoặc xóa. Xem [bản đồ các form](checklist-3.1.md).

Bảng `accounts` tham chiếu `roles`. Hệ thống khởi tạo admin một lần từ cấu hình rồi đọc tài khoản và vai trò từ DB khi đăng nhập hoặc xác thực phiên. Khách chưa đăng nhập xem được tour đang bán. Khách đăng nhập chỉ đọc đơn của mình. Admin đọc toàn bộ đơn để xử lý và quyền đặt tour thuộc vai trò khách.

## Ba giao dịch phức hợp

1. **Đặt tour và giữ chỗ (UC03).** Máy chủ kiểm vai trò, ngày, số khách, tour đang mở bán và số chỗ. Câu lệnh thêm đơn lấy giá hiện tại từ tour và ghi giá lịch sử vào đơn. Trigger tăng số chỗ đã giữ ở đợt tương ứng trong cùng câu lệnh. Khi chỗ đã hết, yêu cầu sau không tạo thêm đơn.
2. **Hủy đơn và trả chỗ (UC06).** Câu lệnh kiểm tra trạng thái, thanh toán và chủ đơn khi người dùng là khách. Trigger trả chỗ về lịch khởi hành trong cùng câu lệnh. Hủy lại không trả chỗ lần thứ hai. Nếu cập nhật bị lỗi, thay đổi ở cả đơn và đợt đều được hoàn tác.
3. **Thu hoặc hoàn tiền (UC07).** Cập nhật trạng thái thanh toán trên đơn và ghi phát sinh vào `payment_events` trong cùng giao dịch. Giao dịch lỗi giữ nguyên trạng thái thanh toán và sổ tiền.

## Cách kiểm chứng

- `npm test` với Python 3.12. Bộ kiểm thử đi qua Worker với SQLite tạm, gồm tranh chỗ, quyền hai vai trò, trạng thái, giá lịch sử và lỗi giữa lúc giữ chỗ.
- Demo qua UI trên môi trường cục bộ: admin tạo tour và đợt, khách đặt, admin mở phiếu xác nhận/thu và hoàn, admin hủy, khách thấy chỗ được trả lại. Khi khách khác mở Hành trình của tôi, đơn của khách đặt không xuất hiện.
- Xem [migration nghiệp vụ và danh mục](../Database) và [kiểm chứng quyền và phiên bản khi sửa địa danh](checklist-5.2.md).
