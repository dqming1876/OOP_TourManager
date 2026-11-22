# Minh chứng 1.2 — Master–Detail, bộ lọc và báo cáo

| Hạng mục | Minh chứng | Cách kiểm chứng |
| --- | --- | --- |
| Master–Detail tour và lịch trình | **Quản lý tour → Sửa tour** nạp điểm ghé và hoạt động theo ngày. Tour và các dòng chi tiết lưu trong một batch D1. | Đổi số ngày, điền các dòng tương ứng, lưu rồi mở lại tour. |
| Master–Detail đơn và bút toán | **Xử lý đơn / Thu tiền → Mở phiếu** hiển thị số khách, giá chốt, lịch sử thu và hoàn, thu ròng và số còn phải thu. | Mở phiếu từ hai danh sách, ghi thu hoặc hoàn rồi kiểm tra dòng phát sinh và tổng tiền. |
| Lọc đa tiêu chí | Báo cáo lọc theo ngày và tour. Trang **Lữ trình** lọc theo vùng, giá, thời lượng và có nút **Xóa lọc**. | Đổi nhiều tiêu chí, kiểm kết quả rồi dùng **Xóa lọc** để về mặc định. |
| Báo cáo | Ba báo cáo gồm dòng tiền theo tháng, đơn theo trạng thái và sức chứa đợt. Báo cáo dòng tiền kèm biểu đồ thu và hoàn. | So sánh kết quả với [ca đối chiếu tính tay](checklist-5.2.md). |
| Tệp xuất | XLSX, CSV và bản in PDF dùng dữ liệu từ báo cáo đang xem. [Tệp XLSX kiểm chứng](evidence/report-export.xlsx) dùng dữ liệu tổng hợp và được đọc lại bằng openpyxl. | Chọn **Tải Excel**, **Tải CSV** hoặc **In / Lưu PDF**. Đối chiếu tiêu đề, ngày xuất, phạm vi, chữ tiếng Việt và tổng cộng. |

Dòng tiền lọc theo ngày ghi nhận. Hai báo cáo còn lại lọc theo ngày khởi hành. Đơn quá hạn là đơn còn chờ xác nhận sau ngày đi. Đơn hoàn thành là đơn đã xác nhận, đã thu và đã qua ngày đi. Đơn hủy hiện thành dòng riêng để đối chiếu, được loại khỏi dòng tổng và không giữ chỗ. Nếu áp migration vào dữ liệu đã có thu tiền, số dư mở đầu mang ngày migration khi ngày thu gốc không có trong dữ liệu.
