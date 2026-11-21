# Mingo — Phạm vi và minh chứng mục 1.1

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
| UC01 Quản lý tour | 1 | Admin | Quản lý tour → biên tập tour | `TourOperations.saveTour/setVisibility` |
| UC02 Quản lý lịch | 2 | Admin | Lịch khởi hành → chọn tour và lưu đợt | `TourOperations.saveDeparture/removeDeparture` |
| UC03 Đặt tour và giữ chỗ | 3 | Khách | Chi tiết tour → form đặt chuyến đi | `TourOperations.placeBooking` |
| UC04 Xem đơn của mình | 3 | Khách | Hành trình của tôi | `TourOperations.bookings` |
| UC05 Xác nhận đơn | 3 | Admin | Xử lý đơn → phiếu xử lý đơn | `TourOperations.updateBooking('confirm')` |
| UC06 Hủy đơn và trả chỗ | 3 | Khách với đơn chờ của mình, hoặc Admin với đơn chưa thu tiền | Hành trình của tôi hoặc phiếu xử lý đơn | `TourOperations.updateBooking('cancel')` |
| UC07 Ghi nhận thu hoặc hoàn | 4 | Admin | Thu tiền / hoàn tiền → phiếu thanh toán | `TourOperations.updateBooking('collect'/'refund')` |
| UC08 Cập nhật hồ sơ | 5 | Khách | Thông tin cá nhân | `accountsRoute('/api/profile')` |

Sáu form nghiệp vụ gồm biên tập tour, lịch khởi hành, đặt chuyến đi, xử lý đơn, thanh toán và thông tin cá nhân. Trong đó, biên tập tour và hồ sơ có thể tính là form đơn giản, chiếm 2/6. Khách chưa đăng nhập có thể xem tour đang mở bán. Vai trò lấy từ phiên phía Worker. Khách chỉ đọc đơn của mình. Admin đọc toàn bộ đơn để xử lý và không thể đặt tour bằng tài khoản admin.

## Hai giao dịch phức hợp

1. **Đặt tour và giữ chỗ (UC03).** Máy chủ kiểm vai trò, ngày, số khách, tour đang mở bán và số chỗ. Câu lệnh thêm đơn lấy giá hiện tại từ tour và ghi giá lịch sử vào đơn. Trigger tăng số chỗ đã giữ ở đợt tương ứng trong cùng câu lệnh. Khi chỗ đã hết, yêu cầu sau không tạo thêm đơn.
2. **Hủy đơn và trả chỗ (UC06).** Câu lệnh kiểm tra trạng thái, thanh toán và chủ đơn khi người dùng là khách. Trigger trả chỗ về lịch khởi hành trong cùng câu lệnh. Hủy lại không trả chỗ lần thứ hai. Nếu cập nhật bị lỗi, thay đổi ở cả đơn và đợt đều được hoàn tác.

## Cách kiểm chứng

- `node scripts/build-cloudflare.mjs && node --test test/operations.test.js` với Node.js 24. Bộ kiểm thử đi qua Worker với SQLite tạm, gồm tranh chỗ, quyền hai vai trò, trạng thái, giá lịch sử và lỗi giữa lúc giữ chỗ.
- Demo qua UI trên môi trường cục bộ: admin tạo tour và đợt, khách đặt, admin mở phiếu xác nhận/thu và hoàn, admin hủy, khách thấy chỗ được trả lại. Khi khách khác mở Hành trình của tôi, đơn của khách đặt không xuất hiện.
- Tệp triển khai D1 nằm ở `drizzle/0001_tour_operations.sql` và `drizzle/0002_initial_catalog.sql`. Dữ liệu nghiệp vụ từ localStorage của bản cũ cần được rà soát trước khi chuyển sang CSDL dùng chung.
