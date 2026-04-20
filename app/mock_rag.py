from __future__ import annotations

import time

from .incidents import STATE

CORPUS = {
    "refund": ["Refunds are available within 7 days with proof of purchase."],
    "monitoring": ["Metrics detect incidents, traces localize them, logs explain root cause."],
    "policy": ["Do not expose PII in logs. Use sanitized summaries only."],
}


def retrieve(message: str) -> list[str]:
    if STATE["tool_fail"]:
        raise RuntimeError("Vector store timeout — tool_fail incident active")
    if STATE["rag_slow"]:
        time.sleep(3.0)   # 3s > SLO 2000ms → guaranteed breach visible on dashboard
    lowered = message.lower()
    for key, docs in CORPUS.items():
        if key in lowered:
            return docs
    return ["No domain document matched. Use general fallback answer."]
