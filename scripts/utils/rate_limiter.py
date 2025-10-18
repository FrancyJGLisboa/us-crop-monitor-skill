#!/usr/bin/env python3
"""
Rate Limiter for NASS API

Implements token bucket algorithm to respect API rate limits.

Author: Agent Creator
Version: 1.0.0
"""

import time
import threading
from typing import Optional


class RateLimiter:
    """
    Token bucket rate limiter.

    Features:
    - Thread-safe
    - Configurable rate
    - Non-blocking check and blocking acquire
    """

    def __init__(self, max_requests: int = 15, time_window: int = 60):
        """
        Initialize rate limiter.

        Args:
            max_requests: Maximum number of requests allowed
            time_window: Time window in seconds
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.tokens = max_requests
        self.last_update = time.time()
        self.lock = threading.Lock()

        # Calculate refill rate
        self.refill_rate = max_requests / time_window

    def _refill(self):
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_update

        # Add tokens based on time elapsed
        new_tokens = elapsed * self.refill_rate
        self.tokens = min(self.max_requests, self.tokens + new_tokens)
        self.last_update = now

    def can_proceed(self) -> bool:
        """
        Check if a request can proceed without blocking.

        Returns:
            True if request can proceed immediately
        """
        with self.lock:
            self._refill()
            return self.tokens >= 1.0

    def acquire(self, timeout: Optional[float] = None) -> bool:
        """
        Acquire permission to make a request (blocking).

        Blocks until a token is available or timeout occurs.

        Args:
            timeout: Maximum time to wait in seconds (None = infinite)

        Returns:
            True if acquired, False if timeout
        """
        start_time = time.time()

        while True:
            with self.lock:
                self._refill()

                if self.tokens >= 1.0:
                    self.tokens -= 1.0
                    return True

            # Check timeout
            if timeout is not None:
                elapsed = time.time() - start_time
                if elapsed >= timeout:
                    return False

            # Sleep before retry (small interval to avoid busy-wait)
            time.sleep(0.1)

    def reset(self):
        """Reset rate limiter to initial state."""
        with self.lock:
            self.tokens = self.max_requests
            self.last_update = time.time()

    def get_wait_time(self) -> float:
        """
        Get time until next token available.

        Returns:
            Wait time in seconds (0 if token available)
        """
        with self.lock:
            self._refill()

            if self.tokens >= 1.0:
                return 0.0

            # Calculate time needed to get 1 token
            tokens_needed = 1.0 - self.tokens
            wait_time = tokens_needed / self.refill_rate
            return wait_time

    def __repr__(self) -> str:
        """String representation."""
        return (f"RateLimiter(max_requests={self.max_requests}, "
                f"time_window={self.time_window}s, "
                f"tokens={self.tokens:.2f})")


if __name__ == "__main__":
    # Test rate limiter
    import random

    print("Testing RateLimiter...")

    # Create limiter: 5 requests per 10 seconds
    limiter = RateLimiter(max_requests=5, time_window=10)

    print(f"Initial state: {limiter}")

    # Simulate requests
    for i in range(8):
        wait = limiter.get_wait_time()
        print(f"\nRequest {i+1}:")
        print(f"  Wait time: {wait:.2f}s")

        success = limiter.acquire(timeout=2.0)
        if success:
            print(f"  Acquired! Tokens left: {limiter.tokens:.2f}")
            # Simulate work
            time.sleep(random.uniform(0.1, 0.5))
        else:
            print(f"  TIMEOUT! Could not acquire token")

    print(f"\nFinal state: {limiter}")

    # Test reset
    print("\nResetting limiter...")
    limiter.reset()
    print(f"After reset: {limiter}")
