# Minh chứng 4.6 — Strategy, Adapter và mở rộng OCP

| Mẫu GoF | Vấn đề và vai trò | Cách chọn lúc chạy |
| --- | --- | --- |
| **Strategy — Behavioral** | Báo cáo có ba công thức và cấu trúc bảng. `ReportPresenter` là Context; hợp đồng của Strategy là `title` và `summarize(data)`. `CashReport`, `BookingReport`, `CapacityReport` là Concrete Strategies. | Người dùng chọn loại báo cáo. `loadReport` chuyển mã vào Presenter, Presenter ủy quyền chiến lược đã đăng ký. Bảng, XLSX và phần in đọc chung kết quả. [Code](../dist/report-strategies.js) |
| **Object Adapter — Structural** | Repository dùng port `Database` gồm `first/all/execute/batch`. `D1Database` chuyển kiểu dữ liệu qua FFI và giữ batch D1. `SQLiteDatabase` bọc `sqlite3`, trả cùng hình dạng dữ liệu và thực thi batch trong BEGIN/COMMIT hoặc ROLLBACK. | Worker nhận binding D1 ở môi trường Cloudflare. Root demo/test cấp adapter SQLite. Các repository gọi cùng Target và tự chạy trên backend đang được lắp. [D1Database](../entry.py) · [SQLiteDatabase](../scripts/sqlite_worker.py) |

## Bài mở rộng tại chỗ

Tạo một Concrete Strategy hoàn tiền. Để dùng trong trình duyệt, thêm lớp và đăng ký một mục `refunds: new RefundOnlyReport()` tại nơi tạo registry. Không sửa `ReportPresenter`, `loadReport()`, HTML của bộ lọc hay các Strategy đang có.

```js
class RefundOnlyReport {
  get title() { return 'Chỉ hoàn tiền'; }

  summarize({ cash }) {
    return {
      headers: ['Tháng', 'Hoàn tiền (VND)'],
      rows: cash.map(row => [row.month, row.refunded]),
      total: ['Tổng cộng', cash.reduce((sum, row) => sum + row.refunded, 0)],
      note: 'Kỳ lọc tính theo ngày ghi nhận tiền.',
    };
  }
}
```

Test 4.6 lắp registry mở rộng và gọi cả báo cáo gốc và biến thể mới. Dữ liệu mẫu thu 1.200.000 ₫ và hoàn 500.000 ₫. Chiến lược thu/hoàn tính 700.000 ₫ thu ròng; biến thể chỉ hoàn trả 500.000 ₫. Bản ứng dụng hiện dùng ba loại báo cáo ban đầu; lớp mới nằm trong bài thực hành kiểm thử. Có thể gõ lại biến thể khi live coding với giảng viên. [Kiểm thử](../tests/frontend/reports.test.js)

## Đánh đổi

- Strategy làm tăng số lớp và cần đăng ký biến thể. Một nhánh cố định đơn giản dùng hàm thường sẽ dễ hơn. Việc chọn nhầm contract có thể gây bảng và tệp xuất thiếu cột, vì vậy mỗi Strategy cần test cả cấu trúc kết quả.
- Adapter duy trì thêm một lớp chuyển đổi. SQLite cục bộ giúp chạy nhanh và tái lập, nhưng không mô phỏng quota, độ trễ mạng hay mọi đặc tính của Cloudflare D1. Các tính chất đó phải đo trên môi trường đích khi triển khai.
