from typing import Any, Dict

from anthropic import Anthropic
from anthropic.types import Message
from flask import current_app

from extensions import db
from .base import BaseAIClient


# noinspection PyArgumentList
class AnthropicClient(BaseAIClient):
    """Client for Anthropic API"""

    client: Anthropic

    def _init_client(self) -> None:
        """Initialize Anthropic client"""
        self.client = Anthropic(api_key=current_app.config["ANTHROPIC_API_KEY"])

    def _generate_content(self, prompt: str, **kwargs: Any) -> Message:
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
            response = self.client.messages.create(
                model=self.model,  # Use model from parent
                max_tokens=self.max_tokens,  # Use max_tokens from parent
                temperature=self.temperature,  # Use temperature from parent
                messages=[{"role": "user", "content": prompt}],
                **kwargs,
            )
            return response

        except Exception as e:
            current_app.logger.error(f"Anthropic API error: {str(e)}")
            raise

    def _track_usage(self, response: Message) -> int:
        """
        Track API usage statistics

        Args:
            response: The Anthropic API response to track

        Returns:
            total_tokens: The total number of tokens used
        """
        from ..models import Provider, Usage

        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens
        total_tokens = input_tokens + output_tokens

        usage = Usage(
            provider=Provider.ANTHROPIC,
            model_id=self.model,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            cost=self._calculate_cost(input_tokens, output_tokens),
        )
        db.session.add(usage)
        db.session.commit()

        return total_tokens

    def _calculate_cost(self, input_tokens, output_tokens: Any) -> float:
        """
        Calculate the cost of API usage

        Args:
            input_tokens: The number of input tokens used
            output_tokens: The number of output tokens used

        Returns:
            float: The calculated cost in USD
        """

        # Claude 3 pricing per 1K tokens (as of March 2024)
        model_rates: Dict[str, Dict[str, float]] = {
            "claude-3-5-sonnet-latest": {"input": 0.003, "output": 0.015},
        }
        rates = model_rates.get(self.model)
        if not rates:
            return 0.0

        return (input_tokens * rates["input"] / 1000) + (
            output_tokens * rates["output"] / 1000
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
