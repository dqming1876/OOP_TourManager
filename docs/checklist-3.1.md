# Minh chứng 3.1 — Khảo sát, BFD, use case và mã nguồn

## Khảo sát 4W+1H

| Câu hỏi | Quan sát và quyết định thiết kế |
| --- | --- |
| Who — Ai sử dụng? | Người đặt cung cấp tên và số điện thoại, chọn chuyến và theo dõi phiếu. Quản trị viên mở lịch, kiểm tra đơn và ghi thu/hoàn. Vai trò được kiểm ở phiên và Service. |
| What — Xử lý gì? | Danh mục tour, lịch khởi hành, số người lớn/trẻ em, phiếu đặt và lịch sử thanh toán. Mingo lưu ngày đi và giá chốt trên đơn. |
| When — Khi nào? | Sau khi chọn chuyến, khách gửi thông tin đặt. Mingo giữ chỗ khi nhận đơn và cho admin xác nhận đến hết ngày khởi hành theo giờ Việt Nam. |
| Where — Ở đâu? | Khách dùng trang Lữ trình và Hành trình của tôi. Admin vào khu Quản trị để xử lý đơn, lập lịch và xem báo cáo. |
| How — Thực hiện thế nào? | Chọn tour và ngày → ghi thông tin đại diện và số người → tạo phiếu chờ nếu còn chỗ → admin mở phiếu và xác nhận → ghi thu hoặc hoàn khi có giao dịch. |

