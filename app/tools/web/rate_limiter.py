"""
Async Rate Limiter with Sliding Window

Prevents excessive API calls and ensures compliance with rate limits.
"""

import asyncio
from datetime import datetime, timedelta
from typing import List

from app.logger import logger


class AsyncRateLimiter:
    """Async rate limiter with sliding window algorithm"""

    def __init__(self, max_calls: int, period: int):
        """
        Initialize rate limiter

        Args:
            max_calls: Maximum number of calls allowed
            period: Time period in seconds
        """
        self.max_calls = max_calls
        self.period = period
        self.calls: List[datetime] = []
        self._lock = asyncio.Lock()

    async def acquire(self):
        """
        Acquire permission to make a call

        Blocks if rate limit is reached until a slot becomes available.
        """
        async with self._lock:
            now = datetime.now()

            # Remove calls outside the sliding window
            cutoff = now - timedelta(seconds=self.period)
            self.calls = [call_time for call_time in self.calls if call_time > cutoff]

            # Check if at limit
            if len(self.calls) >= self.max_calls:
                # Calculate wait time until oldest call expires
                oldest_call = self.calls[0]
                wait_until = oldest_call + timedelta(seconds=self.period)
                wait_time = (wait_until - now).total_seconds()

                if wait_time > 0:
                    logger.warning(
                        f"⏱️ Rate limit reached ({self.max_calls}/{self.period}s), "
                        f"waiting {wait_time:.1f}s..."
                    )
                    await asyncio.sleep(wait_time)

                    # Remove the oldest call that just expired
                    self.calls.pop(0)

            # Record this call
            self.calls.append(now)

    def get_remaining(self) -> int:
        """
        Get number of remaining calls in current window

        Returns:
            Number of calls that can be made without waiting
        """
        now = datetime.now()
        cutoff = now - timedelta(seconds=self.period)
        active_calls = [c for c in self.calls if c > cutoff]

        return max(0, self.max_calls - len(active_calls))

    def reset(self):
        """Reset the rate limiter"""
        self.calls.clear()
        logger.info("🔄 Rate limiter reset")
