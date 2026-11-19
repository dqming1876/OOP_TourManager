# Nhánh feature/accounts

## Phạm vi và cách chạy

Nhánh xuất phát từ main, độc lập với feature/catalog và feature/operations. Dùng User và Group mặc định của Django; không tạo model hoặc migration mới.

```bash
python manage.py migrate
python manage.py setup_roles
python manage.py create_admin
python manage.py runserver
python manage.py test
```

Cấu hình .env theo .env.example. Nếu ADMIN_PASSWORD để trống, create_admin hỏi mật khẩu hai lần bằng getpass. Mật khẩu phải vượt validators hiện có của Django. Các biến ADMIN_USERNAME, ADMIN_EMAIL, ADMIN_PASSWORD cũng có thể được đặt trong môi trường hệ điều hành. Tham số CLI có ưu tiên cao hơn biến môi trường/.env.

```bash
python manage.py create_admin --username admin --email admin@example.com
```

Có hỗ trợ --password theo yêu cầu; nên dùng nhập ẩn hoặc .env để tránh lưu mật khẩu trong lịch sử terminal. Lệnh chỉ in tên tài khoản và kết quả. Chạy lại cùng username cập nhật mật khẩu/quyền, không tạo trùng. User được kích hoạt, bật is_staff/is_superuser và có đúng một nhóm Admin. Lệnh tự chạy setup_roles nếu nhóm Admin chưa tồn tại.

## Luồng đăng ký và duyệt

1. Mở /register/, nhập username, họ tên, email, mật khẩu và xác nhận. Họ tên tối đa 150 ký tự, lưu trong first_name; last_name để trống, không cần model hồ sơ riêng.
2. User mới có is_active=False, is_staff=False, is_superuser=False và không có Group. POST thêm trường role/groups/is_active/is_superuser không được áp dụng.
3. Sau khi gửi, hiện đúng thông báo “Đăng ký thành công, vui lòng chờ Admin duyệt” và chuyển đến /login/.
4. Login từ chối tài khoản chưa duyệt. Chỉ khi mật khẩu đúng mới hiện “Tài khoản đang chờ Admin duyệt”; mật khẩu sai vẫn nhận thông báo đăng nhập thông thường.
5. Admin mở /users/, chọn vai trò tại hàng chờ duyệt và bấm Duyệt. Thao tác dùng POST + CSRF, không gán vai trò ngầm định.
6. Tài khoản được kích hoạt và có đúng một nhóm: Admin, Sales hoặc Operator. Đăng nhập lại để dùng chức năng theo vai trò.

### Nhận diện ba trạng thái bằng dữ liệu sẵn có

- Đang hoạt động: is_active=True.
- Chờ duyệt: is_active=False, is_superuser=False và không có nhóm.
- Bị khóa: is_active=False nhưng không thuộc điều kiện chờ duyệt (thông thường đã có vai trò).

Không có cột trạng thái hoặc model mới. Với dữ liệu được nhập trực tiếp qua SQL/shell ngoài các luồng này, Admin nên sửa qua /users/ để chuẩn hóa về một vai trò. Không tự thay quyền của dữ liệu cũ khi seed chạy lại.

## URL và phân quyền

| URL | Tên URL | Quyền |
|---|---|---|
| /register/ | accounts:register | Công khai |
| /login/ | accounts:login | Công khai |
| /logout/ | accounts:logout | POST |
| /users/ | accounts:user_list | Admin |
| /users/create/ | accounts:user_create | Admin |
| /users/<pk>/edit/ | accounts:user_update | Admin |
| /users/<pk>/delete/ | accounts:user_delete | Admin |
| /users/<pk>/approve/ | accounts:user_approve | Admin, chỉ POST |
| /users/<pk>/password-reset/ | accounts:user_password_reset | Admin |
| /profile/ | accounts:profile | Đã đăng nhập |
| /password-change/ | accounts:password_change | Đã đăng nhập |

AdminRequiredMixin kế thừa RoleRequiredMixin. Superuser/nhóm Admin được qua; mọi đường dẫn /users/ trả trang 403 của khung nếu không phải Admin, kể cả khách chưa đăng nhập. Profile và tự đổi mật khẩu dùng LoginRequiredMixin, khách được chuyển tới login. Không sửa middleware hoặc settings.

Danh sách tìm bằng q theo username, họ tên, email; lọc role và status; mỗi trang 10 dòng, giữ query string khi chuyển trang. Hàng chờ duyệt có màu nổi bật; sidebar chỉ Admin thấy menu Người dùng và badge tổng số đang chờ.

## Vai trò và an toàn tài khoản