Đối chiếu với biểu mẫu đặt tour đang công khai. Vietnam Tourist có họ tên, điện thoại và ngày khởi hành. Sài Gòn Tourism có lựa chọn khởi hành, thông tin liên hệ và nhóm khách. Vietravel mô tả luồng xem lịch trình, bấm đặt và điền form. Mingo tự đặt quy tắc giữ chỗ, xác nhận và ghi nhận tiền cho phạm vi đồ án. Khảo sát dựa trên biểu mẫu web công khai, không có phỏng vấn. [Vietnam Tourist](https://vietnamtouristvn.com/dat-tour) · [Sài Gòn Tourism](https://sgtourism.com.vn/gio-hang.html) · [Hướng dẫn Vietravel](https://vietravel.com/vn/tin-tuc-du-lich/huong-dan-dat-tour-du-lich-vietravel-voi-6-buoc-don-gian-v14344.aspx)

## BFD ba cấp và ánh xạ xuôi

Cấp 1 là **F1 Mingo**. Bảng ghi đủ năm nhánh cấp 2, gồm ba nhánh dùng chung và hai nhánh đặc thù quản lý tour. Mỗi nút lá trỏ đến màn hình hoặc Form cụ thể và hàm phục vụ. Các UC mở rộng được gộp theo Form khi dùng cùng giao diện.

| Cấp 2 | Nút lá cấp 3 | UC và vai trò | Menu → Form hoặc màn hình | Hàm xử lý |
| --- | --- | --- | --- | --- |
| F1.1 Danh mục (chung) | F1.1.1 Tra cứu tour | UC09 khách, admin | Lữ trình → `frm010_dm_tra_cuu_tour` | `TourCatalogService.catalog`, sau đó `filterTours` lọc dữ liệu đã tải |
| F1.1 Danh mục (chung) | F1.1.2 Quản lý tour | UC01 admin | Quản trị → Quản lý tour → `frm001_dm_tour` | `submitTour` → `save_tour`. Nút Ẩn/Hiện trong màn hình danh mục gọi `set_visibility`. |
| F1.2 Tài khoản (chung) | F1.2.1 Đăng nhập | UC10 khách, admin | Đăng nhập → `frm000_dang_nhap` | `login` → `accounts_route` → `loginAccount` |
| F1.2 Tài khoản (chung) | F1.2.2 Đăng ký | UC11 khách | Đăng nhập → Tạo tài khoản → `frm008_dang_ky` | `registerAccount` ở UI và Worker |
| F1.2 Tài khoản (chung) | F1.2.3 Cập nhật liên hệ | UC08 khách | Tài khoản → `frm006_nv_ho_so` | `saveProfile` → `saveCustomerProfile` |
| F1.3 Báo cáo (chung) | F1.3.1 Lọc/xuất báo cáo | UC12 admin | Quản trị → Báo cáo → `frm007_bc_don_dat` | `loadReport` → `ReportsService.load`; xuất tệp từ kết quả đang xem |
| F1.4 Lịch khởi hành (riêng) | F1.4.1 Quản lý đợt | UC02 admin | Quản trị → Lịch khởi hành → `frm002_nv_lich_khoi_hanh` | `submitDeparture` → `saveDeparture`; nút Xóa gọi `remove_departure` |
| F1.5 Đơn tour và thanh toán (riêng) | F1.5.1 Đặt giữ chỗ | UC03 khách | Chi tiết tour → `frm003_nv_dat_tour` | `placeOrder` → `BookingService.place_booking` |
| F1.5 Đơn tour và thanh toán (riêng) | F1.5.2 Xem/hủy đơn của mình | UC04, UC06 khách | Hành trình của tôi → `frm011_nv_don_cua_toi` / `bookingDetail` | `BookingService.bookings`; `performBookingAction` → `update_booking` |
| F1.5 Đơn tour và thanh toán (riêng) | F1.5.3 Xử lý phiếu | UC05, UC06 admin | Quản trị → Xử lý đơn → `frm004_nv_xu_ly_don` | `editBooking` / `submitBookingAction` → `payment_history` / `update_booking` |
| F1.5 Đơn tour và thanh toán (riêng) | F1.5.4 Thu/hoàn | UC07 admin | Quản trị → Thu tiền / hoàn tiền → `frm005_nv_thanh_toan` | `submitBookingAction` → `update_booking` → trigger ghi `payment_events` |

UC01–UC08 giữ mã của minh chứng 1.1. UC09–UC12 bổ sung tra cứu, đăng nhập, đăng ký và báo cáo. BFD trục 3 nhóm lại các nhánh chung và riêng theo yêu cầu rubric; bảng 1.1 trình bày phạm vi tính năng ban đầu.

Mã giao diện: [app.js](../dist/app.js), [admin.js](../dist/admin.js), [operations.js](../dist/operations.js), [reports.js](../dist/reports.js). Điểm vào tầng HTTP: [app.py](../backend/app.py).

## Ánh xạ ngược từ Form và cột Grid

| Cột / Form | Nguồn dữ liệu ở code | Đọc ngược tới biểu mẫu và BFD |
| --- | --- | --- |
| **Mã / khách** trong Xử lý đơn | Payload `Booking.id / name / phone`, từ `bookings.id / name / phone` | Mã phiếu do hệ thống cấp; họ tên/số điện thoại từ form đặt công khai → `frm003` F1.5.1 → phiếu xử lý F1.5.3 |
| **Chuyến đi** trong Xử lý đơn | `date(b.date)` và `b.people`, DTO từ `bookings.day` và `Booking.people` | Ngày khởi hành và nhóm người lớn/trẻ em → F1.5.1; lịch gốc quản lý ở F1.4.1 |
| **Tổng tiền** trong Xử lý đơn | `Booking.total`, dựa trên giá chốt `bookings.unit_price` | Giá tour trên biểu mẫu, nhân số người theo quy tắc Mingo → F1.5.1; dùng lại khi thu/hoàn F1.5.4 |
| **Ngày đi / Còn trống** trong Lịch khởi hành | `Departure.day / remaining`, từ `departures.day / capacity / reserved` | Ngày chuyến trên form đặt công khai; sức chứa do admin nhập tại F1.4.1 và kiểm lại khi đặt ở F1.5.1 |

## Ví dụ đổi bước quy trình

F1.5.3 nay kiểm tra ngày khởi hành trước khi xác nhận. Phiếu chờ quá ngày đi hiện “Quá hạn xác nhận” và chỉ còn luồng hủy trả chỗ. Điều kiện thực thi ở [Booking.transition](../backend/domain.py) và câu cập nhật của [BookingRepository](../backend/repositories.py), nên request trực tiếp trả 409. [Kiểm thử](../tests/test_operations.py) xác nhận từ chối ở cả API và Service. Nếu thêm bước duyệt có trạng thái lưu riêng, cần đổi DTO/ô trạng thái của `frm004`, luật chuyển của `Booking`, CHECK và migration trước khi cập nhật báo cáo.
