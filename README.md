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
