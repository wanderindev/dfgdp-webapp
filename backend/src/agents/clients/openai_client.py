from typing import Any, Dict

from flask import current_app
from openai import OpenAI
from openai.types.chat import ChatCompletion

from extensions import db
from .base import BaseAIClient


# noinspection PyArgumentList
class OpenAIClient(BaseAIClient):
    """Client for OpenAI API"""

    client: OpenAI

    def _init_client(self) -> None:
        """Initialize OpenAI client"""
        self.client = OpenAI(api_key=current_app.config["OPENAI_API_KEY"])

    def _generate_content(self, prompt: str, **kwargs: Any) -> ChatCompletion:
        """
        Generate content using OpenAI API

        Args:
            prompt: The input prompt text
            **kwargs: Additional arguments to pass to the API

        Returns:
            ChatCompletion: The OpenAI API response

        Raises:
            Exception: If the API call fails
        """
        try:
            return self.client.chat.completions.create(
                model=self.model,  # Use model from parent
                messages=[
                    {"role": "system", "content": "You are a helpful AI assistant."},
                    {"role": "user", "content": prompt},
                ],
                temperature=self.temperature,  # Use temperature from parent
                max_tokens=self.max_tokens,  # Use max_tokens from parent
                **kwargs,
            )
        except Exception as e:
            current_app.logger.error(f"OpenAI API error: {str(e)}")
            raise

    def _track_usage(self, response: ChatCompletion) -> int:
        """
        Track API usage statistics

        Args:
            response: The OpenAI API response to track

        Returns:
            total_tokens: The total number of tokens used
        """
        from ..models import Provider, Usage

        input_tokens = response.usage.prompt_tokens
        output_tokens = response.usage.completion_tokens
        total_tokens = input_tokens + output_tokens

        usage = Usage(
            provider=Provider.OPENAI,
            model_id=self.model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost=self._calculate_cost(input_tokens, output_tokens),
        )
        db.session.add(usage)
        db.session.commit()

        return total_tokens

    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """
        Calculate the cost of API usage

        Args:
            input_tokens: The number of input tokens used
            output_tokens: The number of output tokens used

        Returns:
            float: The calculated cost in USD
        """
        # OpenAI pricing per 1K tokens (as of March 2024)
        model_rates: Dict[str, Dict[str, float]] = {
            "GPT-4o": {"input": 0.0025, "output": 0.01},
        }
        rates = model_rates.get(self.model)
        if not rates:
            return 0.0

        return (input_tokens * rates["input"] / 1000) + (
            output_tokens * rates["output"] / 1000
        )

    def _extract_content(self, response: ChatCompletion) -> str:
        """
        Extract the generated content from the API response

        Args:
            response: The OpenAI API response

        Returns:
            str: The extracted content text
        """
        return response.choices[0].message.content.strip()
