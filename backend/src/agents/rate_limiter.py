import asyncio
import time
from typing import List


class AsyncRateLimiter:
    """
    An asynchronous token-bucket rate limiter.
    Allows up to `calls_per_minute` calls per minute.
    """

    def __init__(self, calls_per_minute: int = 50) -> None:
        self.calls_per_minute = calls_per_minute
        self.calls: List[float] = []

    def _cleanup_old_calls(self) -> None:
        """Remove calls older than 60 seconds."""
        now: float = time.time()
        self.calls = [t for t in self.calls if now - t < 60]

    async def wait_if_needed(self) -> None:
        """
        If we have already reached the maximum number of calls within the last minute,
        this will sleep until we can proceed.
        """
        self._cleanup_old_calls()
        # If at or above the rate limit, wait
        if len(self.calls) >= self.calls_per_minute:
            wait_time: float = 60 - (time.time() - self.calls[0])
            if wait_time > 0:
                await asyncio.sleep(wait_time)
            self._cleanup_old_calls()

        self.calls.append(time.time())
