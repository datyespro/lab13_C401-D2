"""
demo_chaos.py — Kịch bản Demo tự động cho Thành viên 5 (SRE Engineer)

Cách chạy:
  cd D:\AIThucChien\BaiTapLab\Demo\lab13_C401-D2
  python scripts/demo_chaos.py

4 Phase rõ ràng — mỗi phase RESET metrics → Dashboard luôn phản ánh đúng hiện tại:
  Phase 1 (30s) : Normal load  → Dashboard xanh lá, P95 ~150ms
  Phase 2 (40s) : rag_slow ON  → P95 > 3000ms, SLO BREACH đỏ rực
  Phase 3 (20s) : tool_fail ON → HTTP 500 errors, Error Rate tăng
  Phase 4 (20s) : Tất cả OFF   → System recovers, Dashboard trở về xanh
"""
from __future__ import annotations

import concurrent.futures
import json
import sys
import time
from pathlib import Path

import httpx

BASE_URL = "http://127.0.0.1:8000"
QUERIES  = Path("data/sample_queries.jsonl")

# ── ANSI Colors ──────────────────────────────────────────────────────
R = "\033[91m"; G = "\033[92m"; Y = "\033[93m"; C = "\033[96m"; B = "\033[1m"; X = "\033[0m"


def banner(msg: str, color: str = C) -> None:
    bar = "═" * 62
    print(f"\n{color}{B}{bar}{X}")
    print(f"{color}{B}  {msg}{X}")
    print(f"{color}{B}{bar}{X}\n")


def step(msg: str) -> None:
    print(f"  {C}▶{X} {msg}")


# ── API helpers ──────────────────────────────────────────────────────
def toggle(client: httpx.Client, scenario: str, enable: bool) -> None:
    action = "enable" if enable else "disable"
    icon   = f"{R}🔴" if enable else f"{G}🟢"
    try:
        r = client.post(f"{BASE_URL}/incidents/{scenario}/{action}", timeout=5)
        print(f"  {icon} [{scenario}] → {action.upper()}{X}   (HTTP {r.status_code})")
    except Exception as e:
        print(f"  ⚠ toggle error: {e}")


def metrics_reset(client: httpx.Client) -> None:
    """Gọi endpoint reset metrics — đảm bảo mỗi phase bắt đầu sạch."""
    try:
        client.post(f"{BASE_URL}/metrics/reset", timeout=5)
        print(f"  {Y}⟳ Metrics reset to zero{X}")
    except Exception as e:
        print(f"  ⚠ reset failed: {e}")


def snapshot(client: httpx.Client) -> dict:
    try:
        return client.get(f"{BASE_URL}/metrics", timeout=5).json()
    except Exception:
        return {}


def print_snap(d: dict) -> None:
    p95   = int(d.get("latency_p95", 0))
    tot   = d.get("traffic", 0)
    errs  = sum(d.get("error_breakdown", {}).values())
    rate  = f"{errs/tot*100:.1f}%" if tot else "0.0%"
    cost  = d.get("total_cost_usd", 0)
    p95c  = R if p95 > 2000 else G
    errc  = R if errs > 0   else G
    print(f"\n  {'─'*56}")
    print(f"  📊  traffic={B}{tot}{X}  P95={p95c}{B}{p95}ms{X}  errors={errc}{B}{rate}{X}  cost=${B}{cost:.4f}{X}")
    print(f"  {'─'*56}\n")


# ── Send one request (thread-safe, no mutable captures) ──────────────
def _send(base_url: str, payload: dict, timeout: float) -> str:
    try:
        t0 = time.perf_counter()
        r  = httpx.post(f"{base_url}/chat", json=payload, timeout=timeout)
        ms = int((time.perf_counter() - t0) * 1000)
        if r.status_code == 200:
            return f"{G}[200 OK ]{X} {payload['feature']:7s} | {ms:>5}ms"
        return f"{R}[{r.status_code} ERR]{X} {payload['feature']:7s} | {ms:>5}ms"
    except httpx.TimeoutException:
        return f"{Y}[TIMEOUT]{X} {payload['feature']:7s} | >{int(timeout*1000)}ms"
    except Exception as e:
        return f"{R}[ERROR  ]{X} {str(e)[:50]}"


