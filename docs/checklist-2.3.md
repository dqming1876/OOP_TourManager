# Minh chứng 2.3 — Hiệu năng, cấu hình ngoài và tái lập

| Tiêu chí | Minh chứng |
| --- | --- |
| Lọc và tổng hợp | **Quản trị → Báo cáo** lọc theo ngày và tour. Có ba báo cáo về thu/hoàn, tình hình đặt tour và sức chứa. Giao diện tải bất đồng bộ, hiển thị tiến trình và bỏ qua phản hồi cũ khi yêu cầu mới chạy. |
| Tránh N+1 | [ReportsRepository](../backend/repositories.py) dùng một batch với ba truy vấn cố định, có JOIN và tổng hợp trong D1. [TourCatalogRepository](../backend/repositories.py) ghép tour, lịch và điểm ghé với ba truy vấn cố định. Trang tra cứu chỉ dựng 12 thẻ kết quả đầu và tăng theo nút Xem thêm. |
| Chỉ mục | [0004_report_indexes.sql](../Database/0004_report_indexes.sql) tạo chỉ mục theo ngày cho đơn và lịch. Bộ test kiểm tra `EXPLAIN QUERY PLAN` dùng `bookings_report_by_day`. |
| Cấu hình | [wrangler.example.jsonc](../wrangler.example.jsonc) định nghĩa binding D1 và thư mục migration. [.dev.vars.example](../.dev.vars.example) liệt kê biến cấu hình quản trị. Worker nhận DB qua `env.DB`. Đổi ID D1 trong cấu hình và giữ tên binding `DB`. |

## Kết quả cục bộ

- `npm test` tạo **120 đơn**, đo **30 lượt** lọc ngày và tour, xác minh mỗi lượt trả 60 đơn xác nhận và 60 khách. Phân tích truy vấn xác nhận ba câu lệnh cố định và index theo ngày. P95 được in khi chạy test, chỉ gồm Worker/SQLite nội bộ.
- Kiểm tra DOM mô phỏng trên 120 tour: màn hình khởi tạo dựng 12 thẻ, sau Xem thêm dựng 24. Báo cáo hiển thị số liệu trả về từ Worker; các nút xuất tải đúng trạng thái.
- Tạo D1 cục bộ và kiểm tra bundle bằng Wrangler. Cách đổi cấu hình và tái lập dữ liệu có trong [README](../README.md).

Tài liệu đối chiếu: [Cloudflare D1 Database](https://developers.cloudflare.com/d1/worker-api/d1-database/) và [Workers local secrets](https://developers.cloudflare.com/workers/local-development/environment-variables/).
