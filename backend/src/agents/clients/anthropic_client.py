from typing import Any, Dict, List, Optional

from anthropic import Anthropic
from anthropic.types import Message
from flask import current_app
from tenacity import retry, stop_after_attempt, wait_exponential

from extensions import db
from .base import BaseAIClient


# noinspection PyArgumentList
class AnthropicClient(BaseAIClient):
    """Client for Anthropic API"""

    client: Anthropic

    def _init_client(self) -> None:
        """Initialize Anthropic client"""
        self.client = Anthropic(api_key=current_app.config["ANTHROPIC_API_KEY"])

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=2, min=4, max=20),
        retry_error_callback=lambda retry_state: retry_state.outcome.result(),
    )
    def _generate_content(
        self,
        prompt: str,
        message_history: Optional[List[Dict[str, str]]] = None,
        **kwargs: Any,
    ) -> Message:
        """
        Generate content using Anthropic API with retry logic

        Args:
            prompt: The input prompt text
            message_history: Previous messages in the conversation
            **kwargs: Additional arguments to pass to the API

        Returns:
            Message: The Anthropic API response
        """
        try:
            messages = message_history or []
            messages.append({"role": "user", "content": prompt})

            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=messages,
                stop_sequences=[],
                **kwargs,
            )
            return response

        except Exception as e:
            if "overloaded_error" in str(e):
                current_app.logger.warning(
                    f"Anthropic API overloaded, retrying: {str(e)}"
                )
                raise  # This will trigger retry
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

    def _extract_content(self, response: Message) -> str:
        """
        Extract the generated content from the API response

        Args:
            response: The Anthropic API response

        Returns:
            str: The extracted content text
        """
        return response.content[0].text.strip()
