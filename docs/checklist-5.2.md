# Minh chứng 5.2 — CSDL kiểm thử, rollback, báo cáo và RBAC

Chạy `python3 -m unittest tests.test_integration_axis5`. Phần đối chiếu trình bày chạy bằng `node --test tests/frontend/*.test.js`. Mỗi ca dựng một SQLite trong bộ nhớ, áp toàn bộ migration và nạp fixture riêng. Adapter chạy cùng SQL, ràng buộc, trigger và Service ứng dụng. Sau mỗi ca, DB trong bộ nhớ được đóng.

| Ca | Rule và tầng thực thi | Kết quả đã xác minh |
| --- | --- | --- |
| IT-01 | R01–R02 · Worker → BookingService → `INSERT ... SELECT` → trigger `reserve_booking_seats` | Đặt đúng ba chỗ cuối trả 201, có một đơn chờ với giá chốt 500.000 ₫/khách, lịch giữ đúng 3 chỗ. Yêu cầu đặt tiếp nhận 409. |
| IT-02 | R02 · Trigger thử nghiệm trên bước UPDATE `departures.reserved` | Lỗi ném sau khi đã vào trigger của INSERT đơn. API báo 500, số đơn = 0 và sức chứa giữ nguyên 3 với 0 chỗ đã giữ. Bỏ trigger thử nghiệm rồi chạy lại nhận 201. |
| IT-03 | R09/R11 · ReportsService → ReportsRepository → Strategy hiển thị | Bao gồm hai biên ngày, bỏ ngày đứng ngoài và tour khác. Thu, hoàn, ròng khớp giá trị tính tay. Dòng tổng đơn bỏ đơn hủy, còn dòng chi tiết giữ đơn hủy để đối chiếu. |
| IT-04 | R05–R07 · Gọi BookingService và ReportsService trực tiếp | Khách thu tiền hoặc đọc báo cáo nhận 403 và không mở câu SQL. Khách khác hủy đơn chờ nhận 409. Đơn, chỗ giữ và sổ tiền không thay đổi. |

## IT-03 — Đối chiếu tính tay

Tour báo cáo, kỳ **10–12/05/2028**. Dữ liệu cụ thể được dựng ở [bộ kiểm thử](../tests/test_integration_axis5.py).

| Ngày | Sự kiện của tour được chọn | Tính vào báo cáo |
| --- | --- | --- |
| 09/05 | Thu một phiếu 400.000 ₫ | Trước biên, loại |
| 10/05 | Thu phiếu hai khách × 750.000 ₫ | Thu 1.500.000 ₫, 1 đơn, 2 khách, giữ 2 chỗ |
| 11/05 | Thu phiếu một khách sẽ hủy, 1.000.000 ₫ | Ghi dòng tiền thu 1.000.000 ₫ |
| 11/05 | Thu 900.000 ₫ thuộc tour khác | Loại theo mã tour |
| 12/05 | Hoàn 1.000.000 ₫ cho phiếu hủy, đồng thời có phiếu chờ ba khách | Ghi dòng tiền hoàn 1.000.000 ₫; tổng đơn thêm 1 đơn chờ và 3 khách, phiếu hủy ghi riêng và không giữ chỗ |
| 13/05 | Thu phiếu 600.000 ₫ | Sau biên, loại |

Tổng thu **2.500.000 ₫**, hoàn **1.000.000 ₫**, thu ròng **1.500.000 ₫**. Dòng tổng gồm **2 đơn, 5 khách**. Dòng hủy riêng có 1 đơn và 1 khách. Hai đợt có sức chứa 6, lần lượt còn **4** và **3** chỗ. Nếu lọc đúng ngày 12/05, thu bằng 0 và hoàn 1.000.000 ₫. Đây là dòng tiền theo ngày ghi nhận, nên khoản hoàn trong kỳ vẫn xuất hiện khi khoản thu gốc ở kỳ khác.

Kết quả được đối chiếu trực tiếp cả tại SQL và qua [Strategy đang dùng để dựng bảng và tệp xuất](../dist/report-strategies.js).
