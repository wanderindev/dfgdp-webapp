import abc
from typing import Any, Optional


class BaseAIClient(abc.ABC):
    """
    Abstract base class for AI API clients.
    Exposes a single public async method `generate(...)`.
    """

    @abc.abstractmethod
    async def generate(
        self, prompt: str, message_history: Optional[list] = None, **kwargs: Any
    ) -> str:
        """
        Public async method to generate text from a prompt.
        Child classes must implement their own logic.
        """
        pass
