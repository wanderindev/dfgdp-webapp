import json
from datetime import datetime, timezone
from typing import Any, List, TypeVar, Optional, Protocol

from flask import g
from slugify import slugify
from sqlalchemy import inspect
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
        """
        Get translation for a field in specified language.

        Args:
            field: Name of the field to get translation for
            language: Language code. If None, uses current language from Flask g
                     or falls back to default language

        Returns:
            Translated content or original field value if no translation exists
        """
        # Import here to avoid circular import
        from translations.models import ApprovedLanguage, Translation

        if language is None:
            # Get language from Flask g or fall back to default
            language = getattr(g, "language", None)
            if not language:
                default_lang = ApprovedLanguage.get_default_language()
                language = default_lang.code if default_lang else "en"

        # Get entity ID using inspect
        instance_state = inspect(self)
        try:
            mapper = instance_state.mapper
            pk = mapper.primary_key[0]
            entity_id = getattr(self, pk.name)
        except (AttributeError, IndexError):
            return getattr(self, field)

        # Look for translation
        translation = Translation.query.filter_by(
            entity_type=self.__tablename__,
            entity_id=entity_id,
            field=field,
            language=language,
        ).first()

        if translation:
            try:
                # Try to parse as JSON for complex types
                return json.loads(translation.content)
            except json.JSONDecodeError:
                return translation.content

        # Fallback to original value
        return getattr(self, field)

    def get_available_translations(self: T, field: str) -> List[str]:
        """
        Get list of available language codes for a field.

        Args:
            field: Name of the field to check translations for

        Returns:
            List of language codes that have translations
        """
        # Import here to avoid circular import
        from translations.models import Translation

        # Get entity ID using inspect
        instance_state = inspect(self)
        try:
            mapper = instance_state.mapper
            pk = mapper.primary_key[0]
            entity_id = getattr(self, pk.name)
        except (AttributeError, IndexError):
            return []

        translations = Translation.query.filter_by(
            entity_type=self.__tablename__, entity_id=entity_id, field=field
        ).all()

        return [t.language for t in translations]

    def has_translation(self: T, field: str, language: str) -> bool:
        """
        Check if a translation exists for a field in a specific language.

        Args:
            field: Name of the field to check
            language: Language code to check for

        Returns:
            bool: True if translation exists, False otherwise
        """
        # Import here to avoid circular import
        from translations.models import Translation

        # Get entity ID using inspect
        instance_state = inspect(self)
        try:
            mapper = instance_state.mapper
            pk = mapper.primary_key[0]
            entity_id = getattr(self, pk.name)
        except (AttributeError, IndexError):
            return False

        return (
            Translation.query.filter_by(
                entity_type=self.__tablename__,
                entity_id=entity_id,
                field=field,
                language=language,
            ).first()
            is not None
        )


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
