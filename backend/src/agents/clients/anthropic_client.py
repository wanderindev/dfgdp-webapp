from typing import Any, Dict, List, Optional

from anthropic import AsyncAnthropic
from flask import current_app
from sqlalchemy.exc import IntegrityError
from tenacity import retry, stop_after_attempt, wait_exponential

from agents.clients.base_ai_client import BaseAIClient
from agents.rate_limiter import AsyncRateLimiter
from extensions import db


def async_retry(*dargs, **dkwargs):
    """
    Helper to apply Tenacity's async functionality.
    Usage:
      @async_retry(wait=wait_exponential(...), stop=stop_after_attempt(...))
      async def myfunc(...):
          ...
    """

    def decorator(func):
        # tenacity.retry is universal. But for async coroutines, Tenacity
        # automatically detects it if we don't disable 'reraise' or so.
        return retry(*dargs, **dkwargs)(func)

    return decorator


class AnthropicClient(BaseAIClient):
    """
    Client for Anthropic API (async version).
    """

    def __init__(
        self, model: str, temperature: float, max_tokens: int, rate_limit: int = 100
    ) -> None:
        """
        Args:
            model: Anthropic model name
            temperature: Sampling temperature
            max_tokens: Maximum tokens in the response
            rate_limit: Max calls per minute
        """
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.rate_limiter = AsyncRateLimiter(rate_limit)

        self.client = AsyncAnthropic(api_key=current_app.config["ANTHROPIC_API_KEY"])

    @async_retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=2, min=4, max=20),
        reraise=True,
    )
    async def _call_api(
        self,
        prompt: str,
        message_history: Optional[List[Dict[str, str]]] = None,
        **kwargs: Any,
    ) -> Any:
        """
        Protected method to call Anthropic's API asynchronously with retry logic.
        Raises:
            RetryError: after max attempts
        """
        await self.rate_limiter.wait_if_needed()

        try:
            messages = message_history or []
            messages.append({"role": "user", "content": prompt})

            response = await self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=messages,
                stop_sequences=[],
                **kwargs,
            )
            return response

        except Exception as e:
            # On "overloaded" message, Tenacity will retry.
            if "overloaded_error" in str(e).lower():
                current_app.logger.warning(f"Anthropic API overloaded, retrying: {e}")
                raise
            current_app.logger.error(f"Anthropic API error: {e}")
            raise

    # noinspection PyArgumentList
    def _track_usage(self, response: Any) -> None:
        """Track API usage."""
        from agents.models import Provider, Usage

        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens
        total_tokens = input_tokens + output_tokens

        usage = Usage(
            provider=Provider.ANTHROPIC,
            model_id=self.model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost=self._calculate_cost(input_tokens, output_tokens),
        )
        db.session.add(usage)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            current_app.logger.warning("Usage commit failed.")

        current_app.logger.debug(
            f"Anthropic usage tracked: {total_tokens} tokens used."
        )

    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost from tokens, using data from the AIModel DB row."""
        from agents.models import AIModel

        model = db.session.query(AIModel).filter_by(model_id=self.model).first()
        if not model:
            return 0.0

        return (input_tokens * float(model.input_rate) / 1_000_000) + (
            output_tokens * float(model.output_rate) / 1_000_000
        )

    @staticmethod
    def _extract_content(response: Any) -> str:
        """Parse the assistant's actual text from the API response."""
        return response.content[0].text.strip()

    async def generate(
        self, prompt: str, message_history: Optional[list] = None, **kwargs: Any
    ) -> str:
        """
        Public method to generate text from the Anthropic API.
        1) Calls the API with retry logic.
        2) Tracks usage in DB
        3) Extracts and returns the text.
        """
        if message_history is None:
            message_history = []

        response = await self._call_api(
            prompt, message_history=message_history, **kwargs
        )

        # track usage
        self._track_usage(response)

        # extract final content
        return AnthropicClient._extract_content(response)
