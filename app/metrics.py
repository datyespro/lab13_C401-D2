from __future__ import annotations

from collections import Counter, deque
from statistics import mean

# Sliding window: chỉ giữ 100 request gần nhất để P95 phản ánh trạng thái HIỆN TẠI
_WINDOW = 100

REQUEST_LATENCIES: deque[int]   = deque(maxlen=_WINDOW)
REQUEST_COSTS: deque[float]     = deque(maxlen=_WINDOW)
REQUEST_TOKENS_IN: deque[int]   = deque(maxlen=_WINDOW)
REQUEST_TOKENS_OUT: deque[int]  = deque(maxlen=_WINDOW)
ERRORS: Counter[str] = Counter()
TRAFFIC: int = 0
QUALITY_SCORES: deque[float]    = deque(maxlen=_WINDOW)


def record_request(latency_ms: int, cost_usd: float, tokens_in: int, tokens_out: int, quality_score: float) -> None:
    global TRAFFIC
    TRAFFIC += 1
    REQUEST_LATENCIES.append(latency_ms)
    REQUEST_COSTS.append(cost_usd)
    REQUEST_TOKENS_IN.append(tokens_in)
    REQUEST_TOKENS_OUT.append(tokens_out)
    QUALITY_SCORES.append(quality_score)



def record_error(error_type: str) -> None:
    ERRORS[error_type] += 1


def reset() -> None:
    """Hard-reset toàn bộ metrics — dùng giữa các phase demo."""
    global TRAFFIC
    TRAFFIC = 0
    REQUEST_LATENCIES.clear()
    REQUEST_COSTS.clear()
    REQUEST_TOKENS_IN.clear()
    REQUEST_TOKENS_OUT.clear()
    QUALITY_SCORES.clear()
    ERRORS.clear()



def percentile(values: list[int], p: int) -> float:
    if not values:
        return 0.0
    items = sorted(values)
    idx = max(0, min(len(items) - 1, round((p / 100) * len(items) + 0.5) - 1))
    return float(items[idx])



def snapshot() -> dict:
    total_errors = sum(ERRORS.values())
    success_count = TRAFFIC - total_errors
    error_rate_pct = (total_errors / TRAFFIC * 100) if TRAFFIC > 0 else 0.0
    
    return {
        "traffic": TRAFFIC,
        "success_count": success_count,
        "error_count": total_errors,
        "error_rate_pct": round(error_rate_pct, 2),
        "latency_p50": percentile(REQUEST_LATENCIES, 50),
        "latency_p95": percentile(REQUEST_LATENCIES, 95),
        "latency_p99": percentile(REQUEST_LATENCIES, 99),
        "avg_cost_usd": round(mean(REQUEST_COSTS), 4) if REQUEST_COSTS else 0.0,
        "total_cost_usd": round(sum(REQUEST_COSTS), 4),
        "tokens_in_total": sum(REQUEST_TOKENS_IN),
        "tokens_out_total": sum(REQUEST_TOKENS_OUT),
        "error_breakdown": dict(ERRORS),
        "quality_avg": round(mean(QUALITY_SCORES), 4) if QUALITY_SCORES else 0.0,
    }
