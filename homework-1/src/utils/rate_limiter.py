"""Basic in-memory, fixed-window rate limiter (per client IP).

This is intentionally simple for a single-process, in-memory demo API:
- Each IP gets its own counter and a 60-second window.
- When the window elapses, the counter resets.
- State lives only in process memory - it does not survive a restart and
  does not coordinate across multiple processes/instances. For production
  use behind multiple workers, a shared store (e.g. Redis) would be needed.
"""

import time
from threading import Lock
from typing import Dict, Tuple

RATE_LIMIT_MAX_REQUESTS = 100
RATE_LIMIT_WINDOW_SECONDS = 60.0


class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: float) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        # key -> (window_start_monotonic, request_count)
        self._buckets: Dict[str, Tuple[float, int]] = {}
        self._lock = Lock()

    def check(self, key: str) -> Tuple[bool, int, float]:
        """Record one request for `key`.

        Returns (allowed, remaining, retry_after_seconds). `allowed` is
        False once the count for the current window exceeds the limit.
        """
        now = time.monotonic()
        with self._lock:
            window_start, count = self._buckets.get(key, (now, 0))
            if now - window_start >= self.window_seconds:
                window_start, count = now, 0

            count += 1
            self._buckets[key] = (window_start, count)

            allowed = count <= self.max_requests
            remaining = max(self.max_requests - count, 0)
            retry_after = max(self.window_seconds - (now - window_start), 0.0)

        return allowed, remaining, retry_after

    def reset(self) -> None:
        """Clear all rate-limit state. Mainly useful for tests."""
        with self._lock:
            self._buckets.clear()


# Single shared limiter used by the whole application.
rate_limiter = RateLimiter(RATE_LIMIT_MAX_REQUESTS, RATE_LIMIT_WINDOW_SECONDS)
