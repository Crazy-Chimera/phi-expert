"""Minimal in-process request metrics."""
from collections import Counter
from threading import Lock
from time import perf_counter
from typing import Any

_lock = Lock()
_counts: Counter[str] = Counter()
_total_seconds = 0.0

def record_request(endpoint: str, elapsed: float) -> None:
    global _total_seconds
    with _lock:
        _counts[endpoint] += 1
        _total_seconds += max(0.0, elapsed)

def snapshot() -> dict[str, Any]:
    with _lock:
        total = sum(_counts.values())
        return {"requests_total": total, "requests_by_endpoint": dict(_counts),
                "processing_seconds_total": round(_total_seconds, 6)}
