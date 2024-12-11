from typing import Any

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
                    {
                        "role": "assistant",
                        "content": "You are a thorough researcher for a historical and cultural education platform.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=self.temperature,
                max_completion_tokens=self.max_tokens,
                presence_penalty=0.3,
                frequency_penalty=0.3,
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
        Calculate the cost of API usage using rates from the database

        Args:
            input_tokens: The number of input tokens used
            output_tokens: The number of output tokens used

        Returns:
            float: The calculated cost in USD
        """
        from ..models import AIModel

        # Get model rates from database
        model = AIModel.query.filter_by(model_id=self.model).first()
        if not model:
            return 0.0

        # Calculate cost using rates per million tokens
        return (input_tokens * float(model.input_rate) / 1000000) + (
            output_tokens * float(model.output_rate) / 1000000
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
