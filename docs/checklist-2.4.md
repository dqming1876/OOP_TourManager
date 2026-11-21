# Minh chứng 2.4 — Tổ chức mã nguồn và quy ước đặt tên

| Tầng | Thư mục | Vai trò |
| --- | --- | --- |
| GUI | [dist/](../dist/) | HTML/CSS, luồng khách và quản trị, validation tại form |
| API | [worker/api/](../worker/api/) | Điều hướng HTTP, đọc yêu cầu và trả lỗi |
| BLL | [worker/service/](../worker/service/) | Nghiệp vụ tour, tài khoản, xác thực và phiên |
| DAL | [worker/database/](../worker/database/) | Repository tài khoản, tour và báo cáo |
| Domain | [worker/domain/](../worker/domain/) | Quy tắc đầu vào và cây lỗi |
| Database | [Database/](../Database/) | Migration và dữ liệu danh mục khởi tạo |
| Resource | [dist/Resource/](../dist/Resource/) | Dữ liệu địa danh dùng ở giao diện |

## Quy ước

- ID form theo nhóm chức năng, ví dụ `frm000_dang_nhap`, `frm001_dm_tour`, `frm002_nv_lich_khoi_hanh`, `frm003_nv_dat_tour` và `frm007_bc_don_dat`. Có thể kiểm tra ID trên DOM khi mở màn hình tương ứng.
- File theo `kebab-case`, lớp theo `PascalCase` như `TourOperations`, phương thức và biến theo `camelCase` như `bookingReport`.
- Điểm vào thực tế là [worker/index.js](../worker/index.js). Worker dùng import/export thay cho script ghép nội dung nhiều file. Các script build/preview cũ đã được bỏ.
- Kiểm tra hai file [accounts-route.js](../worker/api/accounts-route.js) và [accounts-service.js](../worker/service/accounts-service.js) để thấy tách biệt HTTP, xác thực và nghiệp vụ. [app.js](../dist/app.js) có một điểm render, một hàm lọc tour và một luồng dựng chi tiết; không còn các lớp ghi đè hàm cũ.

Kiểm tra bằng `npm run build`, `npm test` và `node --check` cho mã frontend.
