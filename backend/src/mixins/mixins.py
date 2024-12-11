from datetime import datetime, timezone
from typing import Any, List, TypeVar, Union, Optional, Protocol
from sqlalchemy.orm import Mapped, declared_attr
from extensions import db


class HasId(Protocol):
    """Protocol for objects that have an id attribute"""

    id: Any


T = TypeVar("T", bound=HasId)


class TimestampMixin:
    """Mixin for automatic timestamp management"""

    created_at: Mapped[datetime] = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    updated_at: Mapped[datetime] = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


# noinspection PyMethodParameters
class AIGenerationMixin:
    """Mixin for tracking AI content generation metadata"""

    tokens_used: Mapped[Optional[int]] = db.Column(db.Integer, nullable=True)

    @declared_attr
    def model_id(cls) -> Mapped[Optional[int]]:
        return db.Column(
            db.Integer,
            db.ForeignKey("ai_models.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        )

    generation_started_at: Mapped[Optional[datetime]] = db.Column(
        db.DateTime(timezone=True), nullable=True
    )

    last_generation_error: Mapped[Optional[str]] = db.Column(db.Text, nullable=True)


class TranslatableMixin:
    """Mixin for models that support field translations"""

    def get_translation(self: T, field: str, language: Optional[str] = None) -> Any:
        """Get translation for a field in specified language."""
        from translations.services import get_translation

        return get_translation(self, field, language)

    def set_translation(
        self: T,
        field: str,
        language: str,
        content: Union[str, dict, list],
        is_generated: bool = True,
        model_id: Optional[int] = None,
    ) -> None:
        """Set translation for a field in specified language."""
        from translations.services import set_translation

        return set_translation(self, field, language, content, is_generated, model_id)

    def get_available_translations(self: T, field: str) -> List[str]:
        """Get list of available language codes for a field."""
        from translations.services import get_available_translations

        return get_available_translations(self, field)
