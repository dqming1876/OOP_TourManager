# Mã nguồn đầy đủ – feature/accounts

Nội dung đầy đủ của 24 tệp thêm/sửa, mỗi tệp có đường dẫn và khối code riêng. Không bao gồm .env hoặc mật khẩu demo.

## Cây thư mục các tệp thêm/sửa

```text
tourManager/
├── .env.example
├── README.md
├── accounts/
│   ├── README.md
│   ├── admin.py
│   ├── context_processors.py
│   ├── forms.py
│   ├── management/
│   │   └── commands/
│   │       ├── create_admin.py
│   │       └── seed_base.py
│   ├── services.py
│   ├── templates/
│   │   └── accounts/
│   │       ├── form_fields.html
│   │       ├── login.html
│   │       ├── pagination.html
│   │       ├── password_change.html
│   │       ├── profile.html
│   │       ├── register.html
│   │       ├── user_confirm_delete.html
│   │       ├── user_dropdown.html
│   │       ├── user_form.html
│   │       ├── user_list.html
│   │       └── user_password_reset.html
│   ├── tests.py
│   ├── urls.py
│   └── views.py
└── templates/
    └── base.html
```

## tourManager/.env.example

```text
# Sao chép thành .env, thay khóa bí mật và mật khẩu trước khi chạy.
SECRET_KEY=replace-with-a-random-key
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
DB_NAME=tourmanager
DB_USER=tourmanager
DB_PASSWORD=replace-with-your-database-password
DB_HOST=127.0.0.1
DB_PORT=3306

# Tạo Admin bằng create_admin; để trống mật khẩu để nhập ẩn tại terminal.
ADMIN_USERNAME=admin
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=
```

## tourManager/README.md

````markdown
# tourManager

Bộ khung giai đoạn 0 cho đồ án **Hệ thống quản lý dịch vụ du lịch và điều hành tour** của công ty lữ hành nhỏ. Thời gian dự kiến 1–2 tuần, hai người phát triển song song.

Đã có schema, migration, đăng nhập/đăng xuất, nhóm quyền, dashboard chào mừng, giao diện nền, Django Admin và dữ liệu mẫu. Các URL nghiệp vụ mới được quy ước; chưa có view CRUD hay xử lý đặt chỗ, thu tiền, phân công, báo cáo.

## 1. Công nghệ và cách đặt tên

- Python 3.11–3.14; Django 5.2.19; MySQL 8.0 hoặc 8.4; charset `utf8mb4`.
- PyMySQL 1.2.4 (`pymysql.install_as_MySQLdb()`), python-decouple, Django Templates, Bootstrap 5.3.3 qua CDN.
- Repo dùng lowerCamelCase: `tourManager`. Project `config`, các app và tên field giữ đúng đặc tả. Model dùng PascalCase (`TourItinerary`), field/method Python dùng snake_case (`full_name`, `booked_seats`); tên bắt buộc của Django như `__str__`, `Meta`, `allowed_roles` giữ nguyên.
- Tiền VNĐ dùng `DecimalField(max_digits=14, decimal_places=0)`, không dùng float.
- Giao diện, nhãn field và chú thích bằng tiếng Việt; tên biến và model bằng tiếng Anh.

## 2. Cài đặt sau khi clone (Windows PowerShell)

Cài Python 3.11+ và MySQL Server 8 trước. Mở terminal tại thư mục dự án:

```powershell
git clone https://github.com/dqming1876/tourManager.git
cd tourManager
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Nếu máy chỉ có Python 3.12/3.13/3.14, thay `py -3.11` bằng phiên bản đã cài. Nếu PowerShell chặn activate, dùng CMD với `.venv\Scripts\activate.bat`, hoặc gọi trực tiếp `.venv\Scripts\python.exe` thay cho `python`.

Tạo database và tài khoản riêng trong MySQL:

```powershell
mysql -u root -p
```

```sql
CREATE DATABASE tourmanager CHARACTER SET utf8mb4;
CREATE USER 'tourmanager'@'127.0.0.1' IDENTIFIED BY 'thay-mat-khau-db-cua-ban';
GRANT ALL PRIVILEGES ON tourmanager.* TO 'tourmanager'@'127.0.0.1';
EXIT;
```

Nếu `mysql` chưa có trong PATH, mở MySQL Command Line Client hoặc chạy phần SQL bằng MySQL Workbench. Database lấy collation `utf8mb4` mặc định của MySQL. Các bảng dùng InnoDB mặc định của MySQL 8.

Tạo cấu hình riêng:

```powershell
Copy-Item .env.example .env
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Mở `.env`, dán khóa vừa tạo vào `SECRET_KEY` và đặt `DB_PASSWORD` đúng mật khẩu MySQL. Giữ `DB_NAME=tourmanager`, `DB_USER=tourmanager`, `DB_HOST=127.0.0.1`, `DB_PORT=3306` nếu dùng cổng mặc định. Khi khóa chứa dấu `#`, đặt toàn bộ giá trị trong dấu nháy kép. `.env` không được commit.

Chạy theo thứ tự:

```powershell
python manage.py migrate
python manage.py setup_roles
python manage.py seed_base
python manage.py check
python manage.py runserver
```

Mở <http://127.0.0.1:8000/>. Trang đăng nhập: `/login/`; trang quản trị: `/admin/`.

`seed_base` tạo ba tài khoản `admin`, `sales`, `operator` với mật khẩu ngẫu nhiên và không in mật khẩu. Dùng `create_admin` bên dưới để đặt mật khẩu Admin, sau đó vào `/users/` để đặt lại mật khẩu cho tài khoản mẫu khác. Chạy lại seed không đổi mật khẩu hoặc quyền của tài khoản đã tồn tại.

`admin` là superuser và được vào Django Admin. `sales`/`operator` đăng nhập giao diện ứng dụng, không có quyền staff vào Admin mặc định. Người thuộc nhóm Admin được vượt kiểm tra vai trò; muốn vào `/admin/` vẫn cần bật `is_staff` theo cơ chế Django.

### macOS/Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

Các lệnh SQL và `manage.py` giống Windows. Bootstrap cần Internet để tải CDN.

## 3. Lệnh tạo khung từ thư mục trống

Đây là trình tự đã dùng để dựng project. **Không chạy lại startproject/startapp trên bản đã clone**, vì mã nguồn đã có đầy đủ.

```powershell
mkdir tourManager
cd tourManager
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install Django==5.2.19 "PyMySQL[rsa]==1.2.4" python-decouple==3.8
mysql -u root -p
```

Trong MySQL chạy SQL ở mục 2, sau đó thoát và tiếp tục:

```powershell
django-admin startproject config .
python manage.py startapp accounts
python manage.py startapp catalog
python manage.py startapp customers
python manage.py startapp bookings
python manage.py startapp operations
python manage.py startapp reports
```

Sau khi đặt đầy đủ các tệp nguồn và cấu hình `.env`:

```powershell
python manage.py makemigrations catalog customers bookings operations
python manage.py migrate
python manage.py setup_roles
python manage.py seed_base
python manage.py runserver
```

Migration `0001_initial.py` đã được chốt và commit trong repo. Khi clone sang máy khác, chỉ cần `migrate`.

## 4. Schema đã chốt

- `catalog`: Supplier, Service, Guide, Vehicle, Tour, TourItinerary, Departure.
- `customers`: Customer.
- `bookings`: Booking, Payment.
- `operations`: GuideAssignment, VehicleAssignment, TourExpense.
- `accounts`: dùng User/Group/Permission mặc định của Django; không tạo custom User.
- `reports`: không có model, sẽ tổng hợp từ dữ liệu các app khác.

Chi tiết field, lựa chọn trạng thái, quan hệ và quy tắc xóa: [docs/schema.md](docs/schema.md).

`Departure.booked_seats` cộng người lớn và trẻ em của **mọi booking chưa hủy**, gồm PENDING, CONFIRMED, COMPLETED. `available_seats = max_seats - booked_seats`.

`Booking.paid_amount` cộng tất cả Payment; `remaining_amount = total_amount - paid_amount`. Kết quả có thể âm nếu dữ liệu nhập quá chỗ/quá tiền: giai đoạn này chỉ cung cấp property theo yêu cầu, chưa chặn nghiệp vụ hay tự đổi trạng thái. Không tự tính tổng tiền, giảm chỗ, tạo mã, thu/hoàn tiền hoặc kiểm tra trùng lịch.

## 5. Quyền đã thống nhất

| Module | Admin/superuser | Sales | Operator |
|---|---|---|---|
| Dashboard | Truy cập | Truy cập | Truy cập |
| Danh mục tour/dịch vụ/HDV/xe/lịch khởi hành | Toàn quyền | Chỉ xem | Chỉ xem |
| Khách hàng | Toàn quyền | Toàn quyền | Ẩn |
| Booking, thanh toán | Toàn quyền | Toàn quyền | Ẩn |
| Phân công, chi phí | Toàn quyền | Ẩn | Toàn quyền |
| Báo cáo | Xem | Xem | Xem |

Đây là lựa chọn quyền mặc định cho đồ án. `setup_roles` gán Django model permissions tương ứng (Admin có mọi permission). Báo cáo không có model nên kiểm tra theo vai trò ở view sau này. Người chưa có nhóm quyền nhận trang 403 tại dashboard; có thể đăng xuất và đăng nhập tài khoản khác.

`RoleRequiredMixin` đứng trước class-based view; khai báo `allowed_roles = ("Sales",)` hoặc `("Operator",)`. Superuser và nhóm Admin luôn được qua. Người chưa đăng nhập được chuyển đến login, sai vai trò nhận HTTP 403 với trang tiếng Việt. Nhiều nhóm được tính theo hợp quyền. Việc ẩn menu chỉ phục vụ giao diện; view nghiệp vụ tương lai vẫn phải kiểm tra quyền phía server. View thay đổi danh mục dành cho Admin: `allowed_roles = ()`.

## 6. URL và cách chia việc

`config/urls.py` include tất cả app tại gốc bằng `path("", include("<app>.urls"))`. Các app nghiệp vụ có `app_name` và `urlpatterns = []` ở giai đoạn này. `accounts` có `/`, `/login/`, `/logout/` để chạy phần nền.

| Nhóm | App phụ trách | Đường dẫn tương lai |
|---|---|---|
| 1 | catalog, customers | `/suppliers/`, `/services/`, `/guides/`, `/vehicles/`, `/tours/`, `/departures/`, `/customers/` |
| 2 | bookings, operations, reports; DashboardView trong accounts | `/`, `/bookings/`, `/payments/`, `/assignments/`, `/expenses/`, `/reports/` |

Sidebar đã đủ mọi menu và dùng href cứng theo bảng. **Các đường dẫn nghiệp vụ hiện trả 404** vì hai nhóm sẽ tự thêm view/URL; đây là trạng thái dự kiến của giai đoạn 0.

Quy ước code, namespace, tên URL và nhánh: [docs/teamWorkflow.md](docs/teamWorkflow.md).

## 7. Dữ liệu nền và kiểm thử

`seed_base` dùng `get_or_create`, tạo 3 user, 2 nhà cung cấp, 4 dịch vụ, 2 HDV, 2 xe, 2 tour, 5 ngày lịch trình, 3 lịch khởi hành, 3 khách hàng. Các tuyến Hà Nội–Hạ Long và Hà Nội–Sa Pa/địa danh có thật; tên đối tác, liên hệ, con người, giá là mô phỏng để làm đồ án. CCCD để trống. Chưa tạo Booking/Payment/Assignment/Expense. Ngày mẫu cố định trong tháng 12/2026 để chạy lại không sinh thêm lịch khởi hành.

Chạy `setup_roles` sau `migrate` để có đủ model permissions. `seed_base` cũng tự gọi `setup_roles` khi cần.

