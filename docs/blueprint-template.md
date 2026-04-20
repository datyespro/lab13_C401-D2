# Day 13 Observability Lab Report

> **Instruction**: Fill in all sections below. This report is designed to be parsed by an automated grading assistant. Ensure all tags (e.g., `[GROUP_NAME]`) are preserved.

## 1. Team Metadata
- [GROUP_NAME]&#58; C401-D2
- [REPO_URL]&#58; https://github.com/datyespro/lab13_C401-D2
- [MEMBERS]&#58;   - Member A: Nguyễn Thành Đạt (2A202600203) | Role: Core Logging Engineer
  - Member B: Nguyễn Hoàng Việt (2A202600162) | Role: Security & Privacy Engineer (PII)
  - Member C: Đậu Văn Quyền (2A202600359) | Role: Tracing & Middleware Engineer
  - Member D: Vũ Duy Linh (2A202600460) | Role: Metrics & Alerting Engineer
  - Member E: Nguyễn Anh Đức (2A202600387) | Role: Chaos & SRE Engineer
  - Member F: Hoàng Ngọc Anh (2A202600067) | Role: AI Agent & Team Lead

---

## 2. Group Performance (Auto-Verified)
- [VALIDATE_LOGS_FINAL_SCORE]&#58; 100/100
- [TOTAL_TRACES_COUNT]&#58; 66
- [PII_LEAKS_FOUND]&#58; 0

---

## 3. Technical Evidence (Group)

### 3.1 Logging & Tracing
- [EVIDENCE_CORRELATION_ID_SCREENSHOT]&#58; docs/evidence/correlation_id_screenshot.png
- [EVIDENCE_PII_REDACTION_SCREENSHOT]&#58; docs/evidence/pii_redaction_screenshot.png
- [EVIDENCE_TRACE_WATERFALL_SCREENSHOT]&#58; docs/evidence/trace_waterfall_screenshot.png
- [TRACE_WATERFALL_EXPLANATION]&#58; Trace waterfall cho request `/chat` cho thấy hai child span dưới parent span `LabAgent.run()`: (1) `retrieve()` — tra cứu tài liệu RAG qua `mock_rag.py`, ngủ 3 giây khi incident `rag_slow` được bật, và (2) `FakeLLM.generate()` — gọi LLM với độ trễ ~150ms và output tokens nhân 4 khi `cost_spike` active. Correlation ID được truyền từ FastAPI middleware qua mọi dòng log và Langfuse observation, đảm bảo tracing end-to-end. Mức độ chi tiết từng span rất quan trọng: khi `rag_slow`, span `retrieve()` đơn lẻ đã vượt ngưỡng P95 SLO 2000ms.

### 3.2 Dashboard & SLOs
- [DASHBOARD_6_PANELS_SCREENSHOT]&#58; docs/evidence/dashboard_6panels.png
- [SLO_TABLE]&#58; | SLI | Target | Window | Current Value |
|---|---|---:|---|
| Latency P95 | < 2000ms | 28d | 850ms |
| Error Rate | < 2% | 28d | 0.3% |
| Cost Budget | < $1.00/day | 1d | $0.18 |

### 3.3 Alerts & Runbook
- [ALERT_RULES_SCREENSHOT]&#58; docs/evidence/alert_rules_screenshot.png
- [SAMPLE_RUNBOOK_LINK]&#58; docs/alerts.md#2-high-error-rate

---

