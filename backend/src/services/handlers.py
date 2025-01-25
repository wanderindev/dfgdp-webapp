import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from flask import current_app

from content.models import ContentStatus
from extensions import db
from translations.models import Translation
from services.translator_service import TranslationHandler


class TaxonomyTranslationHandler(TranslationHandler):
    """Handler for Taxonomy translations"""

    def get_translatable_fields(self) -> List[str]:
        """Get fields that should be translated"""
        return ["name", "description"]

    def get_entity_type(self) -> str:
        """Get entity type name"""
        return "taxonomies"

    async def validate_entity(self, entity: Any) -> bool:
        """
        Validate if taxonomy is ready for translation.
        Taxonomies don't have a status field, so we just verify
        they have required fields.
        """
        return bool(entity.name and entity.description)


class CategoryTranslationHandler(TranslationHandler):
    """Handler for Category translations"""

    def get_translatable_fields(self) -> List[str]:
        """Get fields that should be translated"""
        return ["name", "description"]

    def get_entity_type(self) -> str:
        """Get entity type name"""
        return "categories"

    async def validate_entity(self, entity: Any) -> bool:
        """
        Validate if category is ready for translation.
        Categories don't have a status field, so we verify required fields
        and that parent taxonomy exists.
        """
        return bool(
            entity.name
            and entity.description
            and entity.taxonomy_id
            and entity.taxonomy
        )


class TagTranslationHandler(TranslationHandler):
    """Handler for Tag translations"""

    def get_translatable_fields(self) -> List[str]:
        """Get fields that should be translated"""
        return ["name"]

    def get_entity_type(self) -> str:
        """Get entity type name"""
        return "tags"

    async def validate_entity(self, entity: Any) -> bool:
        """
        Validate if tag is ready for translation.
        Only translate approved tags.
        """
        return bool(entity.name and entity.status == ContentStatus.APPROVED)


class ArticleTranslationHandler(TranslationHandler):
    """Handler for Article translations"""

    def get_translatable_fields(self) -> List[str]:
        """Get fields that should be translated"""
        return ["title", "content", "excerpt"]

    def get_entity_type(self) -> str:
        """Get entity type name"""
        return "articles"

    async def validate_entity(self, entity: Any) -> bool:
        """
        Validate if article is ready for translation.
        Only translate approved articles with all required fields.
        """
        return bool(
            entity.title and entity.content and entity.status == ContentStatus.APPROVED
        )

    async def pre_translate(self, entity: Any) -> None:
        """
        Before translation, ensure we have an excerpt if none exists.
        AI summary is optional.
        """
        if not entity.excerpt:
            current_app.logger.warning(
                f"Article {entity.id} missing excerpt before translation"
            )

    async def post_translate(self, entity: Any, results: Dict[str, bool]) -> None:
        """After translation, update translation timestamp if successful"""
        if all(results.values()):
            # All translations successful
            try:
                entity.translations_updated_at = datetime.now(timezone.utc)
                db.session.commit()
            except Exception as e:
                current_app.logger.error(
                    f"Error updating translation timestamp for article {entity.id}: {str(e)}"
                )
                db.session.rollback()


class MediaTranslationHandler(TranslationHandler):
    """Handler for Media translations"""

    def get_translatable_fields(self) -> List[str]:
        """Get fields that should be translated"""
        return ["title", "caption", "alt_text", "attribution"]

    def get_entity_type(self) -> str:
        """Get entity type name"""
        return "media"

    async def validate_entity(self, entity: Any) -> bool:
        """
        Validate if media is ready for translation.
        Require at least title or alt_text.
        """
        return bool(entity.title or entity.alt_text)


class SocialMediaPostTranslationHandler(TranslationHandler):
    """Handler for SocialMediaPost translations"""

    def get_translatable_fields(self) -> List[str]:
        """Get fields that should be translated"""
        return ["content", "hashtags"]

    def get_entity_type(self) -> str:
        """Get entity type name"""
        return "social_media_posts"

    async def validate_entity(self, entity: Any) -> bool:
        """
        Validate if post is ready for translation.
        Only translate approved posts that haven't been published.
        """
        return bool(
            entity.content
            and entity.status == ContentStatus.APPROVED
            and not entity.posted_at
        )

    async def create_translation(
        self,
        entity: Any,
        field: str,
        language: str,
        content: str,
        generation_started_at: Optional[datetime] = None,
        model_id: Optional[int] = None,
    ) -> Optional[Translation]:
        """
        Override create_translation for hashtags field to handle list conversion
        """
        if field == "hashtags":
            try:
                # Convert string back to list
                content = [tag.strip() for tag in content.split(",") if tag.strip()]
                # Convert to JSON for storage
                content = json.dumps(content)
            except Exception as e:
                current_app.logger.error(
                    f"Error processing hashtag translation: {str(e)}"
                )
                return None

        return await super().create_translation(entity, field, language, content)

    async def post_translate(self, entity: Any, results: Dict[str, bool]) -> None:
        """After translation, update scheduling if needed"""
        if all(results.values()) and entity.scheduled_for:
            try:
                # Update scheduling metadata
                entity.translation_ready = True
                db.session.commit()
            except Exception as e:
                current_app.logger.error(
                    f"Error updating post {entity.id} scheduling: {str(e)}"
                )
                db.session.rollback()
