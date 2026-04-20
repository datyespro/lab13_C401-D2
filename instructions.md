# Hướng Dẫn Lab 13: Observability

## Tổng Quan Lab
Đây là lab 4 giờ về Monitoring, Logging và Observability. Bạn sẽ xây dựng một ứng dụng FastAPI "agent" với các tính năng:
- **Structured JSON logging**: Ghi logs dưới định dạng JSON có cấu trúc, dễ phân tích và tìm kiếm hơn logs text thông thường, giúp tự động hóa monitoring.
- **Correlation ID propagation**: Truyền một ID duy nhất qua toàn hệ thống cho mỗi request, giúp liên kết logs và traces để debug dễ dàng trong môi trường microservices.
- **PII scrubbing**: Loại bỏ thông tin cá nhân nhạy cảm (như email, số điện thoại) khỏi logs để bảo vệ quyền riêng tư và tuân thủ quy định bảo mật.
- **Langfuse tracing**: Sử dụng công cụ Langfuse để theo dõi chi tiết luồng thực thi của requests, ghi lại thời gian và lỗi để phân tích hiệu suất.
- **Minimal metrics aggregation**: Thu thập và tổng hợp các chỉ số cơ bản như response time, error rate, để monitor sức khỏe hệ thống mà không quá phức tạp.
- **SLOs, alerts và blueprint report**: Định nghĩa Service Level Objectives (mục tiêu dịch vụ), cấu hình cảnh báo tự động khi vi phạm ngưỡng, và tạo báo cáo chi tiết về thiết kế hệ thống.

Template này chưa hoàn chỉnh, bạn cần hoàn thành các TODO trong quá trình lab.

## Các Bước Cần Làm (Sau Khi Setup)

1. **Chạy Starter App**: Khởi động ứng dụng FastAPI cơ bản để quan sát logs hiện tại. Logs ở đây là các bản ghi sự kiện của hệ thống, nhưng ban đầu sẽ rất cơ bản và thiếu correlation IDs (ID duy nhất để liên kết các logs của cùng một request, giúp debug dễ dàng). Bạn sẽ thấy logs không có cấu trúc rõ ràng và khó theo dõi.

2. **Implement Correlation IDs**: Sửa file `app/middleware.py` để thêm middleware tạo ra một `x-request-id` duy nhất cho mỗi request HTTP. Correlation ID propagation nghĩa là truyền ID này qua tất cả các thành phần của hệ thống, giúp theo dõi toàn bộ luồng xử lý của một request từ đầu đến cuối, đặc biệt hữu ích khi có nhiều dịch vụ microservices.

3. **Enrich Logs**: Cập nhật `app/main.py` để bind (gắn) thêm context như user, session và feature vào mỗi log entry. Structured JSON logging sẽ giúp logs có định dạng JSON dễ phân tích, bao gồm thông tin phong phú hơn để hiểu ngữ cảnh của từng sự kiện, thay vì chỉ ghi text đơn giản.

4. **Sanitize Data**: Triển khai PII scrubber (chức năng loại bỏ thông tin cá nhân nhạy cảm) trong `app/logging_config.py`. PII scrubbing bảo vệ quyền riêng tư bằng cách ẩn hoặc xóa dữ liệu như email, số điện thoại khỏi logs trước khi ghi, để tránh rò rỉ thông tin cá nhân trong quá trình logging.

5. **Verify với Script**: Chạy `python scripts/validate_logs.py` để kiểm tra tiến độ. Script này sẽ validate (xác thực) xem logs đã đúng schema (cấu trúc) chưa, đảm bảo chúng tuân thủ logging_schema.json và bao gồm tất cả các trường cần thiết như correlation ID, context, v.v.

6. **Tracing**: Gửi 10-20 requests đến app (có thể dùng load_test.py) và kiểm tra traces trong Langfuse. Tracing là theo dõi luồng thực thi chi tiết của từng request, sử dụng `observe` decorator để wrap các hàm và ghi lại thời gian, lỗi. Langfuse là công cụ để visualize (hiển thị trực quan) các traces này.

7. **Dashboards**: Xây dựng một dashboard với 6 panels từ metrics đã export. Metrics aggregation thu thập và tổng hợp chỉ số như response time, error rate. Dashboard là giao diện trực quan để monitor (giám sát) sức khỏe hệ thống theo thời gian thực.

8. **Alerting**: Cấu hình alert rules trong `config/alert_rules.yaml` và test chúng. Alerting là hệ thống cảnh báo tự động khi metrics vi phạm ngưỡng (ví dụ: error rate > 5%), dựa trên SLOs (Service Level Objectives) như uptime 99.9%. Bạn sẽ test bằng cách inject incidents (chèn lỗi giả) và xem alerts có trigger không.

