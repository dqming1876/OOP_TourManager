# mingo — Travel & Tours

Mingo là hệ thống quản lý tour, lịch khởi hành, đơn và báo cáo. [Trang Cloudflare](https://mingo.doquangminh1807.workers.dev/)

## Mở bản demo

1. Cài sẵn Node.js 24. Mở Terminal trong thư mục mã nguồn hoặc thư mục vừa giải nén.
2. Chạy `node scripts/demo.mjs`, rồi mở `http://127.0.0.1:4173` trên trình duyệt.
3. Dùng `demo_admin` và mật khẩu in trong Terminal để xem khu quản trị. Dùng `mingo_khach1` và mật khẩu demo được in cùng lúc để xem phía khách. Đây là tài khoản giả trên máy cục bộ.
4. Mở **Quản trị → Báo cáo**. Lọc **Hà Nội – Phố cổ và Hồ Gươm** theo tháng liền trước để đối chiếu số liệu trong [minh chứng 1.2–1.4](docs/checklist-1.2-1.4.md).

Bản demo dựng lại SQLite trong bộ nhớ mỗi lần chạy. Đổi cổng bằng biến `MINGO_DEMO_PORT` khi cổng mặc định đang được dùng. Đóng gói với `node scripts/package-demo.mjs mingo-demo.zip` (cần lệnh `zip`).

## Kiểm thử

Chạy `node scripts/build-cloudflare.mjs && node --test test/*.test.js`. Bộ kiểm thử dùng DB tạm: phân quyền, trạng thái, tranh chỗ, hoàn tác, seed và đối chiếu ba báo cáo. Xem thêm [minh chứng mục 1.1](docs/checklist-1.1.md).

## Chạy bằng Cloudflare D1 cục bộ

Chạy `npm install`, áp migration bằng `npx wrangler d1 migrations apply DB --local`. Tạo tệp `.dev.vars` với `ADMIN_USERNAME`, `ADMIN_PASSWORD`, `ADMIN_SESSION_SECRET` riêng cho môi trường. Chạy `npm run dev`.

Nếu cần seed trong D1 cục bộ mới, chạy `node scripts/seed-demo.mjs mingo-demo.sql`, rồi `npx wrangler d1 execute DB --local --file mingo-demo.sql` trước khi mở ứng dụng. Bản demo tại bước trên tự nạp seed và dùng SQLite tạm.

Trước khi triển khai sang Cloudflare, đặt secrets và áp các migration còn thiếu. Với DB có bảng `accounts` từ trước, kiểm tra lịch sử migration để tránh tạo lại bảng. Chỉnh sửa tour và đơn từ localStorage cũ cần chuyển riêng. Trình chỉnh sửa địa danh và đặc sản vẫn lưu tại trình duyệt.
