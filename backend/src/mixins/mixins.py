from datetime import datetime, timezone
from typing import Any, List, TypeVar, Union, Optional, Protocol

from flask import g
from slugify import slugify
from sqlalchemy.orm import Mapped, declared_attr

from extensions import db
from translations.models import ApprovedLanguage


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


# noinspection PyUnresolvedReferences
class SlugMixin:
    """Mixin for models that need language-aware slugs"""

    @property
    def slug(self) -> str:
        """
        Generate slug from translated title/name based on current language.

        The slug is generated from either the 'title' or 'name' field,
        depending on which one exists in the model.

        Returns:
            str: URL-friendly slug
        """
        # Get current language from Flask g object
        current_lang = getattr(g, "language", None)

        # Fallback to default language if not set
        if not current_lang:
            default_lang = ApprovedLanguage.get_default_language()
            current_lang = default_lang.code if default_lang else "en"

        # Get the source field for slug generation (title or name)
        if hasattr(self, "title"):
            source_field = "title"
        elif hasattr(self, "name"):
            source_field = "name"
        else:
            raise AttributeError(
                "Model must have either 'title' or 'name' attribute to generate slug"
            )

        # Get the source field value in the current language
        source_value = self.get_translation(source_field, current_lang)

        # If no translation exists, use the original value
        if not source_value:
            source_value = getattr(self, source_field)

        # Generate and return the slug
        return slugify(source_value)

    def get_slug(self, language: Optional[str] = None) -> str:
        """
        Get slug for a specific language.

        Args:
            language: Language code. If None, uses current language
                     from Flask g object or falls back to default language.

        Returns:
            str: URL-friendly slug for the specified language
        """
        if not language:
            language = getattr(g, "language", None)
            if not language:
                default_lang = ApprovedLanguage.get_default_language()
                language = default_lang.code if default_lang else "en"

        # Get the source field for slug generation (title or name)
        if hasattr(self, "title"):
            source_field = "title"
        elif hasattr(self, "name"):
            source_field = "name"
        else:
            raise AttributeError(
                "Model must have either 'title' or 'name' attribute to generate slug"
            )

        # Get the source field value in the specified language
        source_value = self.get_translation(source_field, language)

        # If no translation exists, use the original value
        if not source_value:
            source_value = getattr(self, source_field)

        # Generate and return the slug
        return slugify(source_value)
