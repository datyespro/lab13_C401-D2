# Kế hoạch Triển khai Lab 13 - Observability (Timeline 3 Tiếng)

Vì đây là một buổi Lab kéo dài 3 tiếng (180 phút), chiến thuật tốt nhất là **làm việc song song**. Mỗi người nhận một file/tác vụ độc lập để tránh đụng độ code (merge conflict), sau đó ghép lại ở 45 phút cuối.

---

## ⏱ Timeline Tổng Quan

- **Phút 0 - 30 (Khởi động):** Setup Git, tạo nhánh, chạy thử ứng dụng gốc.
- **Phút 30 - 120 (Code song song):** 5 thành viên code chức năng, Lead chuẩn bị dàn bài báo cáo.
- **Phút 120 - 150 (Tích hợp & Debug):** Gộp code (Merge), Thành viên 4 chạy giả lập tải để tạo dữ liệu cho Dashboard.
- **Phút 150 - 180 (Hoàn thiện):** Điền báo cáo cá nhân, tập diễn tập kịch bản Demo.

---

## 👨‍💻 Phân công Task cụ thể (Làm việc song song)

### 👤 Thành viên 1: Logging & PII (Trọng tâm)
*File làm việc: `app/logging_config.py`, `app/pii.py`, `app/main.py`*
- **Task 1 (30p):** Cấu hình `structlog` để định dạng toàn bộ output thành JSON.
- **Task 2 (40p):** Viết Regex trong `app/pii.py` che 3 loại dữ liệu:
  - Email (vd: `student@vinuni.edu.vn` -> `s***@vinuni.edu.vn`).
  - Số điện thoại (vd: `0987654321` -> `[REDACTED]`).
  - Thẻ tín dụng (vd: `4111 1111...` -> `[REDACTED_CC]`).
- **Task 3 (20p):** Chạy `python scripts/validate_logs.py` liên tục cho đến khi pass.

### 👤 Thành viên 2: Tracing & Middleware
*File làm việc: `app/middleware.py`, `app/tracing.py`, `app/agent.py`*
- **Task 1 (30p):** Viết logic trong `app/middleware.py` sinh ra `uuid4` gán vào header `x-request-id`.
- **Task 2 (30p):** Truyền `x-request-id` này vào context của `structlog` để log nào cũng có ID này.
- **Task 3 (30p):** Cấu hình API keys Langfuse. Thêm decorator `@observe` vào các hàm gọi RAG và LLM trong `agent.py`. Bắn thử vài request để check trên web Langfuse.

### 👤 Thành viên 3: Metrics, SLOs & Alerts
*File làm việc: `app/metrics.py`, `config/slo.yaml`, `config/alert_rules.yaml`*
- **Task 1 (45p):** Hoàn thiện `app/metrics.py` (cài đặt bộ đếm request, đo latency).
- **Task 2 (20p):** Định nghĩa 2-3 chỉ số SLO trong `config/slo.yaml` (ví dụ: 95% requests < 200ms).
- **Task 3 (25p):** Định nghĩa file cảnh báo (Alert) và viết 1 file Runbook đơn giản hướng dẫn xử lý khi hệ thống bị chậm.

### 👤 Thành viên 4: Testing & Chaos (Kiểm thử & Bơm lỗi)
*File làm việc: `scripts/load_test.py`, `scripts/inject_incident.py`*
- **Task 1 (30p):** Đọc hiểu cách script Load Test hoạt động, tùy chỉnh lại số lượng request.
- **Task 2 (30p):** Ở phút thứ 120, chạy script tạo tải để giả lập có nhiều người dùng chat cùng lúc.
- **Task 3 (30p):** Bơm lỗi (`--scenario rag_slow` hoặc `tool_fail`). Phối hợp với Thành viên 1, 2, 5 xem lỗi hiện lên Log/Dashboard như thế nào, sau đó ghi chú lại để viết báo cáo.

### 👤 Thành viên 5: Dashboard Visualization
*File làm việc: Môi trường Langfuse/Grafana (Tùy lab)*
- **Task 1 (45p):** Dựa vào file `docs/dashboard-spec.md` tạo sẵn 6 Panels trống trên giao diện UI.
- **Task 2 (45p):** Chờ Thành viên 4 bắn tải thành công (phút 120), kéo dữ liệu thực tế vào biểu đồ (Error rate, Latency, Request count, Token cost...). Căn chỉnh cho đẹp để kiếm điểm Bonus.

### 👤 Thành viên 6: Tech Lead & Documentation
*File làm việc: Github, `docs/blueprint-template.md`, `docs/grading-evidence.md`*
- **Task 1 (30p):** Tạo repo, cấp quyền cho 5 bạn kia, tạo các branch riêng (`feat-logging`, `feat-tracing`...).
- **Task 2 (30p):** Mở sẵn file báo cáo `blueprint-template.md`, chia mục cho từng người.
- **Task 3 (30p):** Đóng vai trò duyệt code (Merge PR) ở phút thứ 120. Đảm bảo app chạy không bị lỗi khi gộp code.
- **Task 4 (30p):** Làm "MC" cho phần Demo. Tập nói theo kịch bản: Giới thiệu hệ thống -> Thành viên 4 bơm lỗi -> Show Dashboard đỏ báo động -> Mở Log/Trace tìm nguyên nhân.
