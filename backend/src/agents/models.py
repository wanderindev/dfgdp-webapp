from datetime import datetime, timezone

from extensions import db


class AIGenerationMixin:
    """Mixin for tracking AI content generation metadata"""

    tokens_used = db.Column(db.Integer, nullable=True)
    model_id = db.Column(db.Integer, db.ForeignKey("ai_models.id"), nullable=True)
    generation_started_at = db.Column(db.DateTime(timezone=True), nullable=True)
    last_generation_error = db.Column(db.Text, nullable=True)


class AIModel(db.Model):
    """Track different AI models used for generation"""

    __tablename__ = "ai_models"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    provider = db.Column(db.String(50), nullable=False)  # e.g., "anthropic", "openai"
    model_id = db.Column(db.String(50), nullable=False)  # e.g., "gpt-4", "claude-3"
    description = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True)

    created_at = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