## 4. Incident Response (Group)
- [SCENARIO_NAME]&#58; rag_slow
- [SYMPTOMS_OBSERVED]&#58; Latency P95 nhảy từ ~850ms lên >3000ms trên dashboard. Endpoint `/metrics` cho thấy `latency_p95_ms` tăng vọt cao hơn ngưỡng SLO 2000ms. Thanh SLO trên dashboard chuyển sang màu đỏ ở chỉ báo Latency P95. Các request vẫn trả về HTTP 200 (không lỗi), nhưng độ trễ mà người dùng cảm nhận được nghiêm trọng.
- [ROOT_CAUSE_PROVED_BY]&#58;   - **Trace ID từ Langfuse**: Span `retrieve()` có duration 3015ms — được xác nhận trực tiếp qua Langfuse trace waterfall. Parent span `LabAgent.run()` có tổng duration tương ứng.
  - **Dòng log**: `{"event":"request_received","service":"api","latency_ms":3215,"payload":{"message_preview":"My VPN is not..."}}` với cùng `correlation_id` được truyền từ middleware.
  - **Bằng chứng code**: `app/mock_rag.py` dòng 18 — `time.sleep(3.0)` chỉ thực thi khi `STATE["rag_slow"]` = True (incident được enable qua `POST /incidents/rag_slow/enable`).
- [FIX_ACTION]&#58; Tắt incident bằng `POST /incidents/rag_slow/disable`. Độ trễ ngay lập tức trở về baseline (<1000ms P95). Incident `rag_slow` toggle boolean ở module-level trong `app/incidents.py` mà `mock_rag.py` kiểm tra ở mỗi lần retrieve.
- [PREVENTIVE_MEASURE]&#58; Thêm `rag_slow` vào alert rule `high_latency_p95` (P2, condition: latency_p95 > 2000 trong 1m) trong `config/alert_rules.yaml`. Các đợt tăng độ trễ retrieval trong tương lai sẽ trigger page tự động trước khi breach P95 ảnh hưởng đến người dùng. Đã cấu hình rolling window 5 phút cho SLO burn-rate alert.

---

## 5. Individual Contributions & Evidence

### Nguyễn Thành Đạt (Member A — Core Logging Engineer)
- [TASKS_COMPLETED]&#58;   - Triển khai `app/logging_config.py`: cấu hình toàn bộ structlog pipeline — `merge_contextvars`, `add_log_level`, `TimeStamper` (ISO UTC, key=`ts`), processor `scrub_event` tùy chỉnh, `StackInfoRenderer`, `format_exc_info`, `JsonlFileProcessor` (ghi thêm dòng JSON vào `data/logs.jsonl`), và `JSONRenderer`. Console output là JSON có cấu trúc; file log là JSONL append-only.
  - `JsonlFileProcessor` tạo thư mục `data/` khi ghi lần đầu và render mỗi event qua `JSONRenderer` trước khi append.
  - Tích hợp log enrichment vào `app/main.py`: `bind_contextvars` cho `user_id_hash`, `session_id`, `feature`, `model`, và `env` trên mỗi request `/chat`. Cả `request_received` và `response_sent` đều bao gồm dict `payload` với message/answer preview đã được scrub PII.
  - Xác minh bởi `scripts/validate_logs.py`: 0 required fields thiếu, 0 enrichment fields thiếu trên tất cả 139 bản ghi log.
- [EVIDENCE_LINK]&#58; https://github.com/datyespro/lab13_C401-D2/pull/1 (app/logging_config.py, app/main.py)

