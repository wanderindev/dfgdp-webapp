from datetime import datetime, timezone
from typing import Any, List, TypeVar, Union, Optional

from sqlalchemy.orm import DeclarativeMeta, Mapped

from extensions import db

# Create a type that represents classes that use this mixin
SelfT = TypeVar("SelfT", bound=Union[DeclarativeMeta, "TranslatableMixin"])


class TimestampMixin:
    created_at: Mapped[datetime] = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class AIGenerationMixin:
    """Mixin for tracking AI content generation metadata"""

    tokens_used: Mapped[Optional[int]] = db.Column(db.Integer, nullable=True)
    model_id: Mapped[Optional[int]] = db.Column(
        db.Integer, db.ForeignKey("ai_models.id"), nullable=True
    )
    generation_started_at: Mapped[Optional[datetime]] = db.Column(
        db.DateTime, nullable=True
    )
    last_generation_error: Mapped[Optional[str]] = db.Column(db.Text, nullable=True)


# noinspection PyArgumentList,PyUnresolvedReferences
class TranslatableMixin:
    """Mixin for models that need translation support."""

    def get_translation(self: SelfT, field: str, language: Optional[str] = None) -> Any:
        """Get translation for a field in specified language."""
        from translations.services import get_translation

        return get_translation(self, field, language)

    def set_translation(
        self: SelfT,
        field: str,
        language: str,
        content: Union[str, dict, list],
        is_generated: bool = True,
        model_id: Optional[int] = None,
    ) -> None:
        """Set translation for a field in specified language."""
        from translations.services import set_translation

        return set_translation(self, field, language, content, is_generated, model_id)

    def get_available_translations(self: SelfT, field: str) -> List[str]:
        """Get list of available language codes for a field."""
        from translations.services import get_available_translations

        return get_available_translations(self, field)
