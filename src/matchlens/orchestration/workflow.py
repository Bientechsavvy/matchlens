"""Supervisor: retry + fallback + trace per stage (docs/01 §7, docs/03 'Phase 2')."""
from __future__ import annotations

import logging
import time
from collections import deque
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")
log = logging.getLogger("matchlens.workflow")


class Supervisor:
    def __init__(self, retries: int = 2):
        self.retries = retries
        self.trace: deque[dict] = deque(maxlen=100)

    def run(self, stage: str, fn: Callable[[], T], fallback: Callable[[], T] | None = None) -> T:
        t0, last, out, status = time.perf_counter(), None, None, "ok"
        attempts = 0
        for attempts in range(1, self.retries + 2):
            try:
                out = fn()
                status = "ok" if attempts == 1 else "retried"
                last = None
                break
            except Exception as exc:
                last = exc
                log.warning("stage %s attempt %d failed: %s", stage, attempts, exc)
        if last is not None:
            if fallback is None:
                self.trace.append({"stage": stage, "status": "failed", "attempts": attempts, "ms": 0})
                raise last
            out, status = fallback(), "fallback"
        self.trace.append({"stage": stage, "status": status, "attempts": attempts,
                           "ms": round((time.perf_counter() - t0) * 1000, 1)})
        return out
