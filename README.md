# mingo — Travel & Tours

Website quản lý tour du lịch. [Bản đang chạy trên Cloudflare](https://mingo.doquangminh1807.workers.dev/)

- `dist/` chứa giao diện và tài nguyên khách tải về. `dist/Resource/` chứa dữ liệu địa danh dùng chung.
- `worker/api/` xử lý HTTP, `worker/service/` thực hiện nghiệp vụ, `worker/domain/` chứa quy tắc và kiểu lỗi, `worker/database/` truy cập D1.
- `Database/` chứa migration tài khoản, tour, lịch, đơn và chỉ mục báo cáo.
- Minh chứng [1.1–1.4](docs/checklist-1.1-1.4.md), [2.1](docs/checklist-2.1.md), [2.2](docs/checklist-2.2.md), [2.3](docs/checklist-2.3.md) và [2.4](docs/checklist-2.4.md).

## Bản demo

Chạy `npm run demo` với Node.js 24 rồi mở địa chỉ in trong Terminal. Demo tự tạo dữ liệu trên SQLite trong bộ nhớ và in thông tin hai tài khoản thử. Mở **Quản trị → Báo cáo** để đối chiếu dữ liệu trong [minh chứng 1.1–1.4](docs/checklist-1.1-1.4.md).

Đổi cổng bằng `MINGO_DEMO_PORT`. Đóng gói bằng `node scripts/package-demo.mjs mingo-demo.zip` (cần lệnh `zip`).

## Chạy cục bộ

Dùng Node.js 24 và npm. Cấu hình mẫu dùng D1 cục bộ. Dùng cùng tệp cấu hình cho cả migration và khởi chạy.

```bash
npm ci
cp wrangler.example.jsonc wrangler.local.jsonc
cp .dev.vars.example .dev.vars
npx wrangler d1 migrations apply DB --local --config wrangler.local.jsonc
```

Đặt `ADMIN_USERNAME` trong `.dev.vars`. Tạo hash và salt từ mật khẩu thử dài ít nhất 12 ký tự. Lệnh dưới đây đọc mật khẩu từ đầu vào ẩn trong Bash.

```bash
read -rs admin_local_password
printf '%s\n' "$admin_local_password" | node scripts/admin-password-hash.mjs
unset admin_local_password
node -e 'console.log(crypto.randomUUID() + crypto.randomUUID())'
```

Điền `ADMIN_PASSWORD_SALT` và `ADMIN_PASSWORD_HASH` từ kết quả lệnh vào `.dev.vars`, rồi lấy kết quả dòng cuối làm `ADMIN_SESSION_SECRET`.

```bash
npm run dev -- --config wrangler.local.jsonc
npm test
```

Nhánh dùng D1, vì vậy đổi cơ sở dữ liệu bằng `d1_databases` trong tệp Wrangler. Giữ binding `DB`. Các ID khởi động ở tệp mẫu dùng cho môi trường cục bộ.

Nếu cần dữ liệu mẫu trên D1 cục bộ mới, tạo seed bằng `node scripts/seed-demo.mjs mingo-demo.sql` rồi dùng `npx wrangler d1 execute DB --local --config wrangler.local.jsonc --file mingo-demo.sql`.

## Triển khai

Áp dụng migration còn thiếu cho D1 của môi trường đích. Nếu dự án từng tạo bảng `accounts` ngoài Wrangler, đối chiếu lịch sử migration trước khi áp dụng. Với môi trường từng dùng `ADMIN_PASSWORD`, tạo hash và salt từ mật khẩu quản trị và đặt hai giá trị làm Workers secrets **trước khi triển khai code mới**. Sau khi xác minh đăng nhập, xóa secret mật khẩu cũ. Giữ `ADMIN_SESSION_SECRET` hiện tại nếu cần duy trì các phiên hợp lệ.

Tour, lịch và đơn dùng D1. Thay đổi địa danh và đặc sản từ trình chỉnh sửa riêng lưu trên trình duyệt.
