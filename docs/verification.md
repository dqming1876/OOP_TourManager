# Kết quả kiểm tra giai đoạn 0

Môi trường kiểm tra: Python 3.14.3, Django 5.2.19, PyMySQL 1.2.4, MySQL Community Server 8.4.7 trên macOS ARM64. MySQL chạy độc lập với database utf8mb4.

- `python manage.py migrate`: thành công với toàn bộ migration Django và 4 migration của project.
- `python manage.py setup_roles`: Admin 76 quyền, Sales 19 quyền, Operator 19 quyền.
- `python manage.py seed_base`: thành công; mật khẩu ngẫu nhiên in khi tạo user lần đầu.
- `python manage.py test accounts bookings --noinput`: 15 kiểm thử đạt; database test được tạo và hủy riêng.
- `python manage.py makemigrations --check --dry-run`: No changes detected.
- `python manage.py check --database default`: không có lỗi.
- `python manage.py showmigrations catalog customers bookings operations`: 4 migration 0001_initial đều đã áp dụng.

Các kiểm thử kiểm tra cả trạng thái bị từ chối: Operator vào trang chỉ dành cho Sales nhận HTTP 403, tài khoản không có vai trò nhận 403, người chưa đăng nhập được chuyển tới login; Admin và superuser được vượt kiểm tra vai trò. Đăng xuất đòi POST + CSRF. Seed chạy lại không sinh dữ liệu trùng và không đổi mật khẩu cũ.

Chưa có kiểm thử CRUD, đặt chỗ, tính giá bán hay phân công trùng lịch vì đây là công việc của giai đoạn 1. Chưa kiểm thử trực tiếp trên Windows; README có lệnh PowerShell/CMD và driver PyMySQL để tránh phải biên dịch mysqlclient.