### Nguyễn Hoàng Việt (Member B — Security & Privacy Engineer / PII)
- [TASKS_COMPLETED]&#58;   - Triển khai `app/pii.py`: định nghĩa dict `PII_PATTERNS` với 8 regex patterns bao gồm số thẻ tín dụng (`cc`: format 16 chữ số Visa/Mastercard), địa chỉ email (RFC 5322-compliant), số điện thoại Việt Nam (format: `0xxx`, `+84xxx`, có dấu gạch/phân cách), CCCD (12 chữ số), hộ chiếu Việt Nam (1-2 chữ cái + 7-8 chữ số), và từ khóa địa chỉ Việt Nam (Hà Nội và TP.HCM). Ngoài ra còn có pattern `ssn_like` 9 chữ số.
  - `scrub_text()` duyệt tất cả patterns và thay thế mỗi match bằng `[REDACTED_<TYPE>]` viết hoa (ví dụ: `[REDACTED_EMAIL]`, `[REDACTED_CC]`).
  - `summarize_text()` bọc `scrub_text()` với cắt ngắn 80 ký tự — được sử dụng trong `app/main.py` cho `payload.message_preview` và `payload.answer_preview`.
  - `hash_user_id()` dùng SHA256 (12 ký tự hex đầu) để giả mạo hóa user ID trước khi xuất hiện trong logs và Langfuse traces.
  - `scrub_text()` được gọi bởi processor `scrub_event` trong `logging_config.py`, đảm bảo PII được redact trước khi bất kỳ log entry nào đến `data/logs.jsonl` hoặc console.
  - Đã test với tất cả 10 entries từ `data/sample_queries_pii.jsonl` — xác nhận 0 PII leaks (`validate_logs.py` xác nhận: "Potential PII leaks detected: 0").
- [EVIDENCE_LINK]&#58; https://github.com/datyespro/lab13_C401-D2/pull/4 (app/pii.py)

### Đậu Văn Quyền (Member C — Tracing & Middleware Engineer)
- [TASKS_COMPLETED]&#58;   - Triển khai `app/middleware.py`: `CorrelationIdMiddleware` — clear structlog contextvars ở đầu mỗi request (ngăn rò rỉ dữ liệu giữa các request), đọc `x-request-id` từ request headers (hỗ trợ client-provided IDs), tạo `req-{8-char-hex}` bằng `uuid.uuid4().hex[:8]` nếu header không có, bind `correlation_id` vào structlog context vars, lưu vào `request.state.correlation_id` để endpoint truy cập, đo elapsed time bằng `time.perf_counter()`, và thêm response headers `x-request-id` và `x-response-time-ms`.
  - Triển khai `app/tracing.py`: tích hợp Langfuse với graceful fallback (dummy decorator/class khi langfuse chưa cài). `tracing_enabled()` trả về True chỉ khi cả `LANGFUSE_PUBLIC_KEY` và `LANGFUSE_SECRET_KEY` env vars được set. Helper `trace_metadata()` gửi metadata đến Langfuse trace hiện tại khi enabled.
  - Tất cả log entries trên mọi module (main.py, agent.py, mock_rag.py, mock_llm.py) tự động bao gồm `correlation_id` chung từ context vars — xác minh bởi `validate_logs.py`: 66 unique correlation IDs trên 139 bản ghi.
  - Hệ thống chạy không lỗi trong môi trường không có Langfuse keys (graceful degradation).
- [EVIDENCE_LINK]&#58; https://github.com/datyespro/lab13_C401-D2/pull/6 (app/middleware.py, app/tracing.py) — được document trong `member3_report.md`

### Vũ Duy Linh (Member D — Metrics & Alerting Engineer)
- [TASKS_COMPLETED]&#58;   - Triển khai `app/metrics.py`: metrics aggregation in-memory với các global lists cho `REQUEST_LATENCIES`, `REQUEST_COSTS`, `REQUEST_TOKENS_IN`, `REQUEST_TOKENS_OUT`, `QUALITY_SCORES`, Counter cho `ERRORS`, và counter `TRAFFIC`. `record_request()` và `record_error()` đều tăng `TRAFFIC`. Hàm `percentile()` tùy chỉnh tính P50/P95/P99. `snapshot()` trả về dict với tất cả metrics bao gồm `error_rate_pct`, `avg_cost_usd`, `total_cost_usd`, `tokens_in_total`, `tokens_out_total`, `error_breakdown`, và `quality_avg`.
  - Viết `config/alert_rules.yaml`: định nghĩa 4 alert rules:
    - `high_latency_p95` (P2, symptom-based): latency_p95 > 2000ms trong 1m, owner=team-oncall, runbook=docs/alerts.md#1-high-latency-p95
    - `high_error_rate` (P1, symptom-based): error_rate_pct > 5% trong 1m, owner=team-oncall, runbook=docs/alerts.md#2-high-error-rate
    - `cost_budget_spike` (P2, symptom-based): total_cost_usd > 1.0 trong 5m, owner=finops-owner, runbook=docs/alerts.md#3-cost-budget-spike
    - `low_quality_score` (P3, symptom-based): quality_avg < 0.7 trong 5m, owner=team-oncall, runbook=docs/alerts.md#4-low-quality-score
  - Viết `docs/alerts.md`: runbooks cho tất cả 4 alerts bao gồm các bước kiểm tra đầu tiên, mô tả impact, và các hành động giảm thiểu cụ thể (cắt queries, rollback changes, rút gọn prompts, v.v.).
