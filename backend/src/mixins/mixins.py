from datetime import datetime, timezone
from typing import List, Any

from extensions import db


class TimestampMixin:
    created_at = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class AIGenerationMixin:
    """Mixin for tracking AI content generation metadata"""

    tokens_used = db.Column(db.Integer, nullable=True)
    model_id = db.Column(db.Integer, db.ForeignKey("ai_models.id"), nullable=True)
    generation_started_at = db.Column(db.DateTime, nullable=True)
    last_generation_error = db.Column(db.Text, nullable=True)


# noinspection PyArgumentList,PyUnresolvedReferences
class TranslatableMixin:
    """Mixin for models that need translation support."""

    def get_translation(self, field: str, language: str = None) -> Any:
        """Interface method - implementation in translations.services"""
        from translations.services import get_translation

        return get_translation(self, field, language)

    def set_translation(
        self,
        field: str,
        language: str,
        content: Any,
        is_generated: bool = True,
        model_id: int = None,
    ) -> None:
        """Interface method - implementation in translations.services"""
        from translations.services import set_translation

        return set_translation(self, field, language, content, is_generated, model_id)

    def get_available_translations(self, field: str) -> List[str]:
        """Interface method - implementation in translations.services"""
        from translations.services import get_available_translations

        return get_available_translations(self, field)
