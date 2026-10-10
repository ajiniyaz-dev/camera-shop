"""In-process failed-login limiter.

Counters live in this process only. They are not shared across Uvicorn workers
or across more than one API container. Restarting the process clears them.
"""

from __future__ import annotations

import threading
import time
from collections import deque
from collections.abc import Callable


class LoginRateLimiter:
    def __init__(
        self,
        max_attempts: int,
        window_seconds: int,
        max_keys: int = 10_000,
        clock: Callable[[], float] | None = None,
    ) -> None:
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self.max_keys = max_keys
        self.clock = clock or time.monotonic
        self._failures: dict[str, deque[float]] = {}
        self._lock = threading.Lock()

    def is_limited(self, key: str) -> bool:
        now = self.clock()
        with self._lock:
            self._prune(now)
            stamps = self._failures.get(key)
            return bool(stamps and len(stamps) >= self.max_attempts)

    def record_failure(self, key: str) -> None:
        now = self.clock()
        with self._lock:
            self._prune(now)
            self._failures.setdefault(key, deque()).append(now)
            self._prune(now)

    def _prune(self, now: float) -> None:
        empty: list[str] = []
        for key, stamps in self._failures.items():
            while stamps and now - stamps[0] >= self.window_seconds:
                stamps.popleft()
            if not stamps:
                empty.append(key)
        for key in empty:
            del self._failures[key]
        while len(self._failures) > self.max_keys:
            oldest = min(self._failures, key=lambda item: self._failures[item][0])
            del self._failures[oldest]
