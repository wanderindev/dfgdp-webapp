import enum
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Type, Tuple, List

from flask import current_app
from sqlalchemy import func
from sqlalchemy.orm import Mapped, relationship

from agents.clients import BaseAIClient, OpenAIClient, AnthropicClient
from extensions import db
from mixins.mixins import TimestampMixin


class AgentType(enum.Enum):
    CONTENT_MANAGER = "content_manager"
    RESEARCHER = "researcher"
    WRITER = "writer"
    SOCIAL_MEDIA = "social_media"
    TRANSLATOR = "translator"


class Provider(enum.Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class AIModel(db.Model, TimestampMixin):
    """Track different AI models used for generation"""

    __tablename__ = "ai_models"

    id: Mapped[int] = db.Column(db.Integer, primary_key=True)
    name: Mapped[str] = db.Column(db.String(100), nullable=False)
    provider: Mapped[Provider] = db.Column(db.Enum(Provider), nullable=False)
    model_id: Mapped[str] = db.Column(db.String(50), nullable=False)
    description: Mapped[Optional[str]] = db.Column(db.Text, nullable=True)
    is_active: Mapped[bool] = db.Column(db.Boolean, default=True)

    # Usage cost tracking
    input_rate: Mapped[float] = db.Column(db.DECIMAL(10, 2), nullable=True)
    batch_input_rate: Mapped[float] = db.Column(db.DECIMAL(10, 2), nullable=True)
    output_rate: Mapped[float] = db.Column(db.DECIMAL(10, 2), nullable=True)
    batch_output_rate: Mapped[float] = db.Column(db.DECIMAL(10, 2), nullable=True)

    # Relationship to agents using this model
    agents: Mapped[List["Agent"]] = relationship("Agent", backref="model")

    def get_api_key(self) -> Optional[str]:
        """Get the appropriate API key based on the provider."""
        if self.provider == Provider.OPENAI:
            return current_app.config.get("OPENAI_API_KEY")
        elif self.provider == Provider.ANTHROPIC:
            return current_app.config.get("ANTHROPIC_API_KEY")
        return None


class Agent(db.Model, TimestampMixin):
    """Configuration for different AI agents"""

    __tablename__ = "agents"

    id: Mapped[int] = db.Column(db.Integer, primary_key=True)
    name: Mapped[str] = db.Column(db.String(100), nullable=False, unique=True)
    type: Mapped[AgentType] = db.Column(db.Enum(AgentType), nullable=False)
    description: Mapped[Optional[str]] = db.Column(db.Text, nullable=True)

    # AI Model relationship
    model_id: Mapped[int] = db.Column(
        db.Integer, db.ForeignKey("ai_models.id"), nullable=False
    )

    # Configuration
    temperature: Mapped[float] = db.Column(db.Float, nullable=False, default=0.7)
    max_tokens: Mapped[int] = db.Column(db.Integer, nullable=False)
    is_active: Mapped[bool] = db.Column(db.Boolean, default=True)

    # Relationship to prompt templates
    prompts: Mapped[List["PromptTemplate"]] = relationship(
        "PromptTemplate", backref="agent", lazy=True
    )

    def get_template(self, name: str) -> Optional["PromptTemplate"]:
        """Get an active template by name."""
        return PromptTemplate.query.filter_by(
            agent_id=self.id, name=name, is_active=True
        ).first()

    def render_template(self, template_name: str, **kwargs: Any) -> Optional[str]:
        """
        Render a template with the provided variables.

        Args:
            template_name: Template name
            **kwargs: Variables to interpolate into the template

        Returns:
            Rendered template string or None if template not found
        """
        template = self.get_template(template_name)
        if template:
            try:
                return template.render(**kwargs)
            except Exception as e:
                current_app.logger.error(
                    f"Error rendering template {template_name}: {str(e)}"
                )
                return None
        return None

    def get_config(self) -> Dict[str, Any]:
        """Get complete agent configuration including model details."""
        return {
            "name": self.name,
            "type": self.type.value,
            "model_name": self.model.name,
            "model_provider": self.model.provider.value,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "api_key": self.model.get_api_key(),
        }

    def validate_config(self) -> Tuple[bool, Optional[str]]:
        """
        Validate agent configuration is complete and valid.

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not self.is_active:
            return False, "Agent is not active"

        if not self.model.is_active:
            return False, f"Model {self.model.name} is not active"

        if not self.model.get_api_key():
            return False, f"Missing API key for {self.model.provider.value}"

        if not any(p.is_active for p in self.prompts):
            return False, "No active prompt templates found"

        return True, None

    def get_client(self) -> BaseAIClient:
        """Get the appropriate AI client for this agent."""
        # Map providers to client classes
        client_map: Dict[Provider, Type[BaseAIClient]] = {
            Provider.OPENAI: OpenAIClient,
            Provider.ANTHROPIC: AnthropicClient,
        }

        # noinspection PyPep8Naming
        ClientClass = client_map.get(self.model.provider)
        if not ClientClass:
            raise ValueError(
                f"No client implementation for provider {self.model.provider}"
            )

        return ClientClass(
            model=self.model.model_id,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )

    async def generate_content(self, prompt: str, **kwargs: Any) -> str:
        """Generate content using this agent's configuration."""
        client = self.get_client()
        return await client.generate(prompt, **kwargs)


class PromptTemplate(db.Model, TimestampMixin):
    """Store editable prompt templates for agents"""

    __tablename__ = "prompt_templates"

    id: Mapped[int] = db.Column(db.Integer, primary_key=True)
    agent_id: Mapped[int] = db.Column(
        db.Integer, db.ForeignKey("agents.id"), nullable=False
    )
    name: Mapped[str] = db.Column(db.String(100), nullable=False)
    description: Mapped[Optional[str]] = db.Column(db.Text, nullable=True)
    template: Mapped[str] = db.Column(db.Text, nullable=False)
    is_active: Mapped[bool] = db.Column(db.Boolean, default=True)

    __table_args__ = (
        db.UniqueConstraint("agent_id", "name", name="unique_template_name_per_agent"),
    )

    def render(self, **kwargs: Any) -> str:
        """
        Render the template with the provided variables.

        Args:
            **kwargs: Variables to interpolate into the template

        Returns:
            Rendered template string

        Raises:
            ValueError: If template rendering fails
        """
        try:
            # First format any newlines properly
            template = self.template.replace("\\n", "\n")
            # Then render with provided variables
            return template.format(**kwargs)
        except KeyError as e:
            raise ValueError(f"Missing required template variable: {str(e)}")
        except Exception as e:
            raise ValueError(f"Template rendering error: {str(e)}")


class Usage(db.Model, TimestampMixin):
    """Track API usage and costs"""

    __tablename__ = "api_usage"

    id: Mapped[int] = db.Column(db.Integer, primary_key=True)
    provider: Mapped[Provider] = db.Column(db.Enum(Provider), nullable=False)
    model_id: Mapped[str] = db.Column(db.String(50), nullable=False)
    input_tokens: Mapped[int] = db.Column(db.Integer, nullable=False)
    output_tokens: Mapped[int] = db.Column(db.Integer, nullable=False)
    cost: Mapped[float] = db.Column(db.Float, nullable=False)
    timestamp: Mapped[datetime] = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    @classmethod
    def get_usage_summary(
        cls, start_date: datetime, end_date: datetime
    ) -> List[Tuple[Provider, int, int, float]]:
        """Get usage summary for a date range."""
        return (
            db.session.query(
                cls.provider,
                func.sum(cls.input_tokens).label("total_input_tokens"),
                func.sum(cls.output_tokens).label("total_output_tokens"),
                func.sum(cls.cost).label("total_cost"),
            )
            .filter(cls.timestamp.between(start_date, end_date))
            .group_by(cls.provider)
            .all()
        )
