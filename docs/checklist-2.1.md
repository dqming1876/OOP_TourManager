# Minh chứng 2.1 — UI/UX, Master–Detail và validation hai lớp

| Tiêu chí | Minh chứng trong mã nguồn |
| --- | --- |
| Danh mục Master–Detail | **Quản trị → Quản lý tour → Chi tiết** mở thông tin của dòng vừa chọn, gồm điểm đến, thời lượng, giá và mô tả. **Sửa tour** mở form danh mục. Xem `tourManagement`, `showTourDetail` và `editTour` trong [dist/admin.js](../dist/admin.js). |
| Form nghiệp vụ | **Lịch khởi hành** có form lập đợt và chế độ đổi sức chứa riêng. **Đặt chuyến đi** nhập đợt, số khách và liên hệ. **Xử lý đơn** và **Thu tiền / hoàn tiền** có phiếu riêng. Xem [dist/admin.js](../dist/admin.js), [dist/app.js](../dist/app.js) và [dist/operations.js](../dist/operations.js). |
| Hiển thị số, tiền và ngày | CSS chung căn phải cột số/tiền và ô nhập số. Tiền hiển thị theo nhóm ba chữ số, ví dụ `1.200.000 ₫`. Ngày trong danh sách và lựa chọn đợt hiển thị dạng `dd/MM/yyyy`. API dùng `yyyy-MM-dd`. Xem [dist/style.css](../dist/style.css), [dist/form-validation.js](../dist/form-validation.js) và [dist/app.js](../dist/app.js). |
| Lớp 1 — Form | Hiển thị lỗi tiếng Việt cạnh từng ô, nối lỗi bằng `aria-describedby`, đặt `aria-invalid` và đưa tiêu điểm đến ô lỗi đầu tiên trên tất cả form nghiệp vụ, danh mục (`frm001`–`frm009`) và đăng nhập/đăng ký (`frm000`, `frm008`). Chặn trước khi gửi nếu tên trống, số vượt giới hạn, URL ảnh không hợp lệ, ngày đã qua, ngày trùng hoặc số khách vượt chỗ đang hiển thị. Xem [dist/form-validation.js](../dist/form-validation.js), [dist/admin.js](../dist/admin.js), [dist/app.js](../dist/app.js) và [dist/operations.js](../dist/operations.js). |
| Lớp 2 — Domain/Service | Worker kiểm tra lại giá, ngày lịch, sức chứa, liên hệ, URL ảnh điểm đến (`https://` hoặc `/images/...`) và số khách. Khi thêm lịch trùng, câu lệnh INSERT giữ nguyên bản ghi cũ. Chế độ đổi sức chứa cập nhật đợt đã chọn và kiểm tra số chỗ đang giữ. API trả tên trường cho lỗi cụ thể. Xem [domain.py](../backend/domain.py), [services.py](../backend/services.py), [destinations.py](../backend/destinations.py), [repositories.py](../backend/repositories.py) và [app.py](../backend/app.py). |

## Kết quả kiểm tra

- `python3 -m unittest discover` kiểm tra backend Python với SQLite tạm, gồm validation ngày, giá, sức chứa, điện thoại, hồ sơ và lịch trùng. `node --test tests/frontend/*.test.js` kiểm tra dữ liệu báo cáo và tệp xuất.

## Các bước demo

1. **Quản lý tour → Chi tiết → Sửa tour**. Xóa tên hoặc nhập giá âm rồi bấm Lưu tour. Form giữ dữ liệu và đưa tiêu điểm đến ô lỗi.
2. **Lịch khởi hành → Chọn tour**. Lập một đợt trong tương lai. Thử thêm lại đúng ngày trên, rồi dùng **Sửa → Lưu sức chứa** để cập nhật đợt hiện có. Bảng hiển thị ngày dạng `dd/MM/yyyy` và căn phải cột số.
3. Dùng tài khoản khách, mở tour và nhập số điện thoại sai hoặc số khách vượt chỗ. Sửa các ô theo hướng dẫn rồi gửi lại để tạo đơn.
