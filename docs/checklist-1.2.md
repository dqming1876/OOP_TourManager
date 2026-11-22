# Minh chứng 1.2 — Master–Detail, bộ lọc và báo cáo

- **Quản lý tour → Sửa tour** tự nạp các điểm ghé và hoạt động theo ngày. Đổi số ngày cập nhật số dòng chi tiết. Lưu tour và các dòng chi tiết trong một batch D1. Mở lại để kiểm tra danh sách đã lưu.
- **Xử lý đơn / Thu tiền → Mở phiếu** nạp lịch sử thu và hoàn của đúng đơn. Phiếu hiển thị số khách, giá lịch sử, thu ròng và phần còn phải thu. Ghi thu hoặc hoàn tạo sự kiện trong cùng giao dịch với cập nhật đơn.
- **Báo cáo** có dòng tiền theo tháng, tình hình đặt tour theo trạng thái và sức chứa từng đợt. Có biểu đồ dòng tiền, ngày bắt đầu/kết thúc, lọc theo tour và nút xóa lọc. Chọn **Tải Excel** để lưu XLSX hoặc **In / Lưu PDF** và chọn **Lưu dưới dạng PDF** trong hộp thoại trình duyệt. Hai bản xuất dùng cùng dữ liệu với bảng đang xem.

Dòng tiền lọc theo ngày ghi nhận. Hai báo cáo còn lại lọc theo ngày khởi hành. Đơn quá hạn là đơn còn chờ xác nhận sau ngày đi. Đơn hoàn thành là đơn đã xác nhận, đã thu và đã qua ngày đi. Đơn hủy hiện thành dòng trạng thái riêng để đối chiếu. Dòng tổng không cộng đơn hủy, và đơn hủy không giữ chỗ. Nếu áp migration vào dữ liệu 1.1 đã có thu tiền, số dư mở đầu mang ngày migration vì dữ liệu cũ không ghi ngày thu.
