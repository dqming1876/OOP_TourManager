# mingo — Travel & Tours

Mã nguồn website quản lý tour du lịch. Bản đang chạy: https://mingo.doquangminh1807.workers.dev/

- `dist/`: giao diện và ảnh.
- `worker/`: đăng nhập và hồ sơ khách hàng.
- `drizzle/`: cấu trúc bảng tài khoản trong D1.

Chạy `node scripts/build-cloudflare.mjs` rồi `npx wrangler dev` để xem thử. Nếu triển khai sang tài khoản khác, đổi account ID và cấu hình D1 trong `wrangler.jsonc`, áp dụng SQL trong `drizzle/` cho cơ sở dữ liệu mới và đặt các secret `ADMIN_USERNAME`, `ADMIN_PASSWORD`, `ADMIN_SESSION_SECRET` qua Wrangler.

Tour và đơn đặt được lưu trong trình duyệt. Tài khoản dùng Cloudflare D1.
