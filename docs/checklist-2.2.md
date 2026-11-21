# Minh chứng 2.2 — Ngoại lệ, xác thực và rollback

| Tiêu chí | Minh chứng |
| --- | --- |
| Ngoại lệ có kiểu | [errors.js](../worker/domain/errors.js) định nghĩa `AppError`, `ValidationError`, `AccessError` và `ConflictError`. [index.js](../worker/index.js) chuyển lỗi qua [http.js](../worker/api/http.js). Lỗi dự kiến giữ HTTP status và trường nhập. Lỗi bất ngờ trả HTTP 500, thông báo chung và mã yêu cầu. |
| Mật khẩu lưu dạng hash | [passwords.js](../worker/service/passwords.js) dùng PBKDF2-HMAC-SHA256 và salt riêng. Bảng `accounts` lưu `password_hash` và `salt`. Admin dùng `ADMIN_PASSWORD_HASH` và `ADMIN_PASSWORD_SALT` từ Workers secrets hoặc cấu hình thử. Test đăng nhập được với hash khách hiện có. |
| Tham số SQL | [accounts-repository.js](../worker/database/accounts-repository.js) và [operations-repository.js](../worker/database/operations-repository.js) truyền dữ liệu qua placeholder `?` và `.bind()`. Chuyển trạng thái chọn trong tập câu SQL cố định. |
| Ghi đa bảng, rollback | [Trigger D1](../Database/0001_tour_operations.sql) cập nhật `departures.reserved` cùng câu lệnh ghi hoặc hủy `bookings`. Test trên SQLite tạm chủ động gây lỗi khi cập nhật chỗ. Ca tạo đơn giữ 0 đơn và 0 chỗ giữ. Ca hủy giữ đơn ở `pending` và giữ nguyên 3 chỗ. Ca ghi phiếu thu giữ `paid = 0` và không tạo bút toán khi trigger thanh toán lỗi. |

## Cách kiểm chứng

- Chạy `npm test` với Node.js 24. Bộ test xác minh vòng đời đặt → xác nhận → thu → hoàn → hủy, phân quyền, tranh chỗ, hai chiều rollback, kiểm tra hash/salt và phản hồi HTTP 500.
- Để trình bày hash trên dữ liệu demo, đăng ký hai tài khoản thử bằng cùng mật khẩu. Kiểm tra chỉ số qua lệnh sau và so sánh hai dòng. Hash dài 64 ký tự, các salt và hash tạo ra khác nhau.

```bash
npx wrangler d1 execute DB --local --config wrangler.local.jsonc \
  --command "SELECT username, length(password_hash) AS hash_len, substr(password_hash, 1, 8) AS fixture_hash, length(salt) AS salt_len FROM accounts"
```

Tài liệu đối chiếu: [Cloudflare D1 prepared statement](https://developers.cloudflare.com/d1/worker-api/prepared-statements/), [OWASP Error Handling](https://cheatsheetseries.owasp.org/cheatsheets/Error_Handling_Cheat_Sheet.html).
