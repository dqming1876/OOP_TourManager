# Nhánh feature/catalog

## Phạm vi

CRUD Supplier, Service, Guide, Vehicle, Tour, Departure, Customer. Chỉ thay đổi tệp trong catalog và customers; không thay model, migration, settings, accounts, config/urls.py hoặc templates/base.html.

- Class-based views, ModelForm, inline formset cho TourItinerary.
- Tìm kiếm qua `?q=`, phân trang 10 dòng; các liên kết phân trang giữ nguyên điều kiện lọc.
- Lịch khởi hành lọc theo trạng thái và ngày khởi hành trong khoảng `start_date`–`end_date` (bao gồm hai đầu).
- Booking trong chi tiết chuyến/khách hàng chỉ đọc qua related_name `bookings`, phân trang 10 dòng; không phụ thuộc URL của nhánh operations.
- Xóa phải POST sau trang xác nhận, có CSRF; dữ liệu được FK PROTECT bảo vệ nhận thông báo bằng messages.

## Chạy

Kích hoạt môi trường ảo và cấu hình MySQL theo README của bộ khung, sau đó:

```bash
python manage.py migrate
python manage.py setup_roles
python manage.py seed_base
python manage.py seed_catalog
python manage.py test
python manage.py runserver
```

Không cần makemigrations vì schema không đổi. Dùng tài khoản demo do seed_base đã tạo; mật khẩu in khi tạo lần đầu. `seed_catalog` không tạo user, booking, payment, phân công hay chi phí.

Nếu đã chạy seed_base, seed_catalog bổ sung để có 5 nhà cung cấp, 10 dịch vụ, 4 HDV, 4 xe, 4 tour, 10 ngày lịch trình, 8 lịch khởi hành, 10 khách hàng. Chạy lại không trùng, không ghi đè dữ liệu đã sửa. Trên database đã có thêm dữ liệu người dùng, tổng số có thể lớn hơn bộ mẫu; command không xóa dữ liệu để ép số lượng. Địa danh/tuyến đi có thật; liên hệ, con người và giá là mô phỏng. Mốc khởi hành cố định tháng 12/2026 để seed chạy nhiều ngày vẫn không trùng.

## Phân quyền ở view

| Tác nhân | Supplier/Service/Guide/Vehicle | Tour/Departure | Customer |
|---|---|---|---|
| Admin hoặc superuser | CRUD | CRUD | CRUD |
| Operator | CRUD | CRUD | 403 |
| Sales | 403 | Danh sách, chi tiết | CRUD |
| Chưa đăng nhập | Chuyển tới login | Chuyển tới login | Chuyển tới login |
| Chưa có nhóm quyền | 403 | 403 | 403 |

Dùng RoleRequiredMixin của khung; không thêm PermissionRequiredMixin vì model permissions của Operator trong khung chưa theo ma trận mới. Mọi route tạo/sửa/xóa kiểm tra phía server, kể cả POST trực tiếp. Nút sửa/xóa được ẩn với người chỉ có quyền xem. Quyền của nhiều nhóm được hợp lại theo mixin hiện có.

## Lịch trình và dữ liệu liên quan

Tour và toàn bộ lịch trình chỉ được lưu sau khi cả ModelForm và inline formset hợp lệ. Mỗi ngày từ 1 đến Tour.days phải có đúng một lịch trình, không chấp nhận thiếu ngày hoặc trùng ngày. Số đêm phải nhỏ hơn số ngày.

Lưu trong transaction.atomic. Vì TourItinerary không có bảng khác tham chiếu trong schema hiện tại, tập lịch trình được thay bằng các dòng đã xác thực mỗi lần lưu tour. Cách này hỗ trợ đổi số thứ tự ngày trên MySQL mà không va ràng buộc unique(tour, day_number); khóa chính dòng lịch trình sẽ thay đổi, khóa chính Tour vẫn giữ nguyên. Nếu tương lai có bảng tham chiếu TourItinerary, cần xem lại cách lưu trước khi đổi schema.

Departure kiểm tra ngày kết thúc không trước ngày bắt đầu; khi sửa không cho đặt max_seats nhỏ hơn số khách đã đặt chưa hủy. Danh sách dùng SUM có điều kiện để tính chỗ như property booked_seats mà không phát sinh một truy vấn riêng cho mỗi dòng. Không tự đổi trạng thái, tính giá booking hoặc thực hiện điều hành đoàn.

Các CBV và template dùng chung nằm trong catalog/crud.py và catalog/templates/catalog/. Customer có ModelForm, CBV, namespace và template riêng; template kế thừa phần dùng chung để tránh lặp mã. Đây là hai app cùng thuộc nhánh catalog.

## Kiểm thử

Đã chạy trên Python 3.14.3, Django 5.2.19, MySQL 8.4.7 (utf8mb4):

```text
python manage.py test --noinput
Ran 55 tests
OK
```

Trong đó 40 test mới thuộc catalog/customers, 15 test có sẵn. Kiểm tra quyền GET/POST; CRUD và messages; CSRF; tìm kiếm/phân trang; formset thiếu/trùng ngày, đổi thứ tự, xóa ngày, gửi ID lịch trình khác tour; rollback; ngày lọc sai; số chỗ chưa hủy; FK PROTECT; booking chỉ đọc; seed từ DB trống và seed nối tiếp seed_base. `check` không có lỗi, `makemigrations --check --dry-run` không có thay đổi.

## Git

Nhánh đã được chuẩn bị từ main:

```bash
git checkout -b feature/catalog
```

Sau khi thêm mã nguồn (không chạy lại checkout -b nếu nhánh đã tồn tại):

```bash
git status
git add catalog customers
git diff --cached --name-only
git commit -m "Implement catalog and customer management"
git push -u origin feature/catalog
```

Chỉ merge vào main sau khi hai nhóm kiểm tra tích hợp. Không sửa hoặc đẩy vào feature/operations từ nhánh này.

## ĐỀ XUẤT THAY ĐỔI KHUNG

Chưa áp dụng các thay đổi bên dưới vì vượt phạm vi hai app:

1. accounts/context_processors.py và templates/base.html: tách quyền hiển thị menu Supplier/Service/Guide/Vehicle khỏi Tour/Departure, để Sales chỉ nhìn thấy hai menu tour và lịch khởi hành. Hiện sidebar của khung vẫn hiện bốn menu bị cấm với Sales; truy cập chúng nhận trang 403. Thanh điều hướng bổ sung trong module này đã lọc đúng vai trò.
2. accounts/management/commands/setup_roles.py: đồng bộ model permissions theo ma trận mới — Operator CRUD danh mục, Sales chỉ view Tour/Departure và CRUD Customer. Giữ nguyên phần quyền booking/operations theo thỏa thuận với nhóm còn lại.
3. README.md và docs/teamWorkflow.md của khung: cập nhật tên nhánh feature/catalog, feature/operations và ma trận quyền mới sau khi hai nhóm thống nhất.

Không cần thay schema, cấu hình database hay root URL để sử dụng nhánh này.

## Tài liệu Django

- [ModelForm và inline formset](https://docs.djangoproject.com/en/5.2/topics/forms/modelforms/).
- [Transaction atomic](https://docs.djangoproject.com/en/5.2/topics/db/transactions/).
- [Generic editing views](https://docs.djangoproject.com/en/5.2/ref/class-based-views/generic-editing/).
