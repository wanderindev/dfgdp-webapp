import asyncio
import time
from abc import ABC, abstractmethod
from typing import Any, List


class RateLimiter:
    """Rate limiter for API calls"""

    def __init__(self, calls_per_minute: int = 50) -> None:
        self.calls_per_minute: int = calls_per_minute
        self.calls: List[float] = []

    def _cleanup_old_calls(self) -> None:
        """Remove calls older than 1 minute"""
        now: float = time.time()
        self.calls = [t for t in self.calls if now - t < 60]

    async def wait_if_needed(self) -> None:
        """Wait if we're over the rate limit"""
        self._cleanup_old_calls()
        if len(self.calls) >= self.calls_per_minute:
            # Wait until oldest call is more than a minute old
            wait_time: float = 60 - (time.time() - self.calls[0])
            if wait_time > 0:
                await asyncio.sleep(wait_time)
            self._cleanup_old_calls()
        self.calls.append(time.time())


class BaseAIClient(ABC):
    """Base class for AI API clients"""

    model: str
    temperature: float
    max_tokens: int
    rate_limiter: RateLimiter
    client: Any

    def __init__(
        self, model: str, temperature: float, max_tokens: int, rate_limit: int = 50
    ) -> None:
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.rate_limiter = RateLimiter(rate_limit)
        self._init_client()

    @abstractmethod
    def _init_client(self) -> None:
        """Initialize the specific API client."""
        pass

    async def generate(self, prompt: str, **kwargs: Any) -> str:
        """
        Generate content and track usage.

        Args:
            prompt: The text prompt for generation
            **kwargs: Additional arguments for the API call

        Returns:
            str: The generated text content
        """
        # Wait for rate limit if needed
        await self.rate_limiter.wait_if_needed()

        response = await self._generate_content(prompt, **kwargs)
        await self._track_usage(response)
        return self._extract_content(response)

    @abstractmethod
    async def _generate_content(self, prompt: str, **kwargs: Any) -> Any:
        """
        Implementation-specific content generation.

        Args:
            prompt: The text prompt for generation
            **kwargs: Additional arguments for the API call

        Returns:
            Any: Raw API response (specific type defined by child classes)
        """
        pass

    @abstractmethod
    def _extract_content(self, response: Any) -> str:
        """
        Extract text content from API response.

        Args:
            response: The raw API response

        Returns:
            str: The extracted text content
        """
        pass

    @abstractmethod
    async def _track_usage(self, response: Any) -> None:
        """
        Track token usage and cost for this response.

        Args:
            response: The raw API response
        """
        pass
