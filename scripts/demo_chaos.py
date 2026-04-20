"""
demo_chaos.py — Kịch bản Demo tự động cho Thành viên 5 (SRE Engineer)

Cách chạy:  cd D:\AIThucChien\BaiTapLab\Demo\lab13_C401-D2
            python scripts/demo_chaos.py

Kịch bản:
  Phase 1 (30s): Normal load — mọi thứ ổn định, Dashboard xanh lá
  Phase 2 (30s): Inject rag_slow — Latency vượt SLO 2000ms, Dashboard cảnh báo đỏ
  Phase 3 (20s): Inject tool_fail — HTTP 500 errors xuất hiện, Error Rate tăng
  Phase 4 (20s): Tất cả disable — hệ thống phục hồi, Dashboard trở về xanh
"""
from __future__ import annotations

import concurrent.futures
import json
import sys
import time
from pathlib import Path

import httpx

BASE_URL  = "http://127.0.0.1:8000"
QUERIES   = Path("data/sample_queries.jsonl")


# ── Màu ANSI ──────────────────────────────────────────────────────────
RED    = "\033[91m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"


def banner(msg: str, color: str = CYAN) -> None:
    bar = "─" * 60
    print(f"\n{color}{BOLD}{bar}{RESET}")
    print(f"{color}{BOLD}  {msg}{RESET}")
    print(f"{color}{BOLD}{bar}{RESET}\n")


def toggle_incident(client: httpx.Client, scenario: str, enable: bool) -> None:
    action = "enable" if enable else "disable"
    try:
        r = client.post(f"{BASE_URL}/incidents/{scenario}/{action}", timeout=5)
        icon = "🔴" if enable else "🟢"
        print(f"  {icon} Incident [{scenario}] → {action.upper()} | status: {r.status_code}")
    except Exception as e:
        print(f"  ⚠ Could not toggle incident: {e}")


def send_one(client: httpx.Client, payload: dict) -> str:
    try:
        t0 = time.perf_counter()
        r  = client.post(f"{BASE_URL}/chat", json=payload, timeout=15)
        ms = int((time.perf_counter() - t0) * 1000)
        if r.status_code == 200:
            return f"{GREEN}[200 OK ]{RESET} {payload['feature']:7s} | {ms:>5}ms"
        return f"{RED}[{r.status_code} ERR]{RESET} {payload['feature']:7s} | {ms:>5}ms"
    except Exception as e:
        return f"{RED}[TIMEOUT]{RESET} {payload['feature']:7s} | {e}"


def load_burst(client: httpx.Client, lines: list[str], concurrency: int, label: str) -> None:
    """Fire one burst of concurrent requests."""
    print(f"  ↗ Burst [{label}] — {concurrency} concurrent requests")
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as pool:
        futs = [pool.submit(send_one, client, json.loads(l)) for l in lines[:concurrency]]
        for f in concurrent.futures.as_completed(futs):
            print(f"    {f.result()}")


def fetch_snapshot(client: httpx.Client) -> dict:
    try:
        return client.get(f"{BASE_URL}/metrics", timeout=5).json()
    except Exception:
        return {}


def print_snapshot(d: dict) -> None:
    p95  = int(d.get("latency_p95", 0))
    errs = sum(d.get("error_breakdown", {}).values())
    tot  = d.get("traffic", 0)
    cost = d.get("total_cost_usd", 0)
    rate = f"{errs/tot*100:.1f}%" if tot else "0.0%"
    p95c = RED if p95 > 2000 else GREEN
    ec   = RED if errs > 0 else GREEN

    print(f"\n  📊 Snapshot  traffic={tot}  "
          f"P95={p95c}{p95}ms{RESET}  "
          f"errors={ec}{rate}{RESET}  "
          f"cost=${cost:.4f}\n")


# ═══════════════════════════════════════════════════════════════════
def main() -> None:
    if not QUERIES.exists():
        sys.exit("ERROR: Run from the project root: D:\\...\\lab13_C401-D2")

    lines = [l for l in QUERIES.read_text(encoding="utf-8").splitlines() if l.strip()]

    with httpx.Client(timeout=15) as client:

        # ── Phase 1: Normal ────────────────────────────────────────
        banner("PHASE 1 — Normal load (30s)  🟢 Watch Dashboard go GREEN", GREEN)
        for i in range(3):
            load_burst(client, lines, concurrency=10, label=f"normal-{i+1}")
            snap = fetch_snapshot(client)
            print_snapshot(snap)
            time.sleep(8)

        # ── Phase 2: rag_slow ──────────────────────────────────────
        banner("PHASE 2 — Inject rag_slow (30s)  🔴 Latency will BREACH 2000ms SLO", RED)
        toggle_incident(client, "rag_slow", enable=True)
        time.sleep(1)
        for i in range(2):
            load_burst(client, lines, concurrency=8, label=f"slow-{i+1}")
            snap = fetch_snapshot(client)
            print_snapshot(snap)
            time.sleep(12)
        toggle_incident(client, "rag_slow", enable=False)
        print(f"  {YELLOW}rag_slow disabled — recovery begins...{RESET}")

        # ── Phase 3: tool_fail → HTTP 500 ─────────────────────────
        banner("PHASE 3 — Inject tool_fail (20s)  🔴 HTTP 500 errors & Error Rate spike", RED)
        toggle_incident(client, "tool_fail", enable=True)
        time.sleep(1)
        load_burst(client, lines, concurrency=15, label="tool-fail")
        snap = fetch_snapshot(client)
        print_snapshot(snap)
        time.sleep(8)
        toggle_incident(client, "tool_fail", enable=False)

        # ── Phase 4: Recovery ──────────────────────────────────────
        banner("PHASE 4 — Recovery (20s)  🟢 All incidents disabled", GREEN)
        for i in range(2):
            load_burst(client, lines, concurrency=10, label=f"recover-{i+1}")
            snap = fetch_snapshot(client)
            print_snapshot(snap)
            time.sleep(8)

        banner("DEMO COMPLETE ✅  Check your Dashboard for the full story!", GREEN)
        print_snapshot(fetch_snapshot(client))


if __name__ == "__main__":
    main()
