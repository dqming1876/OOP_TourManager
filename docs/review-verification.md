# Rà soát Python — 22/11/2026

## Phạm vi

Tích hợp `codex/mingo-review-fixes` và `review-ocp` trên nền main `598fd60`. Giữ bốn checklist 1.1–1.4 riêng biệt. Không triển khai production hoặc sửa D1 từ xa trong đợt kiểm tra này.

## Thay đổi và truy vết

| Vấn đề | Thay đổi | Kiểm chứng |
| --- | --- | --- |
| D1 đếm cả trigger gây 409 sau khi ghi thành công | Đếm dòng `RETURNING` ở adapter | `tests/test_d1_adapter.py`, mutation khôi phục lỗi phải FAIL |
| Giới hạn đăng nhập chỉ nằm trong RAM | `LoginRateLimiter` + `login_attempts` D1 | `tests/test_login_limits.py`: 12 lượt, lượt 13, hết hạn, nhiều instance |
| Thiếu Strategy Python | `PricingPolicy`, `StandardPrice`, `PercentageDiscount` | `tests/test_pricing.py`; giá/chỗ kiểm trong cùng INSERT |
| Gửi lại đơn tạo trùng | Mã yêu cầu ổn định, đối chiếu nội dung đã lưu | `tests/test_review_fixes.py` |
| Thiếu Enum và lệch tài liệu | `Role`, `BookingStatus`, `PaymentKind`; UML và tên Python | `tests/test_review_completion.py`, checklist 3.2/4.1/4.2 |
| HTTP lọt vào service | Cookie/IP trích xuất ở app; limiter riêng | Test kiến trúc và kiểm tra đọc header/cookie |
| Admin ngoài DB | Bootstrap một lần; FK role tới bảng roles; login đọc hash DB | Test không ghi đè hash đã thay và không giữ quyền sau hạ role |
| Thuộc tính tour gộp JSON | Migration 0008 thêm cột, trích xuất rồi bỏ content | Test nâng schema có dữ liệu cũ, FK và bản lưu đối chiếu |
| Địa danh chỉ lưu trình duyệt | API/D1 cho 204 mục; quyền admin; version tránh mất cập nhật | Test sửa/xóa/trùng tên/phiên cũ/mục cuối; frontend tải dữ liệu chung |
| Thiếu test ở các biên | Test RBAC trực tiếp, paid/status, capacity/reserved, ngày báo cáo, mật khẩu | `tests/test_review_completion.py` |
| Mã frontend khó đọc | Định dạng lại app/admin; giữ tên hàm và UI | Test frontend và kiểm tra cú pháp |
| Cấu hình cá nhân trong repo | Config mặc định dùng ID giả; production dùng tệp riêng gitignore | README và cấu hình mẫu |

## Kết quả thực thi

- `npm test`: 59 test Python và 10 test JavaScript PASS.
- `python3 -m scripts.verify_review`: baseline PASS; phát hiện 11/11 mutant độc lập. Không đồng nhất bộ này với 16 mutant của công cụ bên ngoài.
- `npm run build`: biên dịch cú pháp Python.
- `uv run pywrangler deploy --dry-run --outdir .wrangler/python-bundle --config wrangler.local.jsonc`: đóng gói thành công.
- `npx wrangler d1 migrations apply DB --local --config wrangler.local.jsonc`: 10 migration thành công, tới 0009.
- [XLSX kiểm chứng](evidence/review-export.xlsx) được tạo bằng exporter thật, đọc lại bằng openpyxl: giữ nguyên tiếng Việt, tiêu đề, ngày xuất, phạm vi và tổng số dạng số. Đây là dữ liệu tổng hợp để kiểm định dạng, không phải doanh thu thực tế.

## Chưa xác nhận trên môi trường này

- Wrangler dev bị môi trường chặn khi gọi `uv_interface_addresses`. Vì vậy chưa đánh dấu PASS cho Python Worker chạy trong workerd hoặc Cloudflare production.
- Chromium bị chặn tạo socket khi khởi động. Chưa xác nhận trực quan bố cục, font PDF hoặc toàn bộ luồng UI qua trình duyệt. `window.print()` được giữ nguyên.
- Để kiểm tra trên máy có Chromium: cài `playwright`, `openpyxl`, `pymupdf`; đặt `CHROMIUM_PATH` nếu cần rồi chạy `python3 -m tests.ui_review`. Script mở SQLite tạm ở localhost, kiểm sửa địa danh và xuất XLSX/PDF, dừng server khi xong. Không ghi dữ liệu production.
- Để kiểm tra runtime D1: chạy Wrangler local rồi `python3 -m tests.worker_smoke`, gồm đặt/gửi lại, xác nhận/thu/hoàn/hủy và báo cáo.

Không tự đánh dấu điểm A/B/C hoặc sửa file Excel của giảng viên từ các kết quả trên.
