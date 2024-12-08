from typing import Any, Dict

from anthropic import AsyncAnthropic
from anthropic.types import Message
from flask import current_app

from extensions import db
from .base import BaseAIClient


# noinspection PyArgumentList
class AnthropicClient(BaseAIClient):
    """Client for Anthropic API"""

    client: AsyncAnthropic

    def _init_client(self) -> None:
        """Initialize Anthropic client"""
        self.client = AsyncAnthropic(api_key=current_app.config["ANTHROPIC_API_KEY"])

    async def _generate_content(self, prompt: str, **kwargs: Any) -> Message:
        """
        Generate content using Anthropic API

        Args:
            prompt: The input prompt text
            **kwargs: Additional arguments to pass to the API

        Returns:
            Message: The Anthropic API response

        Raises:
            Exception: If the API call fails
        """
        try:
            return await self.client.messages.create(
                model=self.model,  # Use model from parent
                max_tokens=self.max_tokens,  # Use max_tokens from parent
                temperature=self.temperature,  # Use temperature from parent
                messages=[{"role": "user", "content": prompt}],
                **kwargs,
            )
        except Exception as e:
            current_app.logger.error(f"Anthropic API error: {str(e)}")
            raise

    async def _track_usage(self, response: Message) -> None:
        """
        Track API usage statistics

        Args:
            response: The Anthropic API response to track
        """
        from ..models import Provider, Usage

        usage = Usage(
            provider=Provider.OPENAI,
            model_id=self.model,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            cost=self._calculate_cost(response.usage),
        )
        db.session.add(usage)
        await db.session.commit()

    def _calculate_cost(self, usage: Any) -> float:
        """
        Calculate the cost of API usage

        Args:
            usage: Usage statistics from the API response

        Returns:
            float: The calculated cost in USD
        """
        # OpenAI pricing per 1K tokens (adjust as needed)
        model_rates: Dict[str, Dict[str, float]] = {
            "gpt-4-turbo-preview": {"input": 0.01, "output": 0.03}
        }
        rates = model_rates.get(self.model)
        if not rates:
            return 0.0

        return (usage.input_tokens * rates["input"] / 1000) + (
            usage.output_tokens * rates["output"] / 1000
        )

    def _extract_content(self, response: Message) -> str:
        """
        Extract the generated content from the API response

        Args:
            response: The Anthropic API response

        Returns:
            str: The extracted content text
        """
        return response.content[0].text.strip()
