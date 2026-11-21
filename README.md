# mingo — Travel & Tours

Mã nguồn website quản lý tour du lịch. [Bản đang chạy trên Cloudflare](https://mingo.doquangminh1807.workers.dev/)

- `dist/` chứa giao diện và ảnh.
- `worker/` xử lý tài khoản, phân quyền và nghiệp vụ tour.
- `drizzle/` chứa migration D1 dành cho tài khoản, tour, lịch và đơn.
- [Minh chứng mục 1.1](docs/checklist-1.1.md) ghi phạm vi, use case và cách kiểm chứng.

## Chạy cục bộ

Cài Node.js 24 và npm. Chạy `npm install`, rồi `npx wrangler d1 migrations apply DB --local`. Tạo tệp `.dev.vars` với ba biến `ADMIN_USERNAME`, `ADMIN_PASSWORD` và `ADMIN_SESSION_SECRET`. Dùng mật khẩu riêng cho bản thử và tạo khóa phiên ngẫu nhiên dài. Chạy `npm run dev`, mở địa chỉ Wrangler in ra và đăng ký một tài khoản khách. Bản thử dùng dữ liệu D1 cục bộ.

Chạy `npm test` để kiểm tra Worker với SQLite tạm. Có thể chạy trực tiếp bằng `node scripts/build-cloudflare.mjs && node --test test/operations.test.js`.

Khi triển khai sang một Worker, cấu hình D1 và secrets của môi trường đó. Áp dụng migration còn thiếu trước khi triển khai mã mới. Với cơ sở dữ liệu đã có bảng `accounts` từ trước, kiểm tra lịch sử migration trước khi áp dụng để tránh chạy lại migration tạo bảng. Tour, lịch và đơn cần D1. Các đơn và chỉnh sửa tour từng lưu trong trình duyệt của bản cũ không được nhập tự động. Danh mục địa danh/đặc sản của trình chỉnh sửa riêng vẫn lưu trên trình duyệt.