def burst(lines: list[str], concurrency: int, label: str,
          timeout: float = 10.0) -> None:
    """
    Fire `concurrency` requests concurrently and WAIT for ALL to finish.
    Timeout per request is set conservatively so rag_slow (3s) never times out.
    """
    payloads = [json.loads(l) for l in lines[:concurrency]]
    step(f"Burst [{label}] — {len(payloads)} concurrent requests (timeout={timeout}s/req)")

    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as pool:
        futs = {pool.submit(_send, BASE_URL, p, timeout): p for p in payloads}
        # concurrent.futures.wait() ensures ALL threads finish before returning
        done, _ = concurrent.futures.wait(futs, timeout=timeout * 2)
        for f in done:
            print(f"    {f.result()}")


# ════════════════════════════════════════════════════════════════════
def main() -> None:
    if not QUERIES.exists():
        sys.exit("❌  Run from project root:  D:\\...\\lab13_C401-D2")

    lines = [l for l in QUERIES.read_text(encoding="utf-8").splitlines() if l.strip()]

    with httpx.Client(timeout=12) as client:

        # Đảm bảo tắt mọi incident cũ còn sót
        toggle(client, "rag_slow",  enable=False)
        toggle(client, "tool_fail", enable=False)
        toggle(client, "cost_spike",enable=False)
        metrics_reset(client)
        time.sleep(1)

        # ── Phase 1: Normal ─────────────────────────────────────────
        banner("PHASE 1 — Normal Load (30s)   ✅ Dashboard should be GREEN", G)
        for i in range(3):
            burst(lines, concurrency=10, label=f"normal-{i+1}")
            print_snap(snapshot(client))
            time.sleep(5)

        # ── Phase 2: rag_slow ───────────────────────────────────────
        banner("PHASE 2 — Inject rag_slow (40s)   🔴 P95 Latency BREACH > 2000ms", R)
        metrics_reset(client)           # ← reset trước khi bắt đầu phase mới
        toggle(client, "rag_slow", enable=True)
        time.sleep(0.5)

        # Chỉ bắn 5 requests — 3s mỗi cái rất đủ để P95 vọt lên
        burst(lines, concurrency=5, label="slow-1", timeout=10.0)
        print_snap(snapshot(client))
        time.sleep(3)
        burst(lines, concurrency=5, label="slow-2", timeout=10.0)
        print_snap(snapshot(client))

        toggle(client, "rag_slow", enable=False)
        step(f"{Y}rag_slow disabled — latency trở về bình thường sau vài giây{X}")
        time.sleep(2)

        # ── Phase 3: tool_fail → HTTP 500 ──────────────────────────
        banner("PHASE 3 — Inject tool_fail (20s)   🔴 HTTP 500 & Error Rate spike", R)
        metrics_reset(client)
        toggle(client, "tool_fail", enable=True)
        time.sleep(0.5)

        burst(lines, concurrency=15, label="errors", timeout=5.0)
        print_snap(snapshot(client))
        time.sleep(5)

        toggle(client, "tool_fail", enable=False)

        # ── Phase 4: Recovery ───────────────────────────────────────
        banner("PHASE 4 — Recovery (20s)   🟢 All incidents OFF, system heals", G)
        metrics_reset(client)
        time.sleep(1)

        for i in range(2):
            burst(lines, concurrency=10, label=f"recover-{i+1}")
            print_snap(snapshot(client))
            time.sleep(5)

        # ── Final snapshot ──────────────────────────────────────────
        banner("DEMO COMPLETE ✅  Open Dashboard to see the full timeline", G)
        print_snap(snapshot(client))


if __name__ == "__main__":
    main()
