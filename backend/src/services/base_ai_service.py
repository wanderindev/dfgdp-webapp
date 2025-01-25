from typing import Optional

from agents.clients.anthropic_client import AnthropicClient
from agents.models import Agent, AgentType, Provider
from extensions import db


class BaseAIService:
    """
    Asynchronous base service that loads the appropriate agent & client.
    """

    def __init__(self, agent_type: AgentType) -> None:
        self.agent: Optional[Agent] = (
            db.session.query(Agent).filter_by(type=agent_type, is_active=True).first()
        )

        if not self.agent:
            raise ValueError(f"No active agent found for type {agent_type}")

        provider = self.agent.model.provider
        if provider == Provider.ANTHROPIC:
            self.client = AnthropicClient(
                model=self.agent.model.model_id,
                temperature=self.agent.temperature,
                max_tokens=self.agent.max_tokens,
                rate_limit=100,
            )
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    async def generate_content(self, prompt: str, message_history: list = None) -> str:
        """
        Helper method for derived services. Delegates to the client's async generate.
        """
        if message_history is None:
            message_history = []

        # All the waiting and usage tracking is done inside AnthropicClient.
        content = await self.client.generate(prompt, message_history=message_history)
        return content
