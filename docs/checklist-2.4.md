# Minh chứng 2.4 — Tổ chức mã nguồn và quy ước đặt tên

| Tầng | Thư mục | Vai trò |
| --- | --- | --- |
| GUI | [dist/](../dist/) | HTML/CSS, luồng khách và quản trị, validation tại form |
| API | [backend/app.py](../backend/app.py) | Điều hướng HTTP, đọc yêu cầu và trả lỗi |
| BLL | [backend/services.py](../backend/services.py) | Nghiệp vụ tour, tài khoản, xác thực và phiên |
| DAL | [backend/repositories.py](../backend/repositories.py) | Repository tài khoản, tour và báo cáo |
| Domain | [backend/domain.py](../backend/domain.py) | Quy tắc đầu vào và cây lỗi |
| Database | [Database/](../Database/) | Migration và dữ liệu danh mục khởi tạo |
| Resource | [dist/Resource/](../dist/Resource/) | Dữ liệu địa danh dùng ở giao diện |

## Quy ước

- ID form theo nhóm chức năng, ví dụ `frm000_dang_nhap`, `frm001_dm_tour`, `frm002_nv_lich_khoi_hanh`, `frm003_nv_dat_tour` và `frm007_bc_don_dat`. Có thể kiểm tra ID trên DOM khi mở màn hình tương ứng.
- Module Python, phương thức và biến dùng `snake_case`; lớp dùng `PascalCase` như `BookingService`. JavaScript giao diện giữ `camelCase`.
- Điểm vào thực tế là [entry.py](../entry.py). Python Worker nạp các module của backend qua import.
- `app.js` tải danh mục từ `/api/ops/tours`, dùng một điểm render và một hàm lọc. `dist/` chứa tài nguyên ứng dụng, `Database/` chứa các migration theo thứ tự áp dụng. `index.html` và `style.css` thụt lề 2 khoảng trắng.

Kiểm tra bằng `npm run build`, `npm test` và `node --check` cho mã frontend.
