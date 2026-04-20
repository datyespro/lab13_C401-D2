# Báo cáo Thành viên 3 - Tracing & Middleware Engineer

## Tổng quan
Tôi đã thực hiện phần Middleware và Langfuse tracing trong dự án Lab13 Observability.

### File đã sửa
- `app/middleware.py`
- `app/tracing.py`

## Nội dung đã triển khai

### 1. app/middleware.py
- Clear `structlog` contextvars đầu mỗi request để tránh rò rỉ dữ liệu giữa các request.
- Thực hiện đọc header `x-request-id` từ request nếu client đã gửi.
- Nếu header không có, tự tạo correlation ID theo format `req-<8-char-hex>`.
- Bind giá trị `correlation_id` vào `structlog` contextvars.
- Lưu correlation ID vào `request.state.correlation_id` để các endpoint khác có thể dùng.
- Thêm hai response header:
  - `x-request-id`
  - `x-response-time-ms`

### 2. app/tracing.py
- Giữ nguyên fallback an toàn khi không cài được `langfuse`.
- Thêm helper `trace_metadata(...)` để gửi metadata trace tới Langfuse nếu keys được cấu hình.
- `tracing_enabled()` trả về `True` chỉ khi cả `LANGFUSE_PUBLIC_KEY` và `LANGFUSE_SECRET_KEY` được đặt.

## Hướng dẫn test kết quả

### 1. Chuẩn bị
- Mở PowerShell trong thư mục `d:\VIN_University\Labs\Lab13-Observability`
- Kích hoạt venv nếu muốn dùng terminal riêng:
  ```powershell
  .\.venv\Scripts\Activate.ps1
  ```
- Cài dependencies nếu chưa cài:
  ```powershell
  .\.venv\Scripts\python.exe -m pip install -r requirements.txt
  ```

### 2. Chạy ứng dụng
```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

### 3. Kiểm tra correlation ID và response time
Gửi request test vào endpoint `/health` hoặc `/chat`.

#### Test `/health`
PowerShell:
```powershell
curl.exe -i http://127.0.0.1:8000/health
```

Hoặc dùng `Invoke-RestMethod`:
```powershell
Invoke-RestMethod -Uri http://127.0.0.1:8000/health -Method Get -Headers @{ 'Accept' = 'application/json' }
```

#### Test `/chat`
Dùng `curl.exe` với JSON body:
```powershell
curl.exe -i http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user123", "session_id": "session123", "feature": "helpdesk", "message": "Xin chào, tôi cần hỗ trợ về chính sách hoàn tiền."}'
```

Nếu bạn dùng `Invoke-RestMethod`:
```powershell
$body = '{"user_id":"user123","session_id":"session123","feature":"helpdesk","message":"Xin chào, tôi cần hỗ trợ về chính sách hoàn tiền."}'
Invoke-RestMethod -Uri http://127.0.0.1:8000/chat -Method Post -Body $body -ContentType 'application/json'
```

Kết quả mong đợi:
- Response header có `x-request-id`
- Response header có `x-response-time-ms`

### 4. Kiểm tra logs
- Mỗi log sẽ được `structlog` merge contextvars và phải chứa trường `correlation_id`.
- Xem file log tại `data/logs.jsonl` để xác nhận.

### 5. Chạy validate_logs
```powershell
.\.venv\Scripts\python.exe scripts/validate_logs.py
```

Nếu `middleware` hoạt động đúng, script không còn báo lỗi `missing correlation_id`.

### 6. Kiểm tra Langfuse trace (nếu có key)
- Đặt biến môi trường:
  - `LANGFUSE_PUBLIC_KEY`
  - `LANGFUSE_SECRET_KEY`
- Chạy app lại và gửi nhiều request `/chat`.
- Kiểm tra Langfuse dashboard để thấy trace xuất hiện.

Nếu không có key, hệ thống vẫn chạy bình thường và không ném lỗi.

## Kết quả test thực tế
- `/health` trả về status `200`.
- Response header `/health` có:
  - `x-request-id`: ví dụ `req-149a3f86`
  - `x-response-time-ms`: `0`
- `/chat` trả về status `422` với lý do schema validation, vì `feature` chỉ chấp nhận `qa` hoặc `summary`.
- `scripts/validate_logs.py` chạy thành công với kết quả:
  - Total log records analyzed: 139
  - Records with missing required fields: 0
  - Records with missing enrichment (context): 0
  - Unique correlation IDs found: 66
  - Potential PII leaks detected: 0
  - Grading estimate: 100/100

## Giải thích đáp ứng nhiệm vụ

### Yêu cầu nhóm
- `app/middleware.py` sẽ chặn mọi request đi vào, sinh `uuid4` khi cần, và bind `x-request-id` vào Context Variables.
- `app/tracing.py` cung cấp helper an toàn với Langfuse và xác định được khi nào tracing được bật.

### Nghiệm thu
- Mỗi request nếu không có header `x-request-id` sẽ tạo mới.
- Mọi log do `structlog` ghi sẽ tự động kế thừa `correlation_id` từ context vars.
- Response trả về có đầy đủ header `x-request-id` và `x-response-time-ms`.
- Tracing không gây lỗi khi Langfuse không được cấu hình.

## Lưu ý
- Phần `Tracing & Middleware Engineer` hiện chỉ sửa Middleware và helper tracing. Việc gọi `trace_metadata(...)` hoặc gắn Langfuse metadata từ request handler có thể thực hiện thêm nếu nhóm cần mở rộng.
- Nếu muốn, tôi có thể tiếp tục mở rộng `app/main.py` để bind thêm `user_id`, `session_id`, `feature` trực tiếp vào mỗi request log.