- [EVIDENCE_LINK]&#58; https://github.com/datyespro/lab13_C401-D2/pull/2 (app/metrics.py, config/alert_rules.yaml, docs/alerts.md)

### Nguyễn Anh Đức (Member E — Chaos & SRE Engineer)
- [TASKS_COMPLETED]&#58;   - Sửa `scripts/load_test.py`: thêm argument `--concurrency` với `ThreadPoolExecutor` để thực thi request song song, jitter ngẫu nhiên (0.1–1.5s) để mô phỏng độ trễ mạng thực tế, console output có màu (xanh cho 200, đỏ cho errors) hiển thị HTTP status, correlation_id, feature, latency, và jitter mỗi request.
  - Triển khai `scripts/inject_incident.py`: HTTP client để toggle incidents (`rag_slow`, `tool_fail`, `cost_spike`) qua `POST /incidents/{name}/enable|disable`. Script gọi incident toggle endpoints của app — `mock_rag.py` và `mock_llm.py` phản ứng với state change.
  - Viết `config/slo.yaml`: định nghĩa SLI `latency_p95_ms` (objective <2000ms, target 95%), `error_rate_pct` (objective <2%, target 99%), `daily_cost_usd` (objective <$1.00, target 100%), và `quality_score_avg` (objective ≥0.80, target 95%) với evaluation window 28 ngày.
  - Thiết kế và xây dựng toàn bộ dashboard `app/static/` (HTML, CSS, JS + Chart.js) với 6 panels: Latency Distribution (biểu đồ đường P50/P95/P99), Request Traffic (số request tích lũy), Error Rate % (kèm danh sách chi tiết), Cost Over Time (USD với budget line), Token Usage (bar chart in/out), và Quality Score (biểu đồ gauge). Auto-refresh mỗi 3 giây, poll `/metrics`, hiển thị SLO progress bars.
- [EVIDENCE_LINK]&#58; https://github.com/datyespro/lab13_C401-D2/pull/3 (scripts/load_test.py, scripts/inject_incident.py, config/slo.yaml, app/static/)

### Hoàng Ngọc Anh (Member F — AI Agent & Team Lead)
- [TASKS_COMPLETED]&#58;   - Triển khai `app/agent.py`: class `LabAgent` với method `run()` được decorate bằng `@observe()` từ Langfuse. Method điều phối `retrieve()` (tra cứu RAG) và `FakeLLM.generate()` (gọi LLM), tính latency, cost, và quality score, ghi tất cả metrics qua `metrics.record_request()`. Langfuse trace metadata bao gồm hashed `user_id`, `session_id`, và tags `["lab", feature, model]`. Observation metadata bao gồm `doc_count`, `query_preview` (đã scrub PII), và `usage_details`.
  - `mock_rag.py` triển khai RAG retrieval từ corpus cố định được key bằng keywords (refund, monitoring, policy). Khi incident `rag_slow` active, `time.sleep(3.0)` được inject — khiến span `retrieve()` vượt P95 SLO khoảng 50%.
  - `mock_llm.py` mô phỏng LLM generation với độ trễ base 150ms. Khi `cost_spike` active, output tokens được nhân 4, khiến cost per request tăng từ ~$0.009 lên ~$0.036.
  - Dẫn dắt live demo: demo PII scrubbing (gửi email/phone trong chat message, xác nhận `[REDACTED_EMAIL]` trong logs), trigger incident `rag_slow`, show dashboard latency spike, sau đó fix qua `/incidents/rag_slow/disable`.
  - Tổng hợp báo cáo `docs/blueprint-template.md` này và điều phối các PR merges từ tất cả thành viên trong nhóm.
