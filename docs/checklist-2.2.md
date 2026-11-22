# Minh chứng 2.2 — Ngoại lệ, xác thực và rollback

| Tiêu chí | Minh chứng |
| --- | --- |
| Ngoại lệ có kiểu | [domain.py](../backend/domain.py) định nghĩa `AppError`, `ValidationError`, `AccessError` và `ConflictError`. [entry.py](../entry.py) chuyển lỗi qua [app.py](../backend/app.py). Lỗi dự kiến giữ HTTP status và trường nhập. Lỗi bất ngờ trả HTTP 500, thông báo chung và mã yêu cầu. |
| Mật khẩu lưu dạng hash | [auth.py](../backend/auth.py) dùng PBKDF2-HMAC-SHA256 và salt riêng. Bảng `accounts` lưu `password_hash` và `salt`. Workers secrets cung cấp hash và salt để khởi tạo admin một lần. Đăng nhập đọc hash và salt từ DB. Test đăng nhập được với hash khách hiện có. |
| Tham số SQL | [repositories.py](../backend/repositories.py) truyền dữ liệu qua placeholder `?`; adapter `D1Database.prepare()` trong `entry.py` gọi `.bind()`. Chuyển trạng thái chọn trong tập câu SQL cố định. |
| Ghi đa bảng, rollback | [Trigger D1](../Database/0001_tour_operations.sql) cập nhật `departures.reserved` cùng câu lệnh ghi hoặc hủy `bookings`. Test trên SQLite tạm chủ động gây lỗi khi cập nhật chỗ. Ca tạo đơn giữ 0 đơn và 0 chỗ giữ. Ca hủy giữ đơn ở `pending` và giữ nguyên 3 chỗ. Ca ghi phiếu thu giữ `paid = 0` và không tạo bút toán khi trigger thanh toán lỗi. |
| Kết quả ghi D1 | `D1Database.execute()` đếm các dòng trả về từ `RETURNING`. [Test adapter](../tests/test_d1_adapter.py) dùng binding giả với trigger SQLite thật để xác minh thu, hoàn và hủy. |
| Hạn mức đăng nhập | [LoginRateLimiter](../backend/login_limits.py) lưu cửa sổ 5 phút trên D1 để các Worker dùng chung. [Kiểm thử](../tests/test_login_limits.py) xác nhận lượt thứ 13 trả 429 sau 12 lần đăng nhập sai. |

## Cách kiểm chứng

- Chạy `npm test` với Python 3.12. Bộ test xác minh vòng đời đặt → xác nhận → thu → hoàn → hủy, phân quyền, tranh chỗ, hai chiều rollback, kiểm tra hash/salt và phản hồi HTTP 500.
- Để trình bày hash trên dữ liệu demo, đăng ký hai tài khoản thử bằng cùng mật khẩu. Kiểm tra chỉ số qua lệnh sau và so sánh hai dòng. Hash dài 64 ký tự, các salt và hash tạo ra khác nhau.

```bash
npx wrangler d1 execute DB --local --config wrangler.local.jsonc \
  --command "SELECT username, length(password_hash) AS hash_len, substr(password_hash, 1, 8) AS fixture_hash, length(salt) AS salt_len FROM accounts"
```

Tài liệu đối chiếu: [Cloudflare D1 prepared statement](https://developers.cloudflare.com/d1/worker-api/prepared-statements/), [OWASP Error Handling](https://cheatsheetseries.owasp.org/cheatsheets/Error_Handling_Cheat_Sheet.html).
