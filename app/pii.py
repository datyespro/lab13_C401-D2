from __future__ import annotations

import hashlib
import re

PII_RULES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\b4\d{3}(?:[ -]?\d{4}){3}\b"), "[REDACTED_CC]"),
    (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"), "[REDACTED_EMAIL]"),
    (re.compile(r"(?<!\d)(?:\+84|0)(?:[ .-]?\d){9,10}(?!\d)"), "[REDACTED_PHONE]"),
]


def scrub_text(text: str) -> str:
    safe = text
    for pattern, replacement in PII_RULES:
        safe = pattern.sub(replacement, safe)
    return safe


def summarize_text(text: str, max_len: int = 80) -> str:
    safe = scrub_text(text).strip().replace("\n", " ")
    return safe[:max_len] + ("..." if len(safe) > max_len else "")


def hash_user_id(user_id: str) -> str:
    return hashlib.sha256(user_id.encode("utf-8")).hexdigest()[:12]