Tài khoản chạy kiểm thử cần quyền tạo và xóa **database test riêng**, không dùng dữ liệu đang học. Trong MySQL với tài khoản quản trị:

```sql
GRANT ALL PRIVILEGES ON test_tourmanager.* TO 'tourmanager'@'127.0.0.1';
```

```powershell
python manage.py check --database default
python manage.py makemigrations --check --dry-run
python manage.py test
```

Có 15 kiểm thử cho phân quyền, menu, login/logout + CSRF, seed chạy lặp, các property tiền và số chỗ. Kiểm tra đã chạy trên Python 3.14.3, MySQL 8.4.7, utf8mb4. Các migration đều áp dụng thành công và `makemigrations --check --dry-run` không phát sinh thay đổi.

## 8. Git và GitHub

Repo đã được tạo tại <https://github.com/dqming1876/tourManager> (riêng tư). Người thứ hai cần được chủ repo mời vào mục Settings → Collaborators trước khi clone/push.

Khi muốn tự tạo một repo mới từ thư mục chưa có Git, dùng GitHub CLI đã đăng nhập đúng tài khoản:

```powershell
git init -b main
git add .
git commit -m "Initialize phase zero skeleton"
gh auth status
gh repo create dqming1876/tourManager --private --source=. --remote=origin
git push -u origin main
```

Khối trên chỉ dùng khi repo GitHub **chưa tồn tại**. Nếu tạo repo trống qua giao diện GitHub thì thay lệnh `gh repo create` bằng:

```powershell
git remote add origin https://github.com/dqming1876/tourManager.git
git push -u origin main
```

Với repo hiện tại, clone và phát triển bằng nhánh ở tài liệu chia việc; không chạy lại `git init` hay ghi đè lịch sử remote.

## 9. Giải thích khi bảo vệ (8 ý)

1. Đây là ứng dụng Django theo mô hình MVT: Model quản lý dữ liệu, View xử lý yêu cầu, Template hiển thị HTML.
2. Sáu app chia theo chức năng để hai người phát triển độc lập trên schema đã thống nhất.
3. Tour mô tả sản phẩm; Departure là lần khởi hành cụ thể của sản phẩm đó.
4. Customer liên kết Booking; mỗi Booking thuộc một Departure và có nhiều Payment.
5. Điều hành dùng các bảng phân công HDV, xe và chi phí gắn với Departure.
6. Tiền dùng Decimal để tính chính xác VNĐ; các property tổng hợp số chỗ và khoản thanh toán từ dữ liệu liên quan.
7. User/Group của Django quản lý Admin, Sales, Operator; mixin kiểm tra vai trò phía server và template hiển thị menu phù hợp.
8. Migration tạo cùng một cấu trúc MySQL trên mọi máy; seed tạo dữ liệu mẫu để trình bày và kiểm thử.

## Tài liệu chính thức

