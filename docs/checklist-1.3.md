# Minh chứng 1.3 — Seed, quan hệ và số đối chiếu

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
