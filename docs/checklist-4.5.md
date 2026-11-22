# Minh chứng 4.5 — SRP, ISP, DIP và tiêm phụ thuộc

| Thành phần | Một trách nhiệm |
| --- | --- |
| `TourCatalogService` | Điều phối vòng đời danh mục tour và các đợt khởi hành. |
| `BookingService` | Điều phối giữ chỗ, phạm vi phiếu và chuyển trạng thái thu/hoàn/hủy. |
| `ReportsService` | Kiểm bộ lọc và quyền trước khi lấy báo cáo. |
| `LoginRateLimiter` | Giới hạn thử đăng nhập theo IP, lưu qua port dùng chung. |
| `DestinationsService` | Kiểm dữ liệu, quyền và phiên bản chỉnh sửa danh mục dùng chung. |
| `AccountsService` | Xác thực và cập nhật danh tính/hồ sơ tài khoản. |
| `AccessPolicy` | Áp dụng phạm vi của tài khoản và yêu cầu vai trò. |
| `operations_route` | Chuyển phương thức và đường dẫn HTTP thành lời gọi Service. |
| `BookingRepository` và `TourCatalogRepository` | Lưu dữ liệu đơn và danh mục tương ứng bằng câu SQL tham số hóa. |

## Hợp đồng chuyên biệt

| Port | Bên tiêu thụ | Bên cung cấp |
| --- | --- | --- |
| `Database` — bốn phương thức (`first`, `all`, `execute`, `batch`) | Các lớp Repository | `D1Database` (Cloudflare) hoặc `SQLiteDatabase` (demo/test) |
| `BookingPort` — bốn phương thức | `BookingService` | `BookingRepository` hoặc bản in-memory |
| `TourCatalogPort` — sáu phương thức | `TourCatalogService` | `TourCatalogRepository` |
| `ReportsPort` — chỉ `load(start, end, tour_id, today)` | `ReportsService` | `ReportsRepository` |
| `AccountsPort` — bảy phương thức tài khoản, admin & rate limit | `AccountsService`, `LoginRateLimiter` | `AccountsRepository` |
| `DestinationsPort` — ba phương thức (`list_entries`, `save_entry`, `remove_entry`) | `DestinationsService` | `DestinationsRepository` |

Các hợp đồng dùng kiểu cấu trúc qua `typing.Protocol`. Service nhận port qua constructor và instance kho được tạo ở `Application()`. Route nhận Service đã lắp. Clock ngày Việt Nam được truyền tại root, `LoginRateLimiter` lưu bộ đếm dùng chung trong D1; service nhận địa chỉ IP đã trích xuất ở HTTP boundary. [Port](../backend/ports.py) · [Composition Root](../entry.py)

## Thử đổi DAL

Test 4.5 lắp `Application(repositories=..., today=...)` với BookingPort in-memory, qua cùng đường dẫn HTTP. POST đặt 3 khách trả 201, GET đơn trả đúng mã vừa tạo. BookingService, route, DTO và lớp miền dùng nguyên code. Bản demo thật dùng repository D1 với adapter SQLite, bộ test chạy thêm cả schema và trigger. [Kiểm thử](../tests/test_architecture.py)

Tách port khiến việc kiểm thử không phụ thuộc binding DB, đổi lại cần giữ hợp đồng giữa các adapter và kiểm tra riêng các tính chất như giao dịch hoặc cập nhật đồng thời ở backend thật.