- [Django 5.2: phiên bản Python tương thích](https://docs.djangoproject.com/en/5.2/faq/install/).
- [Django 5.2: cấu hình MySQL](https://docs.djangoproject.com/en/5.2/ref/databases/).
- [PyMySQL: extra rsa cho xác thực MySQL](https://pymysql.readthedocs.io/en/latest/user/installation.html).

## Tạo tài khoản admin

Sau khi cấu hình MySQL và chạy `python manage.py migrate`, dùng:

```bash
python manage.py create_admin
```

Lệnh đọc `ADMIN_USERNAME`, `ADMIN_EMAIL`, `ADMIN_PASSWORD` từ `.env`. Nếu mật khẩu trống, lệnh hỏi mật khẩu và xác nhận bằng getpass, không hiển thị ký tự nhập và không in mật khẩu ra log. Có thể truyền tham số:

```bash
python manage.py create_admin --username admin --email admin@example.com
```

Có hỗ trợ `--password`, nhưng nên dùng `.env` hoặc nhập ẩn để tránh mật khẩu nằm trong lịch sử terminal. Không commit `.env`. Mật khẩu phải vượt các validators của Django. Chạy lại cùng username sẽ cập nhật mật khẩu, kích hoạt tài khoản, bật is_staff/is_superuser và đặt đúng một nhóm Admin. Nếu chưa có nhóm Admin, lệnh tự chạy setup_roles.

Nhánh feature/accounts bổ sung `/register/`, `/users/`, `/profile/`, `/password-change/`. Tài khoản tự đăng ký chưa kích hoạt và chưa có nhóm; Admin chọn vai trò khi duyệt. Chờ duyệt được nhận diện bằng is_active=False và không có nhóm; tài khoản bị khóa đã có vai trò nhưng is_active=False. Thao tác quản lý chỉ dành cho Admin. User/Group trong Django Admin chỉ xem; sử dụng `/users/` để các quy tắc bảo vệ Admin cuối cùng, tự khóa và dữ liệu liên quan luôn được kiểm tra. Không phát sinh model/migration mới.

Chi tiết cài đặt nhánh, kiểm thử và mã nguồn nằm trong `accounts/README.md` và `accounts/fullSource.md`.
````

## tourManager/accounts/README.md

````markdown
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
````

## tourManager/accounts/admin.py

```python
"""User/Group chỉ xem trong Django Admin; sửa qua /users/ để giữ quy tắc bảo vệ."""
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import GroupAdmin, UserAdmin
from django.contrib.auth.models import Group


class ReadOnlyAccountsMixin:
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.unregister(get_user_model())
admin.site.unregister(Group)


@admin.register(get_user_model())
class ManagedUserAdmin(ReadOnlyAccountsMixin, UserAdmin):
    pass


@admin.register(Group)
class ManagedGroupAdmin(ReadOnlyAccountsMixin, GroupAdmin):
    pass
```

## tourManager/accounts/context_processors.py

```python
from .roles import get_user_roles
from .services import pending_users


def current_role(request):
    roles = get_user_roles(request.user)
    is_admin = "Admin" in roles
    return {
        "user_roles": roles,
        "current_role": ", ".join(roles) if roles else "Chưa phân quyền",
        "is_admin_role": is_admin,
        "pending_user_count": pending_users().count() if is_admin else 0,
        "can_view_catalog": bool(roles),
        "can_manage_customers": is_admin or "Sales" in roles,
        "can_manage_bookings": is_admin or "Sales" in roles,
        "can_manage_operations": is_admin or "Operator" in roles,
        "can_view_reports": bool(roles),
    }
```

## tourManager/accounts/forms.py

```python
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm, SetPasswordForm, UserCreationForm
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError

from .roles import ROLE_NAMES
from .services import is_pending_user, save_user_account

User = get_user_model()


def style_fields(form):
    for field in form.fields.values():
        widget = field.widget
        if isinstance(widget, forms.CheckboxInput):
            widget.attrs["class"] = "form-check-input"
        elif isinstance(widget, forms.Select):
            widget.attrs["class"] = "form-select"
        else:
            widget.attrs["class"] = "form-control"


def set_full_name(user, data):
    user.first_name = data.get("full_name", "").strip()
    user.last_name = ""


def available_roles():
    return Group.objects.filter(name__in=ROLE_NAMES).order_by("name")


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "Tên đăng nhập"
        self.fields["password"].label = "Mật khẩu"
        self.fields["username"].widget.attrs.update({"autocomplete": "username", "autofocus": True})
        self.fields["password"].widget.attrs["autocomplete"] = "current-password"
        self.error_messages = self.error_messages.copy()
        self.error_messages["invalid_login"] = "Tên đăng nhập hoặc mật khẩu không đúng."
        self.error_messages["inactive"] = "Tài khoản đã bị khóa."
        style_fields(self)

    def clean(self):
        try:
            return super().clean()
        except ValidationError:
            username = self.cleaned_data.get("username")
            password = self.cleaned_data.get("password")
            user = User.objects.filter(username=username).first() if username else None
            # Chỉ giải thích trạng thái khi mật khẩu đúng, không tiết lộ qua tên tài khoản.
            if user is not None and not user.is_active and password and user.check_password(password):
                message = "Tài khoản đang chờ Admin duyệt" if is_pending_user(user) else "Tài khoản đã bị khóa, vui lòng liên hệ Admin"
                raise ValidationError(message, code="inactive")
            raise


class BaseCreateUserForm(UserCreationForm):
    full_name = forms.CharField(label="Họ tên", max_length=150)
    email = forms.EmailField(label="Email", max_length=254)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "full_name", "email", "password1", "password2")
        labels = {"username": "Tên đăng nhập"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password1"].label = "Mật khẩu"
        self.fields["password2"].label = "Nhập lại mật khẩu"
        style_fields(self)

    def _post_clean(self):
        # Để password validators kiểm tra cả họ tên vừa nhập.
        set_full_name(self.instance, self.cleaned_data)
        super()._post_clean()


class RegistrationForm(BaseCreateUserForm):
    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_active = False
        user.is_staff = False
        user.is_superuser = False
        if commit:
            user.save()
        return user


class AdminUserCreateForm(BaseCreateUserForm):
    role = forms.ModelChoiceField(label="Vai trò", queryset=Group.objects.none(), empty_label="Chọn vai trò")
    is_active = forms.BooleanField(label="Kích hoạt tài khoản", required=False, initial=True)

    class Meta(BaseCreateUserForm.Meta):
        fields = (*BaseCreateUserForm.Meta.fields, "role", "is_active")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["role"].queryset = available_roles()

    def save(self, commit=True):
        if not commit:
            raise ValueError("Form quản lý người dùng phải được lưu cùng vai trò.")
        user = super().save(commit=False)
        return save_user_account(user, self.cleaned_data["role"], self.cleaned_data["is_active"])


class ProfileForm(forms.ModelForm):
    full_name = forms.CharField(label="Họ tên", max_length=150)
    email = forms.EmailField(label="Email", max_length=254)

    class Meta:
        model = User
        fields = ("full_name", "email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.initial["full_name"] = self.instance.get_full_name()
        style_fields(self)

    def save(self, commit=True):
        user = super().save(commit=False)
        set_full_name(user, self.cleaned_data)
        if commit:
            # Không ghi đè cờ quyền nếu Admin vừa khóa tài khoản ở yêu cầu khác.
            user.save(update_fields=["first_name", "last_name", "email"])
        return user


class AdminUserUpdateForm(ProfileForm):
    role = forms.ModelChoiceField(label="Vai trò", queryset=Group.objects.none(), empty_label="Chọn vai trò")
    is_active = forms.BooleanField(label="Kích hoạt tài khoản", required=False)

    class Meta(ProfileForm.Meta):
        fields = ("full_name", "email", "role", "is_active")

    def __init__(self, *args, actor, **kwargs):
        self.actor = actor
        super().__init__(*args, **kwargs)
        self.fields["role"].queryset = available_roles()
        current = self.instance.groups.filter(name__in=ROLE_NAMES).first()
        self.initial["role"] = current.pk if current else None
        if self.instance.is_superuser:
            self.initial["role"] = Group.objects.filter(name="Admin").values_list("pk", flat=True).first()

    def save(self, commit=True):
        if not commit:
            raise ValueError("Form quản lý người dùng phải được lưu cùng vai trò.")
        self.instance = save_user_account(
            self.instance, self.cleaned_data["role"], self.cleaned_data["is_active"],
            actor=self.actor, full_name=self.cleaned_data["full_name"], email=self.cleaned_data["email"],
        )
        return self.instance


class ApproveUserForm(forms.Form):
    role = forms.ModelChoiceField(label="Vai trò", queryset=Group.objects.none(), empty_label="Chọn vai trò")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["role"].queryset = available_roles()
        style_fields(self)


class UserFilterForm(forms.Form):
    q = forms.CharField(label="Tìm kiếm", required=False)
    role = forms.ChoiceField(label="Vai trò", required=False, choices=[("", "Tất cả vai trò"), *((name, name) for name in ROLE_NAMES)])
    status = forms.ChoiceField(label="Trạng thái", required=False, choices=[("", "Tất cả trạng thái"), ("active", "Đang hoạt động"), ("pending", "Chờ duyệt"), ("locked", "Bị khóa")])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_fields(self)


class ConfirmationForm(forms.Form):
    pass


class PasswordOnlySaveMixin:
    def save(self, commit=True):
        self.user.set_password(self.cleaned_data["new_password1"])
        if commit:
            self.user.save(update_fields=["password"])
        return self.user


class AdminPasswordResetForm(PasswordOnlySaveMixin, SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_fields(self)


class SelfPasswordChangeForm(PasswordOnlySaveMixin, PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_fields(self)
```

## tourManager/accounts/management/commands/create_admin.py

```python
from getpass import getpass
from pathlib import Path

from decouple import Config, RepositoryEnv
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

from accounts.services import save_user_account


class Command(BaseCommand):
    help = "Tạo hoặc cập nhật superuser thuộc đúng nhóm Admin; không in mật khẩu."

    def add_arguments(self, parser):
        parser.add_argument("--username")
        parser.add_argument("--email")
        parser.add_argument("--password")

    def handle(self, *args, **options):
        env_file = Path(settings.BASE_DIR) / ".env"
        env = Config(RepositoryEnv(str(env_file))) if env_file.exists() else Config()
        username = options["username"] or env("ADMIN_USERNAME", default="admin") or "admin"
        email = options["email"] if options["email"] is not None else env("ADMIN_EMAIL", default="")
        password = options["password"] if options["password"] is not None else env("ADMIN_PASSWORD", default="")
        if not password:
            try:
                password = getpass("Nhập mật khẩu Admin: ")
                confirmation = getpass("Nhập lại mật khẩu Admin: ")
            except (EOFError, KeyboardInterrupt) as exc:
                raise CommandError("Không đọc được mật khẩu. Hãy cấu hình ADMIN_PASSWORD hoặc nhập trực tiếp tại terminal.") from exc
            if password != confirmation:
                raise CommandError("Hai mật khẩu không khớp.")
        User = get_user_model()
        username = User.normalize_username(username)
        try:
            User._meta.get_field("username").clean(username, None)
            User._meta.get_field("email").clean(email, None)
            user = User.objects.filter(username=username).first() or User(username=username)
            user.email = email
            validate_password(password, user=user)
        except ValidationError as error:
            raise CommandError(" ".join(error.messages)) from error
        if not Group.objects.filter(name="Admin").exists():
            call_command("setup_roles", stdout=self.stdout)
        created = user.pk is None
        try:
            save_user_account(user, Group.objects.get(name="Admin"), True, email=email, password=password, force_superuser=True)
        except ValidationError as error:
            raise CommandError(" ".join(error.messages)) from error
        action = "Tạo mới" if created else "Cập nhật"
        self.stdout.write(self.style.SUCCESS(f"{action} tài khoản Admin {username} thành công."))
```

## tourManager/accounts/management/commands/seed_base.py

```python
import secrets
from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction

from catalog.models import Departure, Guide, Service, Supplier, Tour, TourItinerary, Vehicle
from customers.models import Customer


class Command(BaseCommand):
    help = "Tạo dữ liệu du lịch Việt Nam mẫu; chạy lại không sinh bản ghi trùng."

    @transaction.atomic
    def handle(self, *args, **options):
        call_command("setup_roles", stdout=self.stdout)
        User = get_user_model()
        for username, role, first_name in [
            ("admin", "Admin", "Quản trị viên"),
            ("sales", "Sales", "Nhân viên kinh doanh"),
            ("operator", "Operator", "Nhân viên điều hành"),
        ]:
            user, created = User.objects.get_or_create(username=username, defaults={
                "first_name": first_name,
                "is_staff": username == "admin",
                "is_superuser": username == "admin",
                "is_active": True,
            })
            if created:
                password = secrets.token_urlsafe(12)
                user.set_password(password)
                user.save(update_fields=["password"])
                user.groups.set([Group.objects.get(name=role)])
                self.stdout.write(self.style.SUCCESS(f"Đã tạo tài khoản mẫu {username}. Dùng chức năng đặt lại mật khẩu trước khi đăng nhập."))
            else:
                self.stdout.write(f"Tài khoản {username} đã tồn tại; giữ nguyên mật khẩu và quyền.")

        # Địa danh và tuyến đi có thật; tên đối tác, liên hệ và nhân sự là dữ liệu mô phỏng.
        hotel, _ = Supplier.objects.get_or_create(name="Khách sạn Hạ Long Xanh (mẫu)", defaults={
            "supplier_type": "Lưu trú", "phone": "0900000001",
            "email": "halong@example.com", "address": "Bãi Cháy, Quảng Ninh",
        })
        partner, _ = Supplier.objects.get_or_create(name="Dịch vụ du lịch Việt Bắc (mẫu)", defaults={
            "supplier_type": "Dịch vụ tổng hợp", "phone": "0900000002",
            "email": "vietbac@example.com", "address": "Hoàn Kiếm, Hà Nội",
        })
        for name, kind, supplier, price, unit, description in [
            ("Phòng đôi Bãi Cháy", Service.ServiceType.LODGING, hotel, "800000", "phòng/đêm", "Phòng đôi, tiêu chuẩn 2 khách."),
            ("Xe du lịch Hà Nội - Hạ Long", Service.ServiceType.TRANSPORT, partner, "3500000", "xe/ngày", "Xe 29 chỗ phục vụ đoàn."),
            ("Suất ăn đặc sản địa phương", Service.ServiceType.MEAL, partner, "180000", "suất", "Thực đơn theo đoàn, đặt trước."),
            ("Vé tham quan vịnh Hạ Long", Service.ServiceType.TICKET, partner, "310000", "khách", "Giá mẫu phục vụ đồ án, không phải báo giá thương mại."),
        ]:
            Service.objects.get_or_create(name=name, supplier=supplier, defaults={
                "service_type": kind, "unit_price": Decimal(price), "unit": unit, "description": description,
            })

        for full_name, phone, languages in [
            ("Nguyễn Minh Anh", "0900000011", "Tiếng Việt, Tiếng Anh"),
            ("Trần Hoàng Nam", "0900000012", "Tiếng Việt, Tiếng Trung"),
        ]:
            Guide.objects.get_or_create(full_name=full_name, phone=phone, defaults={"languages": languages})
        for plate, kind, seats, driver, phone in [
            ("29B-900.01", "Thaco Town 29 chỗ", 29, "Lê Văn Hùng", "0900000021"),
            ("29B-900.02", "Ford Transit 16 chỗ", 16, "Phạm Văn Hải", "0900000022"),
        ]:
            Vehicle.objects.get_or_create(plate_number=plate, defaults={
                "vehicle_type": kind, "seats": seats, "driver_name": driver, "driver_phone": phone,
            })

        halong, _ = Tour.objects.get_or_create(code="HNHL2N1D", defaults={
            "name": "Hà Nội - Hạ Long 2 ngày 1 đêm", "days": 2, "nights": 1,
            "destination": "Vịnh Hạ Long, Quảng Ninh", "base_price": Decimal("2450000"),
            "description": "Tham quan vịnh Hạ Long, hang Sửng Sốt, đảo Ti Tốp và nghỉ tại Bãi Cháy.",
        })
        sapa, _ = Tour.objects.get_or_create(code="HNSP3N2D", defaults={
            "name": "Hà Nội - Sa Pa 3 ngày 2 đêm", "days": 3, "nights": 2,
            "destination": "Sa Pa, Lào Cai", "base_price": Decimal("3650000"),
            "description": "Khám phá Sa Pa, bản Cát Cát và khu du lịch Fansipan.",
        })
        for tour, day, title, content in [
            (halong, 1, "Hà Nội - Hạ Long", "Đón khách tại Hà Nội, đi cao tốc đến Hạ Long. Ăn trưa, nhận phòng và tham quan Bãi Cháy."),
            (halong, 2, "Tham quan vịnh - Hà Nội", "Lên tàu tham quan vịnh, hang Sửng Sốt và đảo Ti Tốp. Ăn trưa, trở về Hà Nội."),
            (sapa, 1, "Hà Nội - Sa Pa", "Khởi hành theo cao tốc Nội Bài - Lào Cai. Nhận phòng và thăm nhà thờ đá Sa Pa."),
            (sapa, 2, "Fansipan - bản Cát Cát", "Buổi sáng tham quan khu du lịch Fansipan. Buổi chiều đi bản Cát Cát, tìm hiểu văn hóa địa phương."),
            (sapa, 3, "Sa Pa - Hà Nội", "Tự do tham quan thị trấn, mua đặc sản. Trả phòng và lên xe về Hà Nội."),
        ]:
            TourItinerary.objects.get_or_create(tour=tour, day_number=day, defaults={"title": title, "content": content})
        # Giữ ngày cố định để chạy lại vào ngày khác cũng không sinh thêm chuyến.
        for tour, start, end, seats, price in [
            (halong, date(2026, 12, 5), date(2026, 12, 6), 29, "2450000"),
            (halong, date(2026, 12, 12), date(2026, 12, 13), 29, "2550000"),
            (sapa, date(2026, 12, 19), date(2026, 12, 21), 16, "3650000"),
        ]:
            Departure.objects.get_or_create(tour=tour, start_date=start, defaults={
                "end_date": end, "max_seats": seats, "price": Decimal(price),
            })
        for name, phone, email, address in [
            ("Nguyễn Thu Hà", "0900000031", "thuha@example.com", "Cầu Giấy, Hà Nội"),
            ("Trần Đức Long", "0900000032", "duclong@example.com", "Lê Chân, Hải Phòng"),
            ("Lê Ngọc Mai", "0900000033", "ngocmai@example.com", "Hải Châu, Đà Nẵng"),
        ]:
            Customer.objects.get_or_create(full_name=name, phone=phone, defaults={
                "email": email, "address": address, "note": "Khách hàng mô phỏng phục vụ đồ án.",
            })
        self.stdout.write(self.style.SUCCESS("Đã tạo dữ liệu nền. Không tạo booking, thanh toán, phân công hoặc chi phí."))
```

## tourManager/accounts/services.py

```python
"""Quy tắc tài khoản dùng chung cho form, view và lệnh quản trị."""
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.db.models.deletion import ProtectedError

from .roles import ROLE_NAMES


def pending_users():
    return get_user_model().objects.filter(is_active=False, is_superuser=False, groups__isnull=True)


def is_pending_user(user):
    return not user.is_active and not user.is_superuser and not list(user.groups.all())


def is_admin_user(user):
    return user.is_superuser or any(group.name == "Admin" for group in user.groups.all())


def role_label(user):
    if user.is_superuser:
        return "Admin"
    names = {group.name for group in user.groups.all()}
    return ", ".join(name for name in ROLE_NAMES if name in names) or "Chưa phân quyền"


def lock_admin_group():
    # Mọi thao tác đổi quyền/khóa/xóa khóa cùng một hàng để bảo vệ Admin cuối cùng.
    try:
        return Group.objects.select_for_update().get(name="Admin")
    except Group.DoesNotExist as exc:
        raise ValidationError("Chưa có nhóm Admin. Hãy chạy setup_roles trước.") from exc


def validate_access_change(target, actor, role, is_active, deleting=False):
    loses_admin_access = deleting or not is_active or role.name != "Admin"
    if target.is_active and is_admin_user(target) and loses_admin_access:
        admins = get_user_model().objects.filter(is_active=True).filter(Q(is_superuser=True) | Q(groups__name="Admin")).distinct()
        if admins.count() <= 1:
            raise ValidationError("Không thể khóa, xóa hoặc gỡ quyền Admin cuối cùng đang hoạt động.")
    if actor is not None and target.pk == actor.pk and loses_admin_access:
        raise ValidationError("Bạn không thể tự khóa, xóa hoặc gỡ quyền Admin của chính mình.")


@transaction.atomic
def save_user_account(user, role, is_active, *, actor=None, full_name=None, email=None, password=None, force_superuser=False):
    lock_admin_group()
    if role.name not in ROLE_NAMES:
        raise ValidationError("Vai trò không hợp lệ.")
    target = user
    if user.pk:
        target = get_user_model().objects.select_for_update().get(pk=user.pk)
        validate_access_change(target, actor, role, is_active)
    if full_name is not None:
        target.first_name = full_name.strip()
        target.last_name = ""
    if email is not None:
        target.email = email
    target.is_active = is_active
    target.is_staff = role.name == "Admin"
    if role.name != "Admin":
        target.is_superuser = False
    elif force_superuser:
        target.is_superuser = True
    if password is not None:
        target.set_password(password)
    target.save()
    target.groups.set([role])
    return target


@transaction.atomic
def approve_user(user_pk, role, actor):
    lock_admin_group()
    target = get_user_model().objects.select_for_update().get(pk=user_pk)
    if not is_pending_user(target):
        raise ValidationError("Tài khoản này đã được duyệt hoặc đã được phân quyền. Vui lòng kiểm tra lại.")
    return save_user_account(target, role, True, actor=actor)


@transaction.atomic
def delete_or_lock_user(user_pk, actor):
    admin_group = lock_admin_group()
    target = get_user_model().objects.select_for_update().get(pk=user_pk)
    validate_access_change(target, actor, admin_group, False, deleting=True)
    has_data = target.created_bookings.exists() or target.received_payments.exists()
    if not has_data:
        try:
            with transaction.atomic():
                target.delete()
            return "deleted"
        except ProtectedError:
            # Nếu có quan hệ PROTECT khác, giữ dữ liệu và chuyển sang khóa.
            pass
    target.is_active = False
    target.save(update_fields=["is_active"])
    return "locked"
```

## tourManager/accounts/templates/accounts/form_fields.html

```html
{% if form.non_field_errors %}<div class="alert alert-danger" role="alert">{{ form.non_field_errors }}</div>{% endif %}
{% for field in form %}
  {% if field.field.widget.input_type == "checkbox" %}
  <div class="form-check mb-3">{{ field }}<label class="form-check-label" for="{{ field.id_for_label }}">{{ field.label }}</label></div>
  {% else %}
  <div class="mb-3">
    <label class="form-label fw-semibold" for="{{ field.id_for_label }}">{{ field.label }}{% if field.field.required %} <span class="text-danger">*</span>{% endif %}</label>
    {{ field }}
    {% if field.help_text %}<div class="form-text">{{ field.help_text }}</div>{% endif %}
    {% for error in field.errors %}<div class="text-danger small mt-1" role="alert">{{ error }}</div>{% endfor %}
  </div>
  {% endif %}
{% endfor %}
```

## tourManager/accounts/templates/accounts/login.html

```html
{% extends "base.html" %}
{% block title %}Đăng nhập{% endblock %}
{% block content %}
<div class="login-shell">
  <section class="page-card login-card p-4 p-md-5 shadow-sm" aria-labelledby="loginTitle">
    <span class="badge text-bg-primary mb-3">tourManager</span>
    <h1 class="h3 fw-bold" id="loginTitle">Chào mừng trở lại</h1>
    <p class="text-secondary mb-4">Đăng nhập để truy cập hệ thống quản lý du lịch.</p>
    {% if form.non_field_errors %}
    <div class="alert alert-danger" role="alert">{{ form.non_field_errors }}</div>
    {% endif %}
    <form method="post" action="{% url 'accounts:login' %}">
      {% csrf_token %}
      <input type="hidden" name="next" value="{{ next }}">
      {% for field in form %}
      <div class="mb-3">
        <label class="form-label" for="{{ field.id_for_label }}">{{ field.label }}</label>
        {{ field }}
        {% for error in field.errors %}<div class="text-danger small mt-1">{{ error }}</div>{% endfor %}
      </div>
      {% endfor %}
      <button class="btn btn-primary w-100 mt-2" type="submit">Đăng nhập</button>
    </form>
    <p class="small text-secondary mb-0 mt-4">Chưa có tài khoản? <a href="{% url 'accounts:register' %}">Đăng ký</a></p>
  </section>
</div>
{% endblock %}
```

## tourManager/accounts/templates/accounts/pagination.html

```html
{% if is_paginated %}
<nav class="d-flex flex-wrap align-items-center justify-content-between gap-3 mt-4" aria-label="Phân trang người dùng">
  <span class="small text-secondary">Hiển thị {{ page_obj.start_index }}–{{ page_obj.end_index }} / {{ paginator.count }}</span>
  <ul class="pagination mb-0">
    {% if page_obj.has_previous %}<li class="page-item"><a class="page-link" href="?{% if pagination_query %}{{ pagination_query }}&amp;{% endif %}page={{ page_obj.previous_page_number }}">Trước</a></li>{% endif %}
    <li class="page-item active" aria-current="page"><span class="page-link">{{ page_obj.number }} / {{ paginator.num_pages }}</span></li>
    {% if page_obj.has_next %}<li class="page-item"><a class="page-link" href="?{% if pagination_query %}{{ pagination_query }}&amp;{% endif %}page={{ page_obj.next_page_number }}">Sau</a></li>{% endif %}
  </ul>
</nav>
{% endif %}
```

## tourManager/accounts/templates/accounts/password_change.html

```html
{% extends "base.html" %}
{% block title %}Đổi mật khẩu{% endblock %}
{% block content %}
<section class="page-card p-4 mx-auto" style="max-width: 720px;">
  <h1 class="h3 mb-4">Đổi mật khẩu</h1>
  <form method="post" novalidate>
    {% csrf_token %}
    {% include "accounts/form_fields.html" %}
    <button class="btn btn-primary" type="submit">Đổi mật khẩu</button>
    <a class="btn btn-outline-secondary" href="{% url 'accounts:profile' %}">Hủy</a>
  </form>
</section>
{% endblock %}
```

## tourManager/accounts/templates/accounts/profile.html

```html
{% extends "base.html" %}
{% block title %}Hồ sơ cá nhân{% endblock %}
{% block content %}
<section class="page-card p-4 mx-auto" style="max-width: 800px;">
  <h1 class="h3">Hồ sơ cá nhân</h1>
  <dl class="row my-4"><dt class="col-sm-4">Tên đăng nhập</dt><dd class="col-sm-8">{{ user.username }}</dd><dt class="col-sm-4">Vai trò</dt><dd class="col-sm-8">{{ current_role }}</dd></dl>
  <form method="post" novalidate>
    {% csrf_token %}
    {% include "accounts/form_fields.html" %}
    <button class="btn btn-primary" type="submit">Lưu hồ sơ</button>
    <a class="btn btn-outline-secondary" href="{% url 'accounts:password_change' %}">Đổi mật khẩu</a>
  </form>
</section>
{% endblock %}
```

## tourManager/accounts/templates/accounts/register.html

```html
{% extends "base.html" %}
{% block title %}Đăng ký tài khoản{% endblock %}
{% block content %}
<div class="login-shell">
  <section class="page-card login-card p-4 shadow-sm" aria-labelledby="registerTitle">
    <span class="badge text-bg-primary mb-3">tourManager</span>
    <h1 class="h3 fw-bold" id="registerTitle">Đăng ký tài khoản</h1>
    <p class="text-secondary">Tài khoản cần được Admin duyệt và cấp vai trò trước khi sử dụng.</p>
    <form method="post" novalidate>
      {% csrf_token %}
      {% include "accounts/form_fields.html" %}
      <button class="btn btn-primary w-100" type="submit">Gửi đăng ký</button>
    </form>
    <p class="small mt-4 mb-0">Đã có tài khoản? <a href="{% url 'accounts:login' %}">Đăng nhập</a></p>
  </section>
</div>
{% endblock %}
```

## tourManager/accounts/templates/accounts/user_confirm_delete.html

```html
{% extends "base.html" %}
{% block title %}Xác nhận xóa hoặc khóa tài khoản{% endblock %}
{% block content %}
<section class="page-card p-4 mx-auto mt-3" style="max-width: 720px;">
  <h1 class="h3">Xác nhận {% if has_related_data %}khóa{% else %}xóa{% endif %} tài khoản</h1>
  <p>Tài khoản: <strong>{{ object.username }}</strong> — {{ object.get_full_name }}</p>
  {% if has_related_data %}<div class="alert alert-info">Tài khoản đã có booking hoặc thanh toán. Hệ thống sẽ khóa đăng nhập và giữ lại dữ liệu liên quan.</div>{% else %}<p class="text-secondary">Tài khoản chưa có booking hoặc thanh toán và có thể được xóa hẳn. Hệ thống sẽ kiểm tra lại khi xác nhận.</p>{% endif %}
  <form method="post">
    {% csrf_token %}
    {% include "accounts/form_fields.html" %}
    <button class="btn btn-danger" type="submit">Xác nhận {% if has_related_data %}khóa{% else %}xóa{% endif %}</button>
    <a class="btn btn-outline-secondary" href="{% url 'accounts:user_list' %}">Hủy</a>
  </form>
</section>
{% endblock %}
```

## tourManager/accounts/templates/accounts/user_dropdown.html

```html
<div class="dropdown">
  <button class="btn btn-light dropdown-toggle text-end" type="button" data-bs-toggle="dropdown" aria-expanded="false">
    <span class="d-block fw-semibold">{{ user.get_full_name|default:user.username }}</span>
    <span class="small text-secondary">{{ current_role }}</span>
  </button>
  <ul class="dropdown-menu dropdown-menu-end">
    <li><a class="dropdown-item" href="{% url 'accounts:profile' %}">Hồ sơ cá nhân</a></li>
    <li><a class="dropdown-item" href="{% url 'accounts:password_change' %}">Đổi mật khẩu</a></li>
    {% if is_admin_role %}<li><a class="dropdown-item" href="{% url 'accounts:user_list' %}">Quản lý người dùng</a></li>{% endif %}
    <li><hr class="dropdown-divider"></li>
    <li><form method="post" action="{% url 'accounts:logout' %}">{% csrf_token %}<button class="dropdown-item" type="submit">Đăng xuất</button></form></li>
  </ul>
</div>
```

## tourManager/accounts/templates/accounts/user_form.html

```html
{% extends "base.html" %}
{% block title %}{{ page_title }}{% endblock %}
{% block content %}
<a href="{% url 'accounts:user_list' %}" class="text-decoration-none">Danh sách người dùng</a>
<h1 class="h3 my-4">{{ page_title }}{% if object %}: {{ object.username }}{% endif %}</h1>
<section class="page-card p-3 p-md-4 mx-auto" style="max-width: 800px;">
  <form method="post" novalidate>
    {% csrf_token %}
    {% include "accounts/form_fields.html" %}
    <div class="d-flex flex-wrap gap-2 mt-4">
      <button class="btn btn-primary" type="submit">Lưu người dùng</button>
      <a class="btn btn-outline-secondary" href="{% url 'accounts:user_list' %}">Hủy</a>
      {% if object %}<a class="btn btn-outline-primary" href="{% url 'accounts:user_password_reset' object.pk %}">Đặt lại mật khẩu</a>{% endif %}
    </div>
  </form>
</section>
{% endblock %}
```

## tourManager/accounts/templates/accounts/user_list.html

```html
{% extends "base.html" %}
{% block title %}Người dùng{% endblock %}
{% block content %}
<div class="d-flex flex-wrap align-items-center justify-content-between gap-3 mb-4">
  <div><h1 class="h3 mb-1">Người dùng</h1><p class="text-secondary mb-0">{{ paginator.count }} tài khoản phù hợp · {{ pending_user_count }} tài khoản chờ duyệt</p></div>
  <a class="btn btn-primary" href="{% url 'accounts:user_create' %}">Thêm người dùng</a>
</div>
<section class="page-card p-3 p-md-4">
  <form method="get" class="row g-3 align-items-end mb-4">
    {% if filter_form.non_field_errors %}<div class="col-12 text-danger">{{ filter_form.non_field_errors }}</div>{% endif %}
    {% for field in filter_form %}<div class="col-sm-6 col-lg-3"><label class="form-label" for="{{ field.id_for_label }}">{{ field.label }}</label>{{ field }}{% for error in field.errors %}<div class="small text-danger">{{ error }}</div>{% endfor %}</div>{% endfor %}
    <div class="col-auto"><button class="btn btn-primary" type="submit">Tìm kiếm</button></div>
    <div class="col-auto"><a class="btn btn-outline-secondary" href="{% url 'accounts:user_list' %}">Đặt lại</a></div>
  </form>
  <div class="table-responsive">
    <table class="table table-hover align-middle">
      <thead class="table-light"><tr><th>Tên đăng nhập</th><th>Họ tên</th><th>Email</th><th>Vai trò</th><th>Trạng thái</th><th class="text-end">Thao tác</th></tr></thead>
      <tbody>
        {% for account in users %}
        <tr{% if account.is_pending %} class="table-warning"{% endif %}>
          <td class="fw-semibold">{{ account.username }}{% if account.pk == request.user.pk %}<div class="small text-secondary">Tài khoản của bạn</div>{% endif %}</td>
          <td>{{ account.get_full_name|default:"—" }}</td><td>{{ account.email|default:"—" }}</td><td>{{ account.display_role }}</td>
          <td>{% if account.is_active %}<span class="badge text-bg-success">Đang hoạt động</span>{% elif account.is_pending %}<span class="badge text-bg-warning">Chờ duyệt</span>{% else %}<span class="badge text-bg-secondary">Bị khóa</span>{% endif %}</td>
          <td class="text-end">
            {% if account.is_pending %}
            <form method="post" action="{% url 'accounts:user_approve' account.pk %}" class="d-flex gap-2 mb-2 justify-content-end">
              {% csrf_token %}
              <select name="role" class="form-select form-select-sm" style="min-width: 140px; max-width: 180px;" required aria-label="Vai trò cho {{ account.username }}">
                <option value="">Chọn vai trò</option>
                {% for role in approve_form.fields.role.queryset %}<option value="{{ role.pk }}">{{ role.name }}</option>{% endfor %}
              </select>
              <button class="btn btn-sm btn-success text-nowrap" type="submit">Duyệt</button>
            </form>
            {% endif %}
            <div class="d-flex flex-wrap justify-content-end gap-2">
              <a class="btn btn-sm btn-outline-primary" href="{% url 'accounts:user_update' account.pk %}">Sửa</a>
              <a class="btn btn-sm btn-outline-secondary" href="{% url 'accounts:user_password_reset' account.pk %}">Đặt lại mật khẩu</a>
              {% if account.pk != request.user.pk %}<a class="btn btn-sm btn-outline-danger" href="{% url 'accounts:user_delete' account.pk %}">Xóa / Khóa</a>{% endif %}
            </div>
          </td>
        </tr>
        {% empty %}<tr><td colspan="6" class="text-center text-secondary py-5">Chưa có tài khoản phù hợp.</td></tr>{% endfor %}
      </tbody>
    </table>
  </div>
  {% include "accounts/pagination.html" %}
</section>
{% endblock %}
```

## tourManager/accounts/templates/accounts/user_password_reset.html

```html
{% extends "base.html" %}
{% block title %}Đặt lại mật khẩu{% endblock %}
{% block content %}
<section class="page-card p-4 mx-auto" style="max-width: 720px;">
  <h1 class="h3">Đặt lại mật khẩu</h1>
  <p class="text-secondary">Tài khoản: <strong>{{ target_user.username }}</strong></p>
  <form method="post" novalidate>
    {% csrf_token %}
    {% include "accounts/form_fields.html" %}
    <button class="btn btn-primary" type="submit">Lưu mật khẩu mới</button>
    <a class="btn btn-outline-secondary" href="{% url 'accounts:user_list' %}">Hủy</a>
  </form>
</section>
{% endblock %}
```

## tourManager/accounts/tests.py

```python
from io import StringIO

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.test import Client, TestCase, TransactionTestCase, override_settings
from django.urls import include, path
from django.views.generic import TemplateView

from catalog.models import Departure, Guide, Service, Supplier, Tour, TourItinerary, Vehicle
from customers.models import Customer

from .mixins import RoleRequiredMixin
from .views import permission_denied


class SalesOnlyView(RoleRequiredMixin, TemplateView):
    allowed_roles = ("Sales",)
    template_name = "accounts/dashboard.html"


urlpatterns = [path("sales-only/", SalesOnlyView.as_view()), path("", include("config.urls"))]
handler403 = permission_denied


@override_settings(ROOT_URLCONF=__name__)
class AccessTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("setup_roles", stdout=StringIO())
        User = get_user_model()
        cls.sales = User.objects.create_user("salesTest", password="testPassword123!")
        cls.sales.groups.add(Group.objects.get(name="Sales"))
        cls.operator = User.objects.create_user("operatorTest", password="testPassword123!")
        cls.operator.groups.add(Group.objects.get(name="Operator"))
        cls.admin = User.objects.create_user("adminTest")
        cls.admin.groups.add(Group.objects.get(name="Admin"))
        cls.superuser = User.objects.create_superuser("superTest", password="testPassword123!")
        cls.no_role = User.objects.create_user("noRole")

    def test_anonymous_is_redirected_to_login(self):
        response = self.client.get("/sales-only/")
        self.assertRedirects(response, "/login/?next=/sales-only/")

    def test_wrong_role_receives_custom_403(self):
        self.client.force_login(self.operator)
        response = self.client.get("/sales-only/")
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, "Bạn chưa được cấp quyền", status_code=403)

    def test_superuser_and_admin_bypass_role_restriction(self):
        for user in (self.admin, self.superuser, self.sales):
            with self.subTest(user=user.username):
                self.client.force_login(user)
                self.assertEqual(self.client.get("/sales-only/").status_code, 200)

    def test_authenticated_user_without_role_is_forbidden(self):
        self.client.force_login(self.no_role)
        self.assertEqual(self.client.get("/").status_code, 403)
        self.assertEqual(self.client.get("/login/").status_code, 200)

    def test_sidebar_and_context_follow_roles(self):
        self.client.force_login(self.sales)
        response = self.client.get("/")
        self.assertEqual(response.context["current_role"], "Sales")
        self.assertContains(response, 'href="/bookings/"')
        self.assertNotContains(response, 'href="/assignments/"')
        self.client.force_login(self.operator)
        response = self.client.get("/")
        self.assertContains(response, 'href="/assignments/"')
        self.assertNotContains(response, 'href="/bookings/"')

    def test_multiple_roles_show_both_menus(self):
        self.sales.groups.add(Group.objects.get(name="Operator"))
        self.client.force_login(self.sales)
        response = self.client.get("/")
        self.assertContains(response, 'href="/bookings/"')
        self.assertContains(response, 'href="/assignments/"')

    def test_login_success_and_invalid_password(self):
        response = self.client.post("/login/", {"username": "salesTest", "password": "wrong"})
        self.assertContains(response, "Tên đăng nhập hoặc mật khẩu không đúng.")
        response = self.client.post("/login/", {"username": "salesTest", "password": "testPassword123!"})
        self.assertRedirects(response, "/")

    def test_login_rejects_external_redirect(self):
        response = self.client.post("/login/?next=https://example.com/", {"username": "salesTest", "password": "testPassword123!"})
        self.assertRedirects(response, "/")

    def test_logout_requires_post_and_csrf(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.sales)
        self.assertEqual(client.get("/logout/").status_code, 405)
        client.get("/")
        self.assertEqual(client.post("/logout/").status_code, 403)
        response = client.post("/logout/", HTTP_X_CSRFTOKEN=client.cookies["csrftoken"].value)
        self.assertRedirects(response, "/login/")
        self.assertNotIn("_auth_user_id", client.session)

    def test_setup_roles_is_repeatable_and_assigns_permissions(self):
        before = {g.name: set(g.permissions.values_list("pk", flat=True)) for g in Group.objects.all()}
        call_command("setup_roles", stdout=StringIO())
        after = {g.name: set(g.permissions.values_list("pk", flat=True)) for g in Group.objects.all()}
        self.assertEqual(before, after)
        self.assertTrue(self.sales.has_perm("bookings.add_booking"))
        self.assertTrue(self.sales.has_perm("catalog.view_tour"))
        self.assertFalse(self.sales.has_perm("operations.add_tourexpense"))
        self.assertTrue(self.operator.has_perm("operations.add_tourexpense"))
        self.assertFalse(self.operator.has_perm("bookings.add_payment"))


class SeedTests(TestCase):
    def test_seed_is_repeatable_preserves_passwords_and_has_no_transactions(self):
        from bookings.models import Booking, Payment
        from operations.models import GuideAssignment, TourExpense, VehicleAssignment

        output = StringIO()
        call_command("seed_base", stdout=output)
        self.assertNotIn("| Mật khẩu:", output.getvalue())
        User = get_user_model()
        passwords = dict(User.objects.values_list("username", "password"))
        call_command("seed_base", stdout=StringIO())
        self.assertEqual(passwords, dict(User.objects.values_list("username", "password")))
        self.assertEqual(User.objects.count(), 3)
        self.assertTrue(User.objects.get(username="admin").is_superuser)
        for model, count in [(Supplier, 2), (Service, 4), (Guide, 2), (Vehicle, 2), (Tour, 2), (TourItinerary, 5), (Departure, 3), (Customer, 3)]:
            self.assertEqual(model.objects.count(), count)
            for item in model.objects.all():
                item.full_clean()
        for model in (Booking, Payment, GuideAssignment, VehicleAssignment, TourExpense):
            self.assertEqual(model.objects.count(), 0)


class RegistrationTests(TestCase):
    password = "PurpleRiver!2026"

    def payload(self, **changes):
        data = {"username": "newMember", "full_name": "Nguyễn Thị Minh", "email": "minh@example.com", "password1": self.password, "password2": self.password}
        data.update(changes)
        return data

    def test_register_and_login_are_public(self):
        self.assertEqual(self.client.get("/register/").status_code, 200)
        self.assertContains(self.client.get("/login/"), 'href="/register/"')

    def test_registration_is_inactive_roleless_and_ignores_injected_privileges(self):
        response = self.client.post("/register/", self.payload(is_active="on", is_staff="on", is_superuser="on", role="Admin", groups="1"), follow=True)
        self.assertContains(response, "Đăng ký thành công, vui lòng chờ Admin duyệt")
        user = get_user_model().objects.get(username="newMember")
        self.assertFalse(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.groups.exists())
        self.assertEqual(user.get_full_name(), "Nguyễn Thị Minh")
        self.assertTrue(user.check_password(self.password))
        self.assertNotEqual(user.password, self.password)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_invalid_registration_is_not_saved(self):
        for changes in ({"password1": "123", "password2": "123"}, {"password2": "Mismatch!2026"}, {"email": "invalid"}, {"full_name": ""}):
            response = self.client.post("/register/", self.payload(**changes))
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.context["form"].errors)
            self.assertFalse(get_user_model().objects.filter(username="newMember").exists())

    def test_duplicate_username_is_rejected(self):
        self.client.post("/register/", self.payload())
        response = self.client.post("/register/", self.payload())
        self.assertIn("username", response.context["form"].errors)
        self.assertEqual(get_user_model().objects.filter(username="newMember").count(), 1)

    def test_pending_account_cannot_login_and_has_clear_message(self):
        self.client.post("/register/", self.payload())
        response = self.client.post("/login/", {"username": "newMember", "password": self.password})
        self.assertContains(response, "Tài khoản đang chờ Admin duyệt")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_wrong_password_does_not_reveal_pending_state(self):
        self.client.post("/register/", self.payload())
        response = self.client.post("/login/", {"username": "newMember", "password": "wrong"})
        self.assertContains(response, "Tên đăng nhập hoặc mật khẩu không đúng.")
        self.assertNotContains(response, "Tài khoản đang chờ Admin duyệt")

    def test_locked_account_has_distinct_login_message(self):
        self.client.post("/register/", self.payload())
        user = get_user_model().objects.get(username="newMember")
        user.groups.add(Group.objects.get_or_create(name="Sales")[0])
        response = self.client.post("/login/", {"username": user.username, "password": self.password})
        self.assertContains(response, "Tài khoản đã bị khóa")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_registration_requires_csrf(self):
        client = Client(enforce_csrf_checks=True)
        self.assertEqual(client.post("/register/", self.payload()).status_code, 403)
        client.get("/register/")
        token = client.cookies["csrftoken"].value
        response = client.post("/register/", self.payload(), HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code, 302)


class UserManagementTests(TestCase):
    password = "PurpleRiver!2026"

    @classmethod
    def setUpTestData(cls):
        call_command("setup_roles", stdout=StringIO())
        User = get_user_model()
        cls.admin = User.objects.create_user("manager", first_name="Quản trị viên", email="manager@example.com", is_staff=True)
        cls.admin.groups.add(Group.objects.get(name="Admin"))
        cls.sales = User.objects.create_user("seller", password=cls.password, first_name="Nguyễn", last_name="Văn An", email="seller@example.com")
        cls.sales.groups.add(Group.objects.get(name="Sales"))
        cls.operator = User.objects.create_user("coordinator")
        cls.operator.groups.add(Group.objects.get(name="Operator"))
        cls.pending = User.objects.create_user("applicant", is_active=False, first_name="Người chờ duyệt")
        cls.locked = User.objects.create_user("lockedSeller", is_active=False)
        cls.locked.groups.add(Group.objects.get(name="Sales"))

    def setUp(self):
        self.client.force_login(self.admin)

    def update_payload(self, user, role="Sales", active=True, **changes):
        data = {"full_name": user.get_full_name() or "Họ tên mới", "email": user.email or "member@example.com", "role": Group.objects.get(name=role).pk}
        if active:
            data["is_active"] = "on"
        data.update(changes)
        return data

    def management_urls(self):
        pk = self.sales.pk
        return ["/users/", "/users/create/", f"/users/{pk}/edit/", f"/users/{pk}/delete/", f"/users/{pk}/approve/", f"/users/{pk}/password-reset/"]

    def test_non_admin_gets_403_for_every_user_route_get_and_post(self):
        for actor in (self.sales, self.operator):
            self.client.force_login(actor)
            for url in self.management_urls():
                with self.subTest(actor=actor.username, url=url):
                    self.assertContains(self.client.get(url), "Bạn chưa được cấp quyền", status_code=403)
                    self.assertEqual(self.client.post(url, {}).status_code, 403)

    def test_anonymous_user_routes_are_forbidden(self):
        self.client.logout()
        for url in self.management_urls():
            self.assertEqual(self.client.get(url).status_code, 403)
            self.assertEqual(self.client.post(url, {}).status_code, 403)

    def test_admin_can_create_each_role_with_correct_flags(self):
        User = get_user_model()
        for role in ("Admin", "Sales", "Operator"):
            data = {"username": f"new{role}", "full_name": "Nhân viên mới", "email": f"new{role}@example.com", "password1": self.password, "password2": self.password, "role": Group.objects.get(name=role).pk, "is_active": "on"}
            response = self.client.post("/users/create/", data)
            self.assertEqual(response.status_code, 302)
            user = User.objects.get(username=f"new{role}")
            self.assertEqual(list(user.groups.values_list("name", flat=True)), [role])
            self.assertEqual(user.is_staff, role == "Admin")
            self.assertFalse(user.is_superuser)
            self.assertTrue(user.is_active)
            self.assertTrue(user.check_password(self.password))

    def test_assigning_role_replaces_groups_and_revokes_superuser(self):
        target = get_user_model().objects.create_user("legacySuper", is_staff=True, is_superuser=True)
        target.groups.set(Group.objects.filter(name__in=["Admin", "Sales"]))
        response = self.client.post(f"/users/{target.pk}/edit/", self.update_payload(target, "Operator"))
        self.assertEqual(response.status_code, 302)
        target.refresh_from_db()
        self.assertEqual(list(target.groups.values_list("name", flat=True)), ["Operator"])
        self.assertFalse(target.is_staff)
        self.assertFalse(target.is_superuser)

    def test_promotion_to_admin_sets_staff(self):
        self.client.post(f"/users/{self.sales.pk}/edit/", self.update_payload(self.sales, "Admin"))
        self.sales.refresh_from_db()
        self.assertTrue(self.sales.is_staff)
        self.assertEqual(list(self.sales.groups.values_list("name", flat=True)), ["Admin"])

    def test_approval_requires_post_and_explicit_valid_role(self):
        url = f"/users/{self.pending.pk}/approve/"
        self.assertEqual(self.client.get(url).status_code, 405)
        response = self.client.post(url, {}, follow=True)
        self.assertContains(response, "Vui lòng chọn một vai trò hợp lệ")
        self.pending.refresh_from_db()
        self.assertFalse(self.pending.is_active)
        self.client.post(url, {"role": Group.objects.get(name="Sales").pk})
        self.pending.refresh_from_db()
        self.assertTrue(self.pending.is_active)
        self.assertEqual(list(self.pending.groups.values_list("name", flat=True)), ["Sales"])

    def test_repeated_approval_does_not_change_assigned_role(self):
        url = f"/users/{self.pending.pk}/approve/"
        self.client.post(url, {"role": Group.objects.get(name="Sales").pk})
        response = self.client.post(url, {"role": Group.objects.get(name="Admin").pk}, follow=True)
        self.assertContains(response, "đã được duyệt")
        self.assertEqual(list(self.pending.groups.values_list("name", flat=True)), ["Sales"])

    def test_last_active_admin_cannot_be_disabled_or_demoted(self):
        url = f"/users/{self.admin.pk}/edit/"
        for role, active in (("Admin", False), ("Sales", True)):
            response = self.client.post(url, self.update_payload(self.admin, role, active))
            self.assertContains(response, "Admin cuối cùng")
            self.admin.refresh_from_db()
            self.assertTrue(self.admin.is_active)
            self.assertTrue(self.admin.groups.filter(name="Admin").exists())

    def test_inactive_admin_does_not_count_as_replacement(self):
        other = get_user_model().objects.create_user("inactiveAdmin", is_active=False, is_staff=True)
        other.groups.add(Group.objects.get(name="Admin"))
        response = self.client.post(f"/users/{self.admin.pk}/delete/")
        self.assertContains(response, "Admin cuối cùng")
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)

    def test_admin_cannot_disable_or_delete_self_even_with_another_admin(self):
        other = get_user_model().objects.create_superuser("otherAdmin", email="other@example.com")
        other.groups.add(Group.objects.get(name="Admin"))
        response = self.client.post(f"/users/{self.admin.pk}/delete/")
        self.assertContains(response, "chính mình")
        response = self.client.post(f"/users/{self.admin.pk}/edit/", self.update_payload(self.admin, "Admin", False, full_name="Không được lưu"))
        self.assertContains(response, "chính mình")
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)
        self.assertEqual(self.admin.first_name, "Quản trị viên")

    def test_delete_unused_user_requires_confirmation_and_preserves_on_get(self):
        url = f"/users/{self.pending.pk}/delete/"
        self.assertContains(self.client.get(url), "Xác nhận xóa")
        self.assertTrue(get_user_model().objects.filter(pk=self.pending.pk).exists())
        self.assertEqual(self.client.post(url).status_code, 302)
        self.assertFalse(get_user_model().objects.filter(pk=self.pending.pk).exists())

    def make_booking(self, creator):
        from datetime import date
        from decimal import Decimal
        from bookings.models import Booking
        tour = Tour.objects.create(code="ACC", name="Tour kiểm thử", days=1, nights=0, destination="Hạ Long", base_price=Decimal("1000000"))
        departure = Departure.objects.create(tour=tour, start_date=date(2026, 12, 5), end_date=date(2026, 12, 5), max_seats=20, price=Decimal("1000000"))
        customer = Customer.objects.create(full_name="Khách mẫu", phone="0900000000")
        return Booking.objects.create(code="ACCBK", customer=customer, departure=departure, total_amount=Decimal("1000000"), created_by=creator)

    def test_user_with_booking_is_locked_instead_of_deleted(self):
        booking = self.make_booking(self.sales)
        response = self.client.post(f"/users/{self.sales.pk}/delete/", follow=True)
        self.assertContains(response, "được khóa và giữ lại dữ liệu")
        self.sales.refresh_from_db()
        self.assertFalse(self.sales.is_active)
        self.assertEqual(booking.created_by_id, self.sales.pk)
        self.assertEqual(list(self.sales.groups.values_list("name", flat=True)), ["Sales"])

    def test_user_with_only_received_payment_is_also_locked(self):
        from bookings.models import Payment
        booking = self.make_booking(self.admin)
        payment = Payment.objects.create(booking=booking, amount=100000, payment_type="DEPOSIT", method="CASH", received_by=self.sales)
        self.client.post(f"/users/{self.sales.pk}/delete/")
        self.sales.refresh_from_db()
        self.assertFalse(self.sales.is_active)
        self.assertTrue(Payment.objects.filter(pk=payment.pk, received_by=self.sales).exists())

    def test_search_full_name_role_status_and_pagination(self):
        response = self.client.get("/users/", {"q": "Nguyễn Văn An", "role": "Sales", "status": "active"})
        self.assertEqual([user.pk for user in response.context["users"]], [self.sales.pk])
        for index in range(12):
            get_user_model().objects.create_user(f"Waiting{index:02}", is_active=False)
        response = self.client.get("/users/", {"q": "Waiting", "status": "pending"})
        self.assertEqual(response.context["paginator"].count, 12)
        self.assertEqual(len(response.context["users"]), 10)
        self.assertContains(response, "q=Waiting&amp;status=pending&amp;page=2")
        self.assertEqual(len(self.client.get("/users/", {"q": "Waiting", "status": "pending", "page": 2}).context["users"]), 2)

    def test_pending_and_locked_filters_are_distinct(self):
        pending = self.client.get("/users/", {"status": "pending"})
        locked = self.client.get("/users/", {"status": "locked"})
        self.assertEqual([user.pk for user in pending.context["users"]], [self.pending.pk])
        self.assertEqual([user.pk for user in locked.context["users"]], [self.locked.pk])
        self.assertContains(pending, 'class="table-warning"')

    def test_invalid_filters_do_not_crash(self):
        response = self.client.get("/users/", {"status": "INVALID"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["filter_form"].errors)

    def test_pending_badge_only_shown_to_admin(self):
        response = self.client.get("/")
        self.assertEqual(response.context["pending_user_count"], 1)
        self.assertContains(response, 'href="/users/"')
        self.client.force_login(self.sales)
        response = self.client.get("/")
        self.assertEqual(response.context["pending_user_count"], 0)
        self.assertNotContains(response, 'href="/users/"')
        self.assertContains(response, 'href="/profile/"')
        self.assertContains(response, 'href="/password-change/"')

    def test_user_mutations_require_csrf(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.admin)
        for url in ("/users/create/", f"/users/{self.sales.pk}/edit/", f"/users/{self.pending.pk}/approve/", f"/users/{self.sales.pk}/delete/", f"/users/{self.sales.pk}/password-reset/"):
            self.assertEqual(client.post(url, {}).status_code, 403)

    def test_django_admin_cannot_bypass_account_management(self):
        for url in (f"/admin/auth/user/{self.sales.pk}/change/", f"/admin/auth/user/{self.admin.pk}/delete/", "/admin/auth/user/add/", f"/admin/auth/group/{Group.objects.get(name='Admin').pk}/change/"):
            self.assertEqual(self.client.post(url, {}).status_code, 403)
        self.assertEqual(self.client.get(f"/admin/auth/user/{self.sales.pk}/change/").status_code, 200)

    def test_password_reset_invalidates_other_sessions(self):
        old_session = Client()
        old_session.force_login(self.sales)
        new_password = "AnotherRiver!2027"
        response = self.client.post(f"/users/{self.sales.pk}/password-reset/", {"new_password1": new_password, "new_password2": new_password})
        self.assertEqual(response.status_code, 302)
        self.sales.refresh_from_db()
        self.assertTrue(self.sales.check_password(new_password))
        self.assertEqual(old_session.get("/profile/").status_code, 302)
        self.assertNotIn("_auth_user_id", old_session.session)

    def test_self_reset_keeps_admin_session(self):
        response = self.client.post(f"/users/{self.admin.pk}/password-reset/", {"new_password1": "AnotherRiver!2027", "new_password2": "AnotherRiver!2027"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.get("/users/").status_code, 200)


class ProfileTests(TestCase):
    password = "PurpleRiver!2026"

    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user("profileUser", password=cls.password, first_name="Tên cũ", email="old@example.com")
        cls.user.groups.add(Group.objects.get_or_create(name="Sales")[0])

    def setUp(self):
        self.client.force_login(self.user)

    def test_profile_only_changes_name_and_email(self):
        response = self.client.post("/profile/", {"full_name": "Nguyễn Văn Mới", "email": "new@example.com", "username": "hacked", "is_superuser": "on", "is_staff": "on", "role": "Admin"})
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.get_full_name(), "Nguyễn Văn Mới")
        self.assertEqual(self.user.email, "new@example.com")
        self.assertEqual(self.user.username, "profileUser")
        self.assertFalse(self.user.is_superuser)
        self.assertFalse(self.user.is_staff)
        self.assertEqual(list(self.user.groups.values_list("name", flat=True)), ["Sales"])

    def test_profile_and_password_change_require_login(self):
        self.client.logout()
        self.assertEqual(self.client.get("/profile/").status_code, 302)
        self.assertEqual(self.client.get("/password-change/").status_code, 302)

    def test_password_change_validates_old_password_and_keeps_session(self):
        data = {"old_password": "wrong", "new_password1": "AnotherRiver!2027", "new_password2": "AnotherRiver!2027"}
        response = self.client.post("/password-change/", data)
        self.assertIn("old_password", response.context["form"].errors)
        data["old_password"] = self.password
        self.assertEqual(self.client.post("/password-change/", data).status_code, 302)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("AnotherRiver!2027"))
        self.assertEqual(self.client.get("/profile/").status_code, 200)

    def test_password_change_rejects_weak_password(self):
        response = self.client.post("/password-change/", {"old_password": self.password, "new_password1": "123", "new_password2": "123"})
        self.assertTrue(response.context["form"].errors)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(self.password))

    def test_stale_profile_form_does_not_reactivate_a_locked_user(self):
        from .forms import ProfileForm
        form = ProfileForm({"full_name": "Tên mới", "email": "new@example.com"}, instance=self.user)
        self.assertTrue(form.is_valid())
        get_user_model().objects.filter(pk=self.user.pk).update(is_active=False)
        form.save()
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)

    def test_stale_password_form_does_not_reactivate_a_locked_user(self):
        from .forms import AdminPasswordResetForm
        form = AdminPasswordResetForm(self.user, {"new_password1": "AnotherRiver!2027", "new_password2": "AnotherRiver!2027"})
        self.assertTrue(form.is_valid())
        get_user_model().objects.filter(pk=self.user.pk).update(is_active=False)
        form.save()
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)


class CreateAdminTests(TestCase):
    password = "PurpleRiver!2026"

    def test_command_creates_roles_and_is_repeatable_without_password_output(self):
        output = StringIO()
        call_command("create_admin", username="cliAdmin", email="first@example.com", password=self.password, stdout=output)
        user = get_user_model().objects.get(username="cliAdmin")
        first_pk = user.pk
        self.assertTrue(user.is_superuser and user.is_staff and user.is_active)
        self.assertEqual(list(user.groups.values_list("name", flat=True)), ["Admin"])
        user.groups.add(Group.objects.get(name="Sales"))
        user.is_active = False
        user.save(update_fields=["is_active"])
        new_password = "AnotherRiver!2027"
        call_command("create_admin", username="cliAdmin", email="second@example.com", password=new_password, stdout=output)
        user.refresh_from_db()
        self.assertEqual(user.pk, first_pk)
        self.assertEqual(user.email, "second@example.com")
        self.assertTrue(user.is_superuser and user.is_staff and user.is_active)
        self.assertEqual(list(user.groups.values_list("name", flat=True)), ["Admin"])
        self.assertTrue(user.check_password(new_password))
        self.assertNotIn(self.password, output.getvalue())
        self.assertNotIn(new_password, output.getvalue())

    def test_command_reads_env_file(self):
        import os
        from pathlib import Path
        from tempfile import TemporaryDirectory
        from unittest.mock import patch
        with TemporaryDirectory() as directory, override_settings(BASE_DIR=directory), patch.dict(os.environ):
            for key in ("ADMIN_USERNAME", "ADMIN_EMAIL", "ADMIN_PASSWORD"):
                os.environ.pop(key, None)
            Path(directory, ".env").write_text(f"ADMIN_USERNAME=envAdmin\nADMIN_EMAIL=env@example.com\nADMIN_PASSWORD={self.password}\n")
            output = StringIO()
            call_command("create_admin", stdout=output)
            user = get_user_model().objects.get(username="envAdmin")
            self.assertEqual(user.email, "env@example.com")
            self.assertTrue(user.check_password(self.password))
            self.assertNotIn(self.password, output.getvalue())

    def test_missing_password_uses_getpass(self):
        import os
        from unittest.mock import patch
        with patch.dict(os.environ, {"ADMIN_PASSWORD": ""}), patch("accounts.management.commands.create_admin.getpass", return_value=self.password) as prompt:
            call_command("create_admin", username="promptAdmin", email="prompt@example.com", stdout=StringIO())
        self.assertEqual(prompt.call_count, 2)
        self.assertTrue(get_user_model().objects.get(username="promptAdmin").check_password(self.password))

    def test_weak_password_is_rejected(self):
        from django.core.management.base import CommandError
        with self.assertRaises(CommandError):
            call_command("create_admin", username="weakAdmin", email="weak@example.com", password="123", stdout=StringIO())
        self.assertFalse(get_user_model().objects.filter(username="weakAdmin").exists())

    def test_getpass_mismatch_is_rejected(self):
        import os
        from unittest.mock import patch
        from django.core.management.base import CommandError
        with patch.dict(os.environ, {"ADMIN_PASSWORD": ""}), patch("accounts.management.commands.create_admin.getpass", side_effect=[self.password, "AnotherRiver!2027"]):
            with self.assertRaises(CommandError):
                call_command("create_admin", username="mismatchAdmin", stdout=StringIO())
        self.assertFalse(get_user_model().objects.filter(username="mismatchAdmin").exists())

    def test_seed_does_not_promote_pending_username_admin_or_print_passwords(self):
        pending = get_user_model().objects.create_user("admin", is_active=False)
        output = StringIO()
        call_command("seed_base", stdout=output)
        pending.refresh_from_db()
        self.assertFalse(pending.is_active)
        self.assertFalse(pending.is_staff)
        self.assertFalse(pending.is_superuser)
        self.assertFalse(pending.groups.exists())
        self.assertNotIn("| Mật khẩu:", output.getvalue())


class ConcurrentAdminProtectionTests(TransactionTestCase):
    def test_two_admins_cannot_disable_each_other_at_the_same_time(self):
        from concurrent.futures import ThreadPoolExecutor
        from threading import Barrier
        from django.core.exceptions import ValidationError
        from django.db import close_old_connections, connections
        from .services import save_user_account

        role = Group.objects.create(name="Admin")
        users = []
        for username in ("firstAdmin", "secondAdmin"):
            user = get_user_model().objects.create_user(username, is_staff=True)
            user.groups.add(role)
            users.append(user)
        barrier = Barrier(2)

        def disable(actor_pk, target_pk):
            close_old_connections()
            try:
                actor = get_user_model().objects.get(pk=actor_pk)
                target = get_user_model().objects.get(pk=target_pk)
                group = Group.objects.get(name="Admin")
                barrier.wait(timeout=10)
                try:
                    save_user_account(target, group, False, actor=actor)
                    return "disabled"
                except ValidationError:
                    return "blocked"
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(disable, users[0].pk, users[1].pk), pool.submit(disable, users[1].pk, users[0].pk)]
            results = [future.result(timeout=20) for future in futures]
        self.assertCountEqual(results, ["disabled", "blocked"])
        self.assertEqual(get_user_model().objects.filter(is_active=True, groups__name="Admin").count(), 1)
```

## tourManager/accounts/urls.py

```python
from django.urls import path

from . import views

app_name = "accounts"
urlpatterns = [
    path("", views.DashboardView.as_view(), name="dashboard"),
    path("login/", views.UserLoginView.as_view(), name="login"),
    path("logout/", views.UserLogoutView.as_view(), name="logout"),
    path("register/", views.RegisterView.as_view(), name="register"),
    path("users/", views.UserListView.as_view(), name="user_list"),
    path("users/create/", views.UserCreateView.as_view(), name="user_create"),
    path("users/<int:pk>/edit/", views.UserUpdateView.as_view(), name="user_update"),
    path("users/<int:pk>/delete/", views.UserDeleteView.as_view(), name="user_delete"),
    path("users/<int:pk>/approve/", views.UserApproveView.as_view(), name="user_approve"),
    path("users/<int:pk>/password-reset/", views.UserPasswordResetView.as_view(), name="user_password_reset"),
    path("profile/", views.ProfileView.as_view(), name="profile"),
    path("password-change/", views.SelfPasswordChangeView.as_view(), name="password_change"),
]
```

## tourManager/accounts/views.py

```python
from django.contrib import messages
from django.contrib.auth import get_user_model, update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.db.models import CharField, Q, Value
from django.db.models.functions import Concat
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.debug import sensitive_post_parameters
from django.views.generic import CreateView, DeleteView, FormView, ListView, TemplateView, UpdateView

from .forms import AdminPasswordResetForm, AdminUserCreateForm, AdminUserUpdateForm, ApproveUserForm, ConfirmationForm, LoginForm, ProfileForm, RegistrationForm, SelfPasswordChangeForm, UserFilterForm
from .mixins import RoleRequiredMixin
from .roles import ROLE_NAMES
from .services import approve_user, delete_or_lock_user, is_pending_user, pending_users, role_label

User = get_user_model()


class UserLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = LoginForm

    def form_valid(self, form):
        messages.success(self.request, "Đăng nhập thành công.")
        return super().form_valid(form)


class UserLogoutView(LogoutView):
    # Django 5 dùng POST để đăng xuất, đi kèm CSRF token ở thanh điều hướng.
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        messages.success(request, "Bạn đã đăng xuất.")
        return response


class DashboardView(RoleRequiredMixin, TemplateView):
    allowed_roles = ROLE_NAMES
    template_name = "accounts/dashboard.html"


@method_decorator(sensitive_post_parameters(), name="dispatch")
class RegisterView(CreateView):
    form_class = RegistrationForm
    template_name = "accounts/register.html"
    success_url = reverse_lazy("accounts:login")

    def form_valid(self, form):
        try:
            with transaction.atomic():
                self.object = form.save()
        except IntegrityError:
            if User.objects.filter(username=form.cleaned_data["username"]).exists():
                form.add_error("username", "Tên đăng nhập đã được sử dụng.")
                return self.form_invalid(form)
            raise
        messages.success(self.request, "Đăng ký thành công, vui lòng chờ Admin duyệt")
        return HttpResponseRedirect(self.get_success_url())


class AdminRequiredMixin(RoleRequiredMixin):
    allowed_roles = ()

    def handle_no_permission(self):
        # Các trang /users/ trả 403 đẹp cả khi chưa đăng nhập.
        raise PermissionDenied("Chỉ Admin được quản lý người dùng.")


class UserListView(AdminRequiredMixin, ListView):
    model = User
    template_name = "accounts/user_list.html"
    paginate_by = 10
    context_object_name = "users"

    def get_queryset(self):
        queryset = User.objects.prefetch_related("groups").annotate(
            full_name_text=Concat("first_name", Value(" "), "last_name", output_field=CharField()),
        ).order_by("username", "pk")
        self.filter_form = UserFilterForm(self.request.GET)
        if not self.filter_form.is_valid():
            return queryset.none()
        data = self.filter_form.cleaned_data
        q = data.get("q", "").strip()
        if q:
            queryset = queryset.filter(Q(username__icontains=q) | Q(full_name_text__icontains=q) | Q(email__icontains=q))
        role = data.get("role")
        if role == "Admin":
            queryset = queryset.filter(Q(is_superuser=True) | Q(groups__name="Admin"))
        elif role:
            queryset = queryset.filter(groups__name=role)
        status = data.get("status")
        if status == "active":
            queryset = queryset.filter(is_active=True)
        elif status == "pending":
            queryset = queryset.filter(pk__in=pending_users().values("pk"))
        elif status == "locked":
            queryset = queryset.filter(is_active=False).exclude(pk__in=pending_users().values("pk"))
        return queryset.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        for user in context["users"]:
            user.display_role = role_label(user)
            user.is_pending = is_pending_user(user)
        query = self.request.GET.copy()
        query.pop("page", None)
        context.update(filter_form=self.filter_form, pagination_query=query.urlencode(), approve_form=ApproveUserForm())
        return context


class UserSaveMixin:
    success_url = reverse_lazy("accounts:user_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Sửa người dùng" if getattr(self, "object", None) else "Thêm người dùng"
        return context

    def form_valid(self, form):
        try:
            self.object = form.save()
        except ValidationError as error:
            form.add_error(None, error)
            return self.form_invalid(form)
        messages.success(self.request, "Đã lưu người dùng và vai trò thành công.")
        return HttpResponseRedirect(self.get_success_url())


@method_decorator(sensitive_post_parameters(), name="dispatch")
class UserCreateView(AdminRequiredMixin, UserSaveMixin, CreateView):
    model = User
    form_class = AdminUserCreateForm
    template_name = "accounts/user_form.html"


class UserUpdateView(AdminRequiredMixin, UserSaveMixin, UpdateView):
    model = User
    form_class = AdminUserUpdateForm
    template_name = "accounts/user_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["actor"] = self.request.user
        return kwargs


class UserApproveView(AdminRequiredMixin, View):
    http_method_names = ["post"]

    def post(self, request, pk):
        get_object_or_404(User, pk=pk)
        form = ApproveUserForm(request.POST)
        if not form.is_valid():
            messages.error(request, "Vui lòng chọn một vai trò hợp lệ để duyệt tài khoản.")
        else:
            try:
                approve_user(pk, form.cleaned_data["role"], request.user)
                messages.success(request, "Đã duyệt tài khoản và gán vai trò thành công.")
            except ValidationError as error:
                messages.error(request, " ".join(error.messages))
        return redirect("accounts:user_list")


class UserDeleteView(AdminRequiredMixin, DeleteView):
    model = User
    form_class = ConfirmationForm
    template_name = "accounts/user_confirm_delete.html"
    success_url = reverse_lazy("accounts:user_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["has_related_data"] = self.object.created_bookings.exists() or self.object.received_payments.exists()
        return context

    def form_valid(self, form):
        try:
            action = delete_or_lock_user(self.object.pk, self.request.user)
        except ValidationError as error:
            form.add_error(None, error)
            return self.form_invalid(form)
        message = "Tài khoản đã có dữ liệu liên quan nên được khóa và giữ lại dữ liệu." if action == "locked" else "Đã xóa tài khoản chưa phát sinh dữ liệu."
        messages.success(self.request, message)
        return HttpResponseRedirect(self.get_success_url())


@method_decorator(sensitive_post_parameters(), name="dispatch")
class UserPasswordResetView(AdminRequiredMixin, FormView):
    template_name = "accounts/user_password_reset.html"
    form_class = AdminPasswordResetForm
    success_url = reverse_lazy("accounts:user_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = get_object_or_404(User, pk=self.kwargs["pk"])
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["target_user"] = context["form"].user
        return context

    def form_valid(self, form):
        user = form.save()
        if user.pk == self.request.user.pk:
            update_session_auth_hash(self.request, user)
        messages.success(self.request, "Đã đặt lại mật khẩu thành công.")
        return super().form_valid(form)


class ProfileView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = ProfileForm
    template_name = "accounts/profile.html"
    success_url = reverse_lazy("accounts:profile")

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, "Đã cập nhật hồ sơ cá nhân.")
        return super().form_valid(form)


class SelfPasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    template_name = "accounts/password_change.html"
    form_class = SelfPasswordChangeForm
    success_url = reverse_lazy("accounts:profile")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Đã đổi mật khẩu thành công.")
        return response


def permission_denied(request, exception):
    return render(request, "403.html", status=403)
```

## tourManager/templates/base.html

```html
<!doctype html>
<html lang="vi">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{% block title %}tourManager{% endblock %} | Quản lý du lịch</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
  <style>
    :root { --sidebar-width: 246px; --navy: #10283f; }
    body { background: #f3f6fa; color: #24364b; }
    .app-sidebar { background: var(--navy); color: #fff; width: var(--sidebar-width) !important; }
    .app-sidebar .nav-link { color: #c3d0df; padding: .55rem .9rem; border-radius: .5rem; }
    .app-sidebar .nav-link:hover, .app-sidebar .nav-link.active { color: #fff; background: #244862; }
    .nav-heading { color: #8eabc1; font-size: .7rem; letter-spacing: .12em; margin: 1.5rem .9rem .5rem; }
    .brand { font-size: 1.35rem; font-weight: 700; color: #fff; text-decoration: none; }
    .app-navbar { min-height: 76px; background: #fff; border-bottom: 1px solid #e0e7ef; }
    .page-card { border: 1px solid #e0e7ef; border-radius: 1rem; background: #fff; }
    .login-shell { min-height: 85vh; display: grid; place-items: center; }
    .login-card { width: min(100%, 440px); }
    @media (min-width: 992px) {
      .app-sidebar { position: fixed; inset: 0 auto 0 0; overflow-y: auto; }
      .app-main { margin-left: var(--sidebar-width); }
    }
  </style>
  {% block extra_css %}{% endblock %}
</head>
<body>
{% if user.is_authenticated %}
  <aside class="offcanvas-lg offcanvas-start app-sidebar p-3" tabindex="-1" id="appSidebar" aria-labelledby="sidebarTitle">
    <div class="d-flex align-items-center justify-content-between pb-3 border-bottom border-secondary">
      <a class="brand" href="/" id="sidebarTitle">tourManager<span class="text-info">.</span></a>
      <button type="button" class="btn-close btn-close-white d-lg-none" data-bs-dismiss="offcanvas" data-bs-target="#appSidebar" aria-label="Đóng menu"></button>
    </div>
    <div class="small mt-3 text-white-50">CÔNG TY LỮ HÀNH</div>
    <nav class="nav flex-column mt-3" aria-label="Menu chính">
      {% if can_view_catalog %}
      <a class="nav-link {% if request.path == '/' %}active{% endif %}" href="/">Tổng quan</a>
      <div class="nav-heading">DANH MỤC</div>
      <a class="nav-link {% if request.path == '/suppliers/' %}active{% endif %}" href="/suppliers/">Nhà cung cấp</a>
      <a class="nav-link {% if request.path == '/services/' %}active{% endif %}" href="/services/">Dịch vụ</a>
      <a class="nav-link {% if request.path == '/guides/' %}active{% endif %}" href="/guides/">Hướng dẫn viên</a>
      <a class="nav-link {% if request.path == '/vehicles/' %}active{% endif %}" href="/vehicles/">Xe du lịch</a>
      <a class="nav-link {% if request.path == '/tours/' %}active{% endif %}" href="/tours/">Tour du lịch</a>
      <a class="nav-link {% if request.path == '/departures/' %}active{% endif %}" href="/departures/">Lịch khởi hành</a>
      {% endif %}
      {% if can_manage_customers or can_manage_bookings %}
      <div class="nav-heading">KINH DOANH</div>
      {% endif %}
      {% if can_manage_customers %}
      <a class="nav-link {% if request.path == '/customers/' %}active{% endif %}" href="/customers/">Khách hàng</a>
      {% endif %}
      {% if can_manage_bookings %}
      <a class="nav-link {% if request.path == '/bookings/' %}active{% endif %}" href="/bookings/">Đặt tour</a>
      <a class="nav-link {% if request.path == '/payments/' %}active{% endif %}" href="/payments/">Thanh toán</a>
      {% endif %}
      {% if can_manage_operations %}
      <div class="nav-heading">ĐIỀU HÀNH</div>
      <a class="nav-link {% if request.path == '/assignments/' %}active{% endif %}" href="/assignments/">Phân công HDV và xe</a>
      <a class="nav-link {% if request.path == '/expenses/' %}active{% endif %}" href="/expenses/">Chi phí tour</a>
      {% endif %}
      {% if can_view_reports %}
      <div class="nav-heading">THỐNG KÊ</div>
      <a class="nav-link {% if request.path == '/reports/' %}active{% endif %}" href="/reports/">Báo cáo</a>
      {% endif %}
      {% if is_admin_role %}
      <div class="nav-heading">HỆ THỐNG</div>
      <a class="nav-link d-flex justify-content-between align-items-center" href="{% url 'accounts:user_list' %}">Người dùng <span class="badge text-bg-warning" aria-label="Số tài khoản chờ duyệt">{{ pending_user_count }}</span></a>
      {% if user.is_staff %}<a class="nav-link" href="/admin/">Quản trị dữ liệu</a>{% endif %}
      {% endif %}
    </nav>
  </aside>
{% endif %}
<div class="{% if user.is_authenticated %}app-main{% endif %}">
  <header class="app-navbar d-flex align-items-center justify-content-between gap-3 px-3 px-md-4">
    <div class="d-flex align-items-center gap-3">
      {% if user.is_authenticated %}
      <button class="btn btn-outline-secondary d-lg-none" type="button" data-bs-toggle="offcanvas" data-bs-target="#appSidebar" aria-controls="appSidebar" aria-label="Mở menu">☰</button>
      {% endif %}
      <span class="fw-semibold">Quản lý dịch vụ du lịch &amp; điều hành tour</span>
    </div>
    {% if user.is_authenticated %}
    <div class="d-flex align-items-center gap-3 flex-shrink-0">
      {% include "accounts/user_dropdown.html" %}
    </div>
    {% endif %}
  </header>
  <main class="container-fluid p-3 p-md-4">
    {% for message in messages %}
    <div class="alert alert-{{ message.tags|default:'info' }} alert-dismissible fade show" role="alert">
      {{ message }}
      <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Đóng thông báo"></button>
    </div>
    {% endfor %}
    {% block content %}{% endblock %}
  </main>
</div>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
{% block extra_js %}{% endblock %}
</body>
</html>
```
