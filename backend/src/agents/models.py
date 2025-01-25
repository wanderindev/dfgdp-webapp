import enum
from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy import text, Index
from sqlalchemy.orm import Mapped, relationship

from extensions import db
from mixins.mixins import TimestampMixin


class AgentType(str, enum.Enum):
    CONTENT_MANAGER = "CONTENT_MANAGER"
    RESEARCHER = "RESEARCHER"
    WRITER = "WRITER"
    EDITOR = "EDITOR"
    SOCIAL_MEDIA = "SOCIAL_MEDIA"
    TRANSLATOR = "TRANSLATOR"
    MEDIA_MANAGER = "MEDIA_MANAGER"


class Provider(str, enum.Enum):
    OPENAI = "OPENAI"
    ANTHROPIC = "ANTHROPIC"


class AIModel(db.Model, TimestampMixin):
    """Track different AI models used for generation"""

    __tablename__ = "ai_models"

    id: Mapped[int] = db.Column(db.Integer, primary_key=True)
    name: Mapped[str] = db.Column(db.String(100), nullable=False, unique=True)
    provider: Mapped[Provider] = db.Column(
        db.Enum(Provider, name="provider_type"), nullable=False
    )
    model_id: Mapped[str] = db.Column(db.String(50), nullable=False)
    description: Mapped[Optional[str]] = db.Column(db.Text, nullable=True)
    is_active: Mapped[bool] = db.Column(
        db.Boolean, nullable=False, server_default=text("true")
    )

    # Usage cost tracking
    input_rate: Mapped[Optional[float]] = db.Column(db.DECIMAL(10, 2), nullable=True)
    batch_input_rate: Mapped[Optional[float]] = db.Column(
        db.DECIMAL(10, 2), nullable=True
    )
    output_rate: Mapped[Optional[float]] = db.Column(db.DECIMAL(10, 2), nullable=True)
    batch_output_rate: Mapped[Optional[float]] = db.Column(
        db.DECIMAL(10, 2), nullable=True
    )

    # Relationship to agents using this model
    agents: Mapped[List["Agent"]] = relationship(
        "Agent", backref="model", cascade="all, delete-orphan", passive_deletes=True
    )

    __table_args__ = (
        Index("idx_aimodel_provider", "provider"),
        Index("idx_aimodel_active", "is_active"),
    )


class Agent(db.Model, TimestampMixin):
    """Configuration for different AI agents"""

    __tablename__ = "agents"

    id: Mapped[int] = db.Column(db.Integer, primary_key=True)
    name: Mapped[str] = db.Column(db.String(100), nullable=False, unique=True)
    type: Mapped[AgentType] = db.Column(
        db.Enum(AgentType, name="agent_type"), nullable=False
    )
    description: Mapped[Optional[str]] = db.Column(db.Text, nullable=True)

    # AI Model relationship
    model_id: Mapped[int] = db.Column(
        db.Integer,
        db.ForeignKey("ai_models.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # Configuration
    temperature: Mapped[float] = db.Column(db.Float, nullable=False, default=0.7)
    max_tokens: Mapped[int] = db.Column(db.Integer, nullable=False)
    is_active: Mapped[bool] = db.Column(
        db.Boolean, nullable=False, server_default=text("true")
    )

    __table_args__ = (
        Index("idx_agent_type", "type"),
        Index("idx_agent_active", "is_active"),
    )


class Usage(db.Model, TimestampMixin):
    """Track API usage and costs"""

    __tablename__ = "api_usage"

    id: Mapped[int] = db.Column(db.Integer, primary_key=True)
    provider: Mapped[Provider] = db.Column(
        db.Enum(Provider, name="provider_type"), nullable=False
    )
    model_id: Mapped[str] = db.Column(db.String(50), nullable=False)
    input_tokens: Mapped[int] = db.Column(db.Integer, nullable=False)
    output_tokens: Mapped[int] = db.Column(db.Integer, nullable=False)
    cost: Mapped[float] = db.Column(db.Float, nullable=False)
    timestamp: Mapped[datetime] = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        Index("idx_usage_timestamp", "timestamp"),
        Index("idx_usage_provider_model", "provider", "model_id"),
    )
