# Minh chứng 4.3 — Package, phụ thuộc và kiểm thử headless

```mermaid
flowchart TB
    gui["GUI · dist"] -->|"HTTP JSON"| api["API · backend/app.py"]
    api --> service["BLL · backend/services.py"]
    service --> domain["Domain · backend/domain.py"]
    service --> ports["Hợp đồng · backend/ports.py"]
    dal["DAL · backend/repositories.py"] -->|"hiện thực"| ports
    dal -->|"dựng thực thể"| domain
    dal --> dto["DTO · backend/views.py"]
    dal --> db["Database · D1"]
```

Luồng gọi lúc chạy là GUI → API → Service → repository → DB. Chiều phụ thuộc tĩnh là Service → Domain và hợp đồng của ứng dụng; Repository hiện thực phía ngoài. `entry.py` là điểm lắp đặt và biết các lớp cụ thể.

| Mở file | Điều cần kiểm tra |
| --- | --- |
| [operations.js](../dist/operations.js) và [admin.js](../dist/admin.js) | Form đọc dữ liệu, kiểm nhập liệu và gọi HTTP bằng `operationsApi`. Các hàm Form không chứa SQL. |
| [app.py](../backend/app.py) | Route nhận Service đã lắp; đọc JSON, điều hướng và trả response. |
| [services.py](../backend/services.py), [services.py](../backend/services.py) và [services.py](../backend/services.py) | BLL dùng miền và hợp đồng port, không import lớp DAL, DOM hoặc thư viện DB. |
| [domain.py](../backend/domain.py) | Domain chỉ phụ thuộc các module miền. Guard và phép tính chạy khi không có trình duyệt hoặc DB. |
| [repositories.py](../backend/repositories.py) và [views.py](../backend/views.py) | Repository giữ SQL tham số hóa. DTO chuyển tên trường `day → date` và chỉ xuất các giá trị HTTP cần. |

Bài test kiến trúc đọc import tĩnh trong toàn bộ `backend/`, duyệt đồ thị để phát hiện chu kỳ, kiểm chiều phụ thuộc Domain/API/Service và dò câu lệnh SQL phổ biến trong ba tầng này. `npm test` chạy trong Python 3.12. Bài test 4.5 gọi điểm vào HTTP với dữ liệu lưu trong RAM; bài test trục 3 gọi BLL trực tiếp để kiểm chứng guard khi không có UI. [Kiểm thử](../tests/test_architecture.py)

**Đánh đổi.** Nếu ghép SQL và phiên vào Form Worker, ca tạo đơn `BookingService.place_booking` sẽ cần môi trường DB hoặc UI để kiểm thử. Chia lớp tăng số điểm phải mở khi đọc một yêu cầu và đòi hỏi kiểm tra DTO cùng hợp đồng. Với truy vấn chỉ dùng một lần ở script độc lập, chi phí chia tầng có thể lớn hơn lợi ích tái sử dụng.