- Gán vai trò bằng groups.set([role]), xóa toàn bộ nhóm cũ. Các form chỉ cho chọn đúng ba nhóm đã định nghĩa.
- Admin đặt is_staff=True; Sales/Operator đặt is_staff=False và gỡ is_superuser để không còn quyền vượt kiểm tra. Tạo Admin từ giao diện không tự cấp is_superuser; create_admin cấp superuser theo yêu cầu.
- Không cho tự khóa/xóa/gỡ quyền Admin của tài khoản đang sử dụng. Có thể sửa họ tên/email và đổi mật khẩu của chính mình.
- Không cho khóa/xóa/gỡ quyền Admin cuối cùng đang hoạt động; Admin đang bị khóa không được tính là người thay thế.
- Thao tác đổi quyền, duyệt và xóa/khóa chạy trong transaction.atomic; khóa cùng hàng Group Admin bằng select_for_update để tránh hai Admin cùng làm mất tài khoản quản trị cuối.
- User có created_bookings hoặc received_payments chỉ bị khóa; dữ liệu và vai trò được giữ lại. User chưa có dữ liệu có thể xóa sau trang xác nhận. FK PROTECT khác cũng được xử lý bằng khóa tài khoản.
- User/Group trong Django Admin chỉ xem; quản lý tài khoản qua /users/ để không bỏ qua các chốt bảo vệ. Các model nghiệp vụ trong Django Admin không bị thay đổi.
- Profile chỉ lưu first_name/last_name/email; đổi mật khẩu chỉ lưu password, tránh ghi đè trạng thái nếu Admin vừa khóa tài khoản từ yêu cầu khác.
- Tự đổi mật khẩu dùng PasswordChangeView và kiểm tra mật khẩu cũ. Admin đặt lại mật khẩu dùng SetPasswordForm. Cả hai dùng validators Django; mật khẩu được hash qua API của Django.
- Tự đổi mật khẩu hoặc Admin đặt lại cho chính mình vẫn giữ phiên hiện tại. Admin đặt lại cho người khác làm các phiên cũ của người đó hết hiệu lực qua cơ chế session auth hash của Django.
- Các form có CSRF; các view nhận mật khẩu đánh dấu dữ liệu nhạy cảm. Không in mật khẩu ra stdout/stderr hoặc log.

seed_base vẫn tạo dữ liệu mẫu nếu cần, nhưng không in mật khẩu. Với tài khoản đã tồn tại, giữ nguyên mật khẩu và quyền; việc đăng ký trước username admin không làm tài khoản được tự cấp Admin khi seed chạy. Dùng create_admin để tạo/cập nhật Admin và giao diện đặt lại mật khẩu cho user mẫu khác.

## Kiểm thử

Đã kiểm tra trên Python 3.14.3, Django 5.2.19, MySQL 8.4.7, utf8mb4. Database phát triển và database test của nhánh được tách khỏi bản catalog đang chạy.

```text
python manage.py test --noinput
Ran 57 tests
OK
```

Kiểm tra đăng ký chưa kích hoạt/không nhóm, chống gửi thêm trường quyền, thông báo đăng nhập chờ duyệt, GET/POST sai vai trò nhận 403, gán một nhóm và cờ staff/superuser, duyệt lặp, Admin cuối cùng, tự khóa/xóa, xóa chuyển sang khóa khi có booking/thanh toán, bộ lọc/phân trang, badge, CSRF, mật khẩu, phiên đăng nhập, create_admin từ tham số/.env/getpass và seed không nâng quyền username có sẵn.

TransactionTestCase chạy hai kết nối MySQL trong hai luồng để xác nhận hai Admin cùng khóa nhau vẫn còn đúng một Admin hoạt động. Không dùng sleep hoặc mô phỏng khóa bằng mock.

## Git và tích hợp

Lệnh thực hiện từ bộ khung main:

```bash
git checkout main
git pull --ff-only origin main
git checkout -b feature/accounts
git add accounts templates/base.html .env.example README.md
git diff --cached --name-only
git commit -m "Implement registration and account administration"
git push -u origin feature/accounts
```

Nếu nhánh đã tồn tại trên GitHub, dùng git fetch origin rồi git switch --track origin/feature/accounts. Không chạy lại checkout -b trên nhánh đã có.

Chỉ sửa accounts/ và ba tệp chung được yêu cầu cụ thể: templates/base.html (menu Người dùng và dropdown tài khoản), .env.example, README.md. Link Đăng ký nằm trong template đăng nhập của accounts. Không đổi models, migrations, config/settings.py, config/urls.py, mixin phân quyền, setup_roles hoặc DashboardView của bộ khung.

Khi tích hợp với nhánh operations, giữ phần DashboardView mà nhóm đó phát triển và ghép các import/view tài khoản. Khi ghép base.html, chỉ áp dụng hai điểm menu/dropdown, giữ các menu nghiệp vụ của nhánh còn lại. Không tự merge các nhánh vào main trong công việc này.

## Tài liệu Django

- [AuthenticationForm và PasswordChangeView](https://docs.djangoproject.com/en/5.2/topics/auth/default/).
- [Password validation](https://docs.djangoproject.com/en/5.2/topics/auth/passwords/).
- [select_for_update](https://docs.djangoproject.com/en/5.2/ref/models/querysets/#select-for-update).
