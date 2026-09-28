"""Rate Limiter & DDoS Mitigation (Token Bucket Algorithm)."""

from collections import defaultdict
import threading
import time
from typing import Dict, Tuple


class TokenBucketRateLimiter:
    """Thread-safe Token Bucket rate limiter per client IP / identifier."""

    def __init__(self, capacity: int = 120, refill_rate_per_sec: float = 2.0) -> None:
        self.capacity = capacity
        self.refill_rate = refill_rate_per_sec
        # client_id -> (tokens, last_refill_timestamp)
        self._buckets: Dict[str, Tuple[float, float]] = defaultdict(lambda: (float(capacity), time.time()))
        self._lock = threading.Lock()

    def allow_request(self, client_id: str, cost: float = 1.0) -> Tuple[bool, float]:
        """Returns (is_allowed, remaining_tokens)."""
        with self._lock:
            now = time.time()
            tokens, last_refill = self._buckets[client_id]

            # Refill tokens based on elapsed time
            elapsed = now - last_refill
            tokens = min(self.capacity, tokens + elapsed * self.refill_rate)

            if tokens >= cost:
                tokens -= cost
                self._buckets[client_id] = (tokens, now)
                return True, tokens
            else:
                self._buckets[client_id] = (tokens, now)
                return False, tokens


rate_limiter = TokenBucketRateLimiter(capacity=100, refill_rate_per_sec=5.0)