## Tooling Sử Dụng

- **Generate requests**: `python scripts/load_test.py --concurrency 5`
- **Inject failures**: `python scripts/inject_incident.py --scenario rag_slow`
- **Check progress**: `python scripts/validate_logs.py`

## Kết Quả Cuối Cùng Cần Nộp

### Group Score (60%):
- **Technical Implementation (30 pts)**: Verified by `validate_logs.py` và live system state.
- **Incident Response (10 pts)**: Accuracy của root cause analysis trong report.
- **Live Demo (20 pts)**: Team presentation và system demonstration.

### Individual Score (40%):
- **Individual Report (20 pts)**: Quality của contributions cụ thể trong `docs/blueprint-template.md`.
- **Git Evidence (20 pts)**: Traceable work via commits và code ownership.

### Passing Criteria:
- Tất cả `TODO` blocks phải completed.
- Minimum 10 traces visible trong Langfuse.
- Dashboard phải show all 6 required panels.

## Team Roles Gợi Ý
- Member A: logging + PII
- Member B: tracing + tags
- Member C: SLO + alerts
- Member D: load test + incident injection
- Member E: dashboard + evidence
- Member F: blueprint + demo lead

## Lưu Ý Quan Trọng
- Đảm bảo hoàn thành tất cả TODOs.
- Test hệ thống với load test và incident injection.
- Chuẩn bị demo và report theo blueprint template.

## Giải Thích Đầy Đủ Các Thuật Ngữ

Dưới đây là giải thích chi tiết các thuật ngữ chính xuất hiện trong file này:

- **Observability**: Khả năng quan sát và hiểu trạng thái của hệ thống thông qua logs, metrics và traces. Nó giúp phát hiện và khắc phục sự cố nhanh chóng.

- **Monitoring**: Quá trình giám sát liên tục các chỉ số và hoạt động của hệ thống để đảm bảo hiệu suất và độ tin cậy.

- **Logging**: Ghi lại các sự kiện và thông tin trong hệ thống dưới dạng logs để phân tích sau này.

- **Structured JSON Logging**: Cách ghi logs dưới định dạng JSON có cấu trúc, dễ dàng phân tích và tìm kiếm so với logs dạng text thông thường.

- **Correlation ID Propagation**: Việc truyền tải một ID duy nhất (correlation ID) qua các thành phần của hệ thống để theo dõi một request từ đầu đến cuối.

- **PII Scrubbing**: Quá trình loại bỏ hoặc ẩn thông tin cá nhân nhạy cảm (Personally Identifiable Information) khỏi logs để bảo vệ quyền riêng tư.

- **Langfuse Tracing**: Công cụ tracing (theo dõi) để ghi lại luồng thực thi của các request, giúp debug và phân tích hiệu suất.

- **Minimal Metrics Aggregation**: Thu thập và tổng hợp các chỉ số cơ bản như thời gian phản hồi, tỷ lệ lỗi để theo dõi sức khỏe hệ thống.

- **SLOs (Service Level Objectives)**: Mục tiêu mức dịch vụ, như tỷ lệ uptime hoặc thời gian phản hồi tối đa mà hệ thống phải đạt được.

- **Alerts**: Cảnh báo tự động khi hệ thống vi phạm các ngưỡng định sẵn, giúp phản ứng nhanh với sự cố.

- **Blueprint Report**: Báo cáo chi tiết về thiết kế và triển khai hệ thống, dùng để nộp và đánh giá.

- **TODO**: Viết tắt của "To Do", chỉ các nhiệm vụ cần hoàn thành trong code.

- **Correlation IDs**: ID duy nhất gắn với mỗi request để liên kết logs và traces.

- **PII (Personally Identifiable Information)**: Thông tin có thể xác định danh tính cá nhân, như email, số điện thoại.

- **Tracing**: Theo dõi luồng thực thi của một request qua các dịch vụ.

- **Dashboards**: Bảng điều khiển trực quan hiển thị metrics và logs để giám sát hệ thống.

- **Alerting**: Hệ thống gửi cảnh báo khi phát hiện vấn đề.

- **Group Score**: Điểm số nhóm, dựa trên công việc tập thể.

- **Individual Score**: Điểm số cá nhân, dựa trên đóng góp riêng.

- **Technical Implementation**: Triển khai kỹ thuật, như code và cấu hình.

- **Incident Response**: Phản ứng với sự cố, bao gồm phân tích nguyên nhân.

- **Live Demo**: Trình diễn trực tiếp hệ thống đang chạy.

- **Git Evidence**: Bằng chứng qua commits trên Git về công việc đã làm.

