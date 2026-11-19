# Quy ước phát triển song song

## Quyền sở hữu tệp

| Nhóm | Được sửa |
|---|---|
| 1 | catalog/views.py, forms.py, urls.py, tests.py, templates/catalog/; customers/views.py, forms.py, urls.py, tests.py, templates/customers/ |
| 2 | bookings, operations, reports: views.py, forms.py, urls.py, tests.py và templates tương ứng; riêng accounts/views.py chỉ phần DashboardView và accounts/templates/accounts/dashboard.html |
| Dùng chung đã chốt | requirements.txt, config/, accounts còn lại, templates/base.html, templates/403.html, toàn bộ models.py, apps.py, admin.py, migrations/, management commands |

Giai đoạn 1 không đổi models/migrations và tệp dùng chung. Nếu phát hiện thiếu field cần trao đổi trước khi sửa; không tự chạy makemigrations trên hai nhánh. Người phụ trách tích hợp sửa tài liệu dùng chung sau khi hai bên thống nhất.

## Quy ước UI và URL

- Dùng class-based views của Django; kiểm tra vai trò bằng `RoleRequiredMixin` đặt trước view.
- ModelForm đặt trong `<app>/forms.py`, không đặt trong views.py.
- Template đặt trong `<app>/templates/<app>/`; mỗi trang extends `base.html` và điền block `title`, `content`.
- Tìm kiếm bằng `?q=`, phân trang `paginate_by = 10`; liên kết phân trang phải giữ giá trị q bằng urlencode.
- Tên URL: `<model>_list`, `<model>_create`, `<model>_update`, `<model>_delete`, `<model>_detail`.
- `<model>` là tên class viết thường: `supplier`, `service`, `guide`, `vehicle`, `tour`, `touritinerary`, `departure`, `customer`, `booking`, `payment`, `guideassignment`, `vehicleassignment`, `tourexpense`.
- Dùng namespace, ví dụ `catalog:tour_list`, `customers:customer_list`, `bookings:booking_list`, `operations:tourexpense_list`.
- Mẫu đường dẫn: `/tours/` (list), `/tours/create/`, `/tours/<int:pk>/`, `/tours/<int:pk>/edit/`, `/tours/<int:pk>/delete/`.
- `/assignments/` dùng `operations:guideassignment_list`; bảng phân công xe có thể đặt `/assignments/vehicles/`, tên `operations:vehicleassignment_list`. Menu chung trỏ đến `/assignments/`.
- `/expenses/` dùng tên `operations:tourexpense_list`; `/reports/` dùng `reports:report_list` vì báo cáo không có model.
- TourItinerary có thể là form con trong chi tiết tour, không cần thêm menu cấp cao.
- `/` giữ tên `accounts:dashboard`; nhóm 2 thay phần nội dung DashboardView và template hiện tại, không thêm root URL thứ hai.
- Khai báo mỗi app có `app_name`; root include đã có sẵn nên không sửa config/urls.py khi thêm trang.
- Query string, số trang, form không hợp lệ và lỗi quyền đều phải xử lý phía server; POST dùng csrf_token.

## Quyền view cần dùng ở giai đoạn 1

| Hành động | allowed_roles |
|---|---|
| Xem danh mục và báo cáo | ("Sales", "Operator") |
| Thêm/sửa/xóa danh mục | () |
| Khách hàng, booking, thanh toán | ("Sales",) |
| Phân công và chi phí | ("Operator",) |

Admin và superuser được qua mọi trường hợp. `setup_roles` đã có model permissions tương ứng; nếu thêm `PermissionRequiredMixin` ở giai đoạn 1 cần bảo đảm không vô tình chặn quy tắc vượt quyền Admin đã chốt.

## Làm việc với hai nhánh

Hai nhánh xuất phát từ cùng bộ khung trên main:

```bash
git clone https://github.com/dqming1876/tourManager.git
cd tourManager
git fetch origin
```

Nhóm 1:

```bash
git switch --track origin/codex/catalogTeam
```

Nhóm 2:

```bash
git switch --track origin/codex/operationsTeam
```

Nếu tự tạo hai nhánh từ main trong repo mới:

```bash
git switch main
git pull --ff-only origin main
git branch codex/catalogTeam
git branch codex/operationsTeam
git push -u origin codex/catalogTeam
git push -u origin codex/operationsTeam
```

Trong quá trình làm:

```bash
git status
git add catalog customers
git commit -m "Add catalog and customer screens"
git push
```

Khối ví dụ trên dành cho nhóm 1. Nhóm 2 chỉ stage thư mục được phân công; dùng `git diff --cached --name-only` để kiểm tra trước khi commit. Hai bên mở Pull Request vào main, người còn lại kiểm tra và merge từng PR. Không force-push main.

Sau khi một PR khác được merge, đồng bộ nhánh đang làm:

```bash
git fetch origin
git merge origin/main
python manage.py migrate
python manage.py test
```

Database và `.env` nằm riêng trên từng máy; không chia sẻ thư mục MySQL hoặc file mật khẩu qua Git. Tất cả migration giai đoạn 0 phải giữ trong repo. Ranh giới tệp trên giúp hai nhóm tránh sửa cùng một chỗ.