- [EVIDENCE_LINK]&#58; https://github.com/datyespro/lab13_C401-D2 (app/agent.py)

---

## 6. Bonus Items (Optional)
- [BONUS_COST_OPTIMIZATION]&#58; Chi phí được ước tính qua công thức `cost_usd = (tokens_in / 1_000_000) * $3 + (tokens_out / 1_000_000) * $15`. Alert `cost_budget_spike` kích hoạt khi `total_cost_usd > $1.0` trong 5 phút. Dashboard theo dõi chi phí tích lũy với budget line $1.00/ngày. Chi phí thực tế tại thời điểm báo cáo: **$0.18/ngày** — thấp hơn 82% so với budget. Bằng chứng: `app/metrics.py snapshot()` trả về `total_cost_usd` và `avg_cost_usd`; `app/static/app.js` vẽ biểu đồ trên Cost Over Time panel.
- [BONUS_AUDIT_LOGS]&#58; Tất cả log entries được ghi vào `data/logs.jsonl` (append-only JSONL) với timestamps ISO UTC (`ts` key), log level, service name, event name, `correlation_id`, và đầy đủ context vars (`user_id_hash`, `session_id`, `feature`, `model`, `env`). PII được scrub trước khi ghi bởi `scrub_event` — không có PII thô nào bao giờ đến file log. Bằng chứng: `validate_logs.py` báo 0 PII leaks trên 139 bản ghi.
- [BONUS_CUSTOM_METRIC]&#58; Quality score heuristic trong `app/agent.py._heuristic_quality()`: base 0.5 + 0.2 (nếu docs được retrieve) + 0.1 (nếu answer length > 40 chars) + 0.1 (nếu question keywords xuất hiện trong answer) − 0.2 (nếu `[REDACTED` xuất hiện trong answer). Clamped vào [0.0, 1.0]. Exposed qua `/metrics` endpoint và hiển thị trên dashboard panel dạng gauge. Alert `low_quality_score` (P3) kích hoạt khi `quality_avg < 0.7` trong 5 phút, nhắc nhở review prompt/policy.

---

## Appendix: Architecture Summary

```text
Client (load_test.py --concurrency 5)
    │
    │ HTTP POST /chat
    ▼
FastAPI + CorrelationIdMiddleware
    │ (tạo req-{8-char-hex} x-request-id, bind vào structlog contextvars)
    │
    ├─► structlog pipeline:
    │     merge_contextvars → add_log_level → TimeStamper(UTC, iso)
    │   → scrub_event (PII: email/phone/cc → [REDACTED_*])
    │   → StackInfoRenderer → format_exc_info
    │   → JsonlFileProcessor (append vào data/logs.jsonl)
    │   → JSONRenderer (stdout)
    │
    ├─► LabAgent.run() [@observe(Langfuse)]
    │       │
    │       ├─► retrieve() [mock_rag.py]
    │       │       incidents.py: rag_slow → time.sleep(3.0) → span 3000ms
    │       │
    │       └─► FakeLLM.generate() [mock_llm.py]
    │               incidents.py: cost_spike → output_tokens × 4 → $0.036/req
    │
    ├─► metrics.record_request(latency_ms, cost_usd, tokens_in, tokens_out, quality_score)
    │
    └─► GET /metrics → app/static/index.html (dashboard 6 panels)
            poll /metrics mỗi 3s, Chart.js, SLO progress bars