- **Passing Criteria**: Tiêu chí để pass lab, như hoàn thành TODOs và đạt số traces tối thiểu.

- **Team Roles**: Vai trò trong nhóm để phân chia công việc.






# Kế hoạch Triển khai Lab 13 - Observability (Timeline 3 Tiếng)

## 💡 Đề tài Chatbot: "IT Helpdesk & Policy Support" (Trợ lý Hỗ trợ IT & Chính sách VinUni)
**Tại sao chọn đề tài này?** Dựa vào file mock data (`sample_queries.jsonl`), đề tài này khớp 100% với dữ liệu có sẵn. Chatbot đóng vai trò giải đáp các thắc mắc về chính sách hoàn tiền học phí, hỗ trợ kỹ thuật và bảo mật dữ liệu. 
**Điểm ăn tiền:** Khi Demo, đề tài này giúp nhóm bạn phô diễn tính năng **PII Scrubbing** (che dữ liệu nhạy cảm) cực kỳ tự nhiên. Sinh viên sẽ nhập vào đoạn chat các thông tin như: Email `@vinuni.edu.vn`, số điện thoại cá nhân, và thẻ Visa đóng học phí. Việc hệ thống tự động nhận diện và "che mờ" các thông tin này sẽ giúp nhóm ăn trọn điểm kỹ thuật.

---

## ⚖️ Phân chia Task (Đảm bảo ai cũng code để lấy điểm Git Evidence)

Vì giảng viên yêu cầu **40 điểm cá nhân (20 điểm Git + 20 điểm Report)**, nên tuyệt đối không có vai trò nào chỉ ngồi "chỉ tay" hoặc vẽ vời giao diện. Cả 6 người ĐỀU PHẢI CODE và tạo Pull Request.

### 👤 Thành viên 1: Core Logging Engineer
- **File phụ trách:** `app/logging_config.py` và `app/main.py`.
- **Nhiệm vụ:** Viết code cấu hình thư viện `structlog`. Đảm bảo console in ra chuẩn định dạng JSON, có chứa đầy đủ các trường `user_id`, `session_id`.
- **Nghiệm thu:** Chạy file `validate_logs.py` không văng lỗi định dạng cơ bản.

### 👤 Thành viên 2: Security & Privacy Engineer (PII)
- **File phụ trách:** `app/pii.py` và `app/schemas.py`.
- **Nhiệm vụ:** Tách biệt hẳn với phần Logging cơ bản, bạn này chuyên viết Regex. Viết logic nhận diện và biến đổi:
  - Phone: `0987...` -> `[REDACTED_PHONE]`
  - Email: `...` -> `[REDACTED_EMAIL]`
  - Thẻ Visa: `4111...` -> `[REDACTED_CC]`
- **Nghiệm thu:** Chạy mock data chứa số thẻ tín dụng, log in ra đã bị che hoàn toàn.

### 👤 Thành viên 3: Tracing & Middleware Engineer
- **File phụ trách:** `app/middleware.py` và `app/tracing.py`.
- **Nhiệm vụ:** Code phần Middleware của FastAPI để chặn mọi request đi vào, sinh ra mã `uuid4` (x-request-id), sau đó nhét nó vào Context Variables. Thiết lập hàm kết nối API với Langfuse.
- **Nghiệm thu:** Mọi dòng log ở bất kỳ file nào (app, agent, RAG) in ra đều tự động mang theo `x-request-id` chung.

### 👤 Thành viên 4: Metrics & Alerting Engineer
- **File phụ trách:** `app/metrics.py` và `config/alert_rules.yaml`.
- **Nhiệm vụ:** Code bộ đếm (counter) cho các request lỗi và request thành công. Viết cấu hình `.yaml` định nghĩa điều kiện báo động (ví dụ: error > 5%).
- **Nghiệm thu:** Tạo ra các thông số ảo để thử nghiệm, file yaml được load thành công không lỗi cú pháp.

### 👤 Thành viên 5: Chaos & SRE Engineer
- **File phụ trách:** `scripts/load_test.py`, `scripts/inject_incident.py` và `config/slo.yaml`.
- **Nhiệm vụ:** Chỉnh sửa (sửa code) file `load_test.py` để bắn tải ngẫu nhiên theo luồng đa luồng (multi-threading/concurrency) thật gắt gao. Cấu hình file `slo.yaml` mô tả chịu tải của hệ thống. Chịu trách nhiệm thiết kế Dashboard.
- **Nghiệm thu:** Khi hệ thống chạy song song 20 requests, có khả năng bắt được biểu đồ Latency tăng vọt trên Dashboard.

### 👤 Thành viên 6: AI Agent & Team Lead
- **File phụ trách:** `app/agent.py` và `docs/blueprint-template.md`.