from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class ChatRequest(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=64, examples=["u_team_01"])
    session_id: str = Field(..., min_length=1, max_length=64, examples=["s_demo_01"])
    feature: Literal["qa", "summary"] = Field(default="qa", examples=["qa", "summary"])
    message: str = Field(..., min_length=1, max_length=2000)

    @field_validator("user_id", "session_id", "message", mode="before")
    @classmethod
    def strip_and_reject_blank(cls, value: Any) -> Any:
        if isinstance(value, str):
            value = value.strip()
        if value == "":
            raise ValueError("must not be blank")
        return value


class ChatResponse(BaseModel):
    answer: str
    correlation_id: str
    latency_ms: int
    tokens_in: int
    tokens_out: int
    cost_usd: float
    quality_score: float


class LogRecord(BaseModel):
    ts: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    level: Literal["info", "warning", "error", "critical"]
    service: str
    event: str
    correlation_id: str
    env: str
    user_id_hash: str | None = None
    session_id: str | None = None
    feature: str | None = None
    model: str | None = None
    latency_ms: int | None = None
    tokens_in: int | None = None
    tokens_out: int | None = None
    cost_usd: float | None = None
    error_type: str | None = None
    tool_name: str | None = None
    payload: dict[str, Any] | None = None
