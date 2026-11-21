# Minh chứng 4.5 — SRP, ISP, DIP và tiêm phụ thuộc

| Thành phần | Một trách nhiệm |
| --- | --- |
| `TourCatalogService` | Điều phối vòng đời danh mục tour và các đợt khởi hành. |
| `BookingService` | Điều phối giữ chỗ, phạm vi phiếu và chuyển trạng thái thu/hoàn/hủy. |
| `ReportsService` | Kiểm bộ lọc và quyền trước khi lấy báo cáo. |
| `AccountsService` | Xác thực và cập nhật danh tính/hồ sơ tài khoản. |
| `AccessPolicy` | Áp dụng phạm vi của tài khoản và yêu cầu vai trò. |
| `OperationsRoute` | Chuyển phương thức và đường dẫn HTTP thành lời gọi Service. |
| `BookingRepository` và `TourCatalogRepository` | Lưu dữ liệu đơn và danh mục tương ứng bằng câu SQL tham số hóa. |

## Hợp đồng chuyên biệt

| Port | Bên tiêu thụ | Bên cung cấp |
| --- | --- | --- |
| `BookingPort` — bốn phương thức | BookingService | BookingRepository hoặc bản in-memory |
| `TourCatalogPort` — sáu phương thức | TourCatalogService | TourCatalogRepository |
| `ReportPort` — chỉ `load(filter)` | ReportsService | ReportsRepository |
| `AccountsPort` — bốn phương thức tài khoản | AccountsService | AccountsRepository |

Các hợp đồng JSDoc dùng kiểu cấu trúc. Service nhận port qua constructor và instance kho được tạo ở `createWorker()`. Route nhận Service đã lắp. Clock ngày Việt Nam được truyền tại root, bộ đếm đăng nhập ở cùng vòng đời Worker do root cấp xuống AccountsService. [Port](../worker/ports.js) · [Composition Root](../worker/index.js)

## Thử đổi DAL

Test 4.5 lắp `createWorker({ repositories, today })` với BookingPort in-memory, qua cùng đường dẫn HTTP. POST đặt 3 khách trả 201, GET đơn trả đúng mã vừa tạo. BookingService, route, DTO và lớp miền dùng nguyên code. Bản demo thật dùng repository D1 với adapter SQLite, bộ test chạy thêm cả schema và trigger. [Kiểm thử](../test/architecture.test.js)

Tách port khiến việc kiểm thử không phụ thuộc binding DB, đổi lại cần giữ hợp đồng giữa các adapter và kiểm tra riêng các tính chất như giao dịch hoặc cập nhật đồng thời ở backend thật.
