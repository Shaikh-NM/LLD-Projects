from abc import ABC, abstractmethod
import time
import threading
from typing import Dict, Deque
from collections import deque


# ==========================================
# 1. STRATEGY INTERFACE (The Abstraction)
# ==========================================

class RateLimitingStrategy(ABC):
    """Abstract Strategy interface declaring rate-limiting decision rules."""
    
    @abstractmethod
    def allow_request(self) -> bool:
        """Returns True if the request is allowed, False if rate-limited."""
        pass


# ==========================================
# 2. CONCRETE STRATEGIES
# ==========================================

class TokenBucketStrategy(RateLimitingStrategy):
    """
    Token Bucket Algorithm:
    - Bucket fills up to `capacity` tokens at `refill_rate` tokens/sec.
    - Each request consumes 1 token.
    - Supports controlled burst traffic.
    """
    def __init__(self, capacity: int, refill_rate_per_sec: float):
        self._capacity: int = capacity
        self._refill_rate: float = refill_rate_per_sec
        self._tokens: float = float(capacity)
        self._last_refill_time: float = time.time()
        self._lock: threading.Lock = threading.Lock()

    def _refill(self) -> None:
        now = time.time()
        elapsed = now - self._last_refill_time
        tokens_to_add = elapsed * self._refill_rate
        self._tokens = min(float(self._capacity), self._tokens + tokens_to_add)
        self._last_refill_time = now

    def allow_request(self) -> bool:
        with self._lock:
            self._refill()
            if self._tokens >= 1.0:
                self._tokens -= 1.0
                return True
            return False


class SlidingWindowLogStrategy(RateLimitingStrategy):
    """
    Sliding Window Log Algorithm:
    - Maintains timestamps of requests in a double-ended queue.
    - Drops timestamps older than `window_size_seconds`.
    - Eliminates burst spikes across boundary edges.
    """
    def __init__(self, max_requests: int, window_size_seconds: float):
        self._max_requests: int = max_requests
        self._window_size: float = window_size_seconds
        self._log: Deque[float] = deque()
        self._lock: threading.Lock = threading.Lock()

    def allow_request(self) -> bool:
        with self._lock:
            now = time.time()
            cutoff = now - self._window_size

            # Evict timestamps older than the sliding window boundary
            while self._log and self._log[0] <= cutoff:
                self._log.popleft()

            if len(self._log) < self._max_requests:
                self._log.append(now)
                return True
            return False


# ==========================================
# 3. RATE LIMITER SERVICE (Facade Orchestrator)
# ==========================================

class RateLimiterService:
    """
    Orchestrates client-level rate limiters thread-safely.
    Supports dynamic factory methods to instantiate distinct algorithms.
    """
    def __init__(self):
        self._limiters: Dict[str, RateLimitingStrategy] = {}
        self._service_lock: threading.Lock = threading.Lock()

    def register_token_bucket(self, client_key: str, capacity: int, refill_rate_per_sec: float) -> None:
        with self._service_lock:
            self._limiters[client_key] = TokenBucketStrategy(capacity, refill_rate_per_sec)

    def register_sliding_window(self, client_key: str, max_requests: int, window_seconds: float) -> None:
        with self._service_lock:
            self._limiters[client_key] = SlidingWindowLogStrategy(max_requests, window_seconds)

    def is_allowed(self, client_key: str) -> bool:
        with self._service_lock:
            limiter = self._limiters.get(client_key)

        if not limiter:
            # Default fallback: If unconfigured, allow or reject based on policy
            return True

        return limiter.allow_request()


# ==========================================
# 4. RUNTIME DEMONSTRATION & TEST CASES
# ==========================================

if __name__ == "__main__":
    service = RateLimiterService()

    # Client A: Token Bucket (Capacity=3, Refill=1 token/sec)
    service.register_token_bucket(client_key="user_free_tier", capacity=3, refill_rate_per_sec=1.0)

    # Client B: Sliding Window Log (Max 2 requests per 1.0 second)
    service.register_sliding_window(client_key="user_premium_tier", max_requests=2, window_seconds=1.0)

    print("=================== TEST 1: TOKEN BUCKET BURST & REFILL ===================")
    # Burst 3 requests immediately -> All should pass
    assert service.is_allowed("user_free_tier") is True
    assert service.is_allowed("user_free_tier") is True
    assert service.is_allowed("user_free_tier") is True
    print("✅ 3/3 initial tokens consumed successfully.")

    # 4th immediate request -> Should be rejected (bucket empty)
    assert service.is_allowed("user_free_tier") is False
    print("✅ 4th request rejected (Rate limit exceeded).")

    # Wait 1.1 seconds for 1 token to refill
    time.sleep(1.1)
    assert service.is_allowed("user_free_tier") is True
    print("✅ Request passed after 1 token refilled.")

    print("\n================ TEST 2: SLIDING WINDOW LOG ACCURACY ================")
    # 2 requests allowed within 1 second
    assert service.is_allowed("user_premium_tier") is True
    assert service.is_allowed("user_premium_tier") is True
    assert service.is_allowed("user_premium_tier") is False
    print("✅ Sliding window strictly capped requests to 2 within the 1-second window.")

    # Wait for the 1-second window to slide past
    time.sleep(1.05)
    assert service.is_allowed("user_premium_tier") is True
    print("✅ New request permitted after window shifted forward.")

    print("\n================ TEST 3: CONCURRENT THREADED TRAFFIC ================")
    # Verifying thread safety with 10 concurrent threads hitting 5 capacity
    service.register_token_bucket("concurrent_client", capacity=5, refill_rate_per_sec=0.0)
    results = []

    def worker():
        allowed = service.is_allowed("concurrent_client")
        results.append(allowed)

    threads = [threading.Thread(target=worker) for _ in range(10)]
    for t in threads: t.start()
    for t in threads: t.join()

    passed_count = sum(1 for r in results if r)
    blocked_count = sum(1 for r in results if not r)
    assert passed_count == 5
    assert blocked_count == 5
    print(f"✅ Concurrency verified: Exactly {passed_count} passed and {blocked_count} blocked.")

    print("\n🎉 All rate limiter assertions passed successfully!")