from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Type

from flask import current_app
from sqlalchemy import inspect

from extensions import db
from agents.models import Agent, AgentType
from content.models import ContentStatus
from translations.models import Translation, ApprovedLanguage
import json


# noinspection PyArgumentList
class TranslationHandler(ABC):
    """Base class for model-specific translation handlers"""

    def __init__(self, agent: Agent) -> None:
        self.agent = agent

    @abstractmethod
    def get_translatable_fields(self) -> List[str]:
        """
        Return list of fields that should be translated.
        Must be implemented by each handler.
        """
        pass

    @abstractmethod
    async def validate_entity(self, entity: Any) -> bool:
        """
        Validate if entity is ready for translation.
        Must be implemented by each handler.
        """
        pass

    async def pre_translate(self, entity: Any) -> None:
        """Hook called before translation starts"""
        pass

    async def post_translate(self, entity: Any, results: Dict[str, bool]) -> None:
        """Hook called after translation completes"""
        pass

    def get_entity_type(self) -> str:
        """Get the entity type name for translation records"""
        raise NotImplementedError(
            "Handler must implement get_entity_type() or override create_translation()"
        )

    async def create_translation(
        self,
        entity: Any,
        field: str,
        language: str,
        content: str,
    ) -> Optional[Translation]:
        """
        Create or update a translation record.

        Args:
            entity: The entity being translated
            field: Field name being translated
            language: Target language code
            content: Translated content

        Returns:
            Created/updated Translation object or None if failed
        """
        try:
            # Get entity primary key
            mapper = inspect(entity)
            if not mapper or not mapper.primary_key or not mapper.primary_key[0]:
                raise ValueError("Could not determine entity primary key")

            entity_id = mapper.primary_key[0]

            # Look for existing translation
            translation = Translation.query.filter_by(
                entity_type=self.get_entity_type(),
                entity_id=entity_id,
                field=field,
                language=language,
            ).first()

            if translation:
                # Update existing translation
                translation.content = content
                translation.is_generated = True
                translation.generated_at = datetime.now(timezone.utc)
                translation.generated_by_id = self.agent.model_id
            else:
                # Create new translation
                translation = Translation(
                    entity_type=self.get_entity_type(),
                    entity_id=entity_id,
                    field=field,
                    language=language,
                    content=content,
                    is_generated=True,
                    generated_at=datetime.now(timezone.utc),
                    generated_by_id=self.agent.model_id,
                )
                db.session.add(translation)

            db.session.commit()
            return translation

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(
                f"Error creating translation for {self.get_entity_type()}.{field}: {str(e)}"
            )
            return None


class TranslationService:
    """Service for managing content translations"""

    # Registry of model handlers
    _handlers: Dict[str, Type[TranslationHandler]] = {}

    def __init__(self) -> None:
        # Get the active translator agent
        self.agent = Agent.query.filter_by(
            type=AgentType.TRANSLATOR, is_active=True
        ).first()

        if not self.agent:
            raise ValueError("No active translator agent found")

        # Initialize handlers
        self.initialized_handlers: Dict[str, TranslationHandler] = {}
        for entity_type, handler_class in self._handlers.items():
            self.initialized_handlers[entity_type] = handler_class(self.agent)

    @classmethod
    def register_handler(
        cls, entity_type: str, handler: Type[TranslationHandler]
    ) -> None:
        """
        Register a translation handler for an entity type.

        Args:
            entity_type: The type of entity (e.g., 'article', 'category')
            handler: The handler class for this entity type
        """
        cls._handlers[entity_type] = handler

    async def translate_entity(
        self, entity: Any, target_language: str, fields: Optional[List[str]] = None
    ) -> Dict[str, bool]:
        """
        Translate an entity using its registered handler.

        Args:
            entity: The entity to translate
            target_language: Target language code
            fields: Optional list of specific fields to translate.
                   If None, translates all translatable fields.

        Returns:
            Dictionary mapping field names to translation success status
        """
        # Get the appropriate handler
        handler = self.initialized_handlers.get(entity.__tablename__)
        if not handler:
            raise ValueError(f"No handler registered for {entity.__tablename__}")

        # Validate language
        if not ApprovedLanguage.query.filter_by(
            code=target_language, is_active=True
        ).first():
            raise ValueError(f"Language {target_language} not approved for translation")

        # Get default language
        default_lang = ApprovedLanguage.get_default_language()
        if not default_lang:
            raise ValueError("No default language configured")

        # Validate entity
        if not await handler.validate_entity(entity):
            raise ValueError(f"Entity {entity.__tablename__} not valid for translation")

        # Determine fields to translate
        fields_to_translate = fields or handler.get_translatable_fields()
        results: Dict[str, bool] = {}

        try:
            # Call pre-translation hook
            await handler.pre_translate(entity)

            # Translate each field
            for field in fields_to_translate:
                success = await self._translate_field(
                    handler=handler,
                    entity=entity,
                    field=field,
                    source_language=default_lang.code,
                    target_language=target_language,
                )
                results[field] = success

            # Call post-translation hook
            await handler.post_translate(entity, results)

            return results

        except Exception as e:
            current_app.logger.error(f"Translation error: {str(e)}")
            # Fill remaining fields with False if error occurred mid-translation
            for field in fields_to_translate:
                if field not in results:
                    results[field] = False
            return results

    async def _translate_field(
        self,
        handler: TranslationHandler,
        entity: Any,
        field: str,
        source_language: str,
        target_language: str,
    ) -> bool:
        """
        Translate a single field using the translation agent.

        Returns:
            bool: True if translation successful, False otherwise
        """
        try:
            # Get source content
            source_content = entity.get_translation(field, source_language)
            if not source_content:
                source_content = getattr(entity, field)

            # Generate translation using agent
            translated_content = await self.agent.generate_content(
                prompt=self._build_translation_prompt(
                    content=source_content,
                    source_language=source_language,
                    target_language=target_language,
                    entity_type=handler.get_entity_type(),
                    field=field,
                )
            )

            # Create translation record
            translation = await handler.create_translation(
                entity=entity,
                field=field,
                language=target_language,
                content=translated_content,
            )

            return translation is not None

        except Exception as e:
            current_app.logger.error(
                f"Error translating {handler.get_entity_type()}.{field}: {str(e)}"
            )
            return False

    def _build_translation_prompt(
        self,
        content: str,
        source_language: str,
        target_language: str,
        entity_type: str,
        field: str,
    ) -> str:
        """Build the prompt for the translation agent"""
        template = self.agent.get_template(
            "translate_metadata"
            if field in ["title", "name", "alt_text"]
            else "translate_content"
        )

        if not template:
            raise ValueError("Translation template not found")

        return template.render(
            content=content,
            source_language=source_language,
            target_language=target_language,
            entity_type=entity_type,
            field=field,
        )


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
