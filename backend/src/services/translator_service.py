from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Type

from flask import current_app

from agents.models import AgentType
from agents.prompts.translator_prompts import (
    TRANSLATE_CONTENT_PROMPT,
    TRANSLATE_METADATA_PROMPT,
)
from extensions import db
from services.base_ai_service import BaseAIService
from translations.models import Translation, ApprovedLanguage


class TranslationHandler(ABC):
    """Base class for model-specific translation handlers"""

    def __init__(self, agent: Any) -> None:
        """
        Args:
            agent: The translator agent (provided by the TranslationService)
        """
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
        """Optional hook called before translation starts"""
        pass

    async def post_translate(self, entity: Any, results: Dict[str, bool]) -> None:
        """Optional hook called after translation completes"""
        pass

    def get_entity_type(self) -> str:
        """
        Return the entity type name, e.g., 'articles', 'categories'.
        Must match the DB table name or custom type used in the Translation table.
        If not overridden, you'll need to override create_translation() instead.
        """
        raise NotImplementedError(
            "Handler must implement get_entity_type() or override create_translation()"
        )

    # noinspection PyArgumentList
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
        Create or update a Translation record for the given entity & field.
        """
        from flask import current_app
        from sqlalchemy import inspect

        try:
            # Attempt to get the primary key from the entity
            instance_state = inspect(entity)
            mapper = instance_state.mapper
            pk = mapper.primary_key[0]
            entity_id = getattr(entity, pk.name)

            # Check if a translation record already exists
            translation = (
                db.session.query(Translation)
                .filter_by(
                    entity_type=self.get_entity_type(),
                    entity_id=entity_id,
                    field=field,
                    language=language,
                )
                .first()
            )

            if translation:
                # Update existing translation
                translation.content = content
                translation.is_generated = True
                translation.generated_at = datetime.now(timezone.utc)
                translation.generated_by_id = self.agent.model_id
                translation.generation_started_at = generation_started_at
                translation.model_id = model_id
            else:
                # Create a new Translation record
                translation = Translation(
                    entity_type=self.get_entity_type(),
                    entity_id=entity_id,
                    field=field,
                    language=language,
                    content=content,
                    is_generated=True,
                    generated_at=datetime.now(timezone.utc),
                    generated_by_id=self.agent.model_id,
                    generation_started_at=generation_started_at,
                    model_id=model_id,
                )
                db.session.add(translation)

            db.session.commit()
            return translation

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(
                f"Error creating translation for {self.get_entity_type()}.{field}: {e}"
            )
            return None


class TranslatorService(BaseAIService):
    """
    Main service for managing content translations.
    """

    # Registry of model handlers (e.g., articles, categories, etc.)
    _handlers: Dict[str, Type[TranslationHandler]] = {}

    def __init__(self) -> None:
        super().__init__(AgentType.TRANSLATOR)

        # Initialize handlers
        self.initialized_handlers: Dict[str, TranslationHandler] = {}
        for entity_type, handler_class in self._handlers.items():
            self.initialized_handlers[entity_type] = handler_class(self.agent)

    @classmethod
    def register_handler(
        cls, entity_type: str, handler: Type[TranslationHandler]
    ) -> None:
        """
        Register a translation handler for a given entity type.
        """
        cls._handlers[entity_type] = handler

    async def translate_entity(
        self, entity: Any, target_language: str, fields: Optional[List[str]] = None
    ) -> Dict[str, bool]:
        """
        Translate all or some fields of the given entity.
        """

        # Determine which handler to use, based on entity.__tablename__
        handler = self.initialized_handlers.get(entity.__tablename__)
        if not handler:
            raise ValueError(f"No handler registered for {entity.__tablename__}")

        # Validate the requested target language is approved & active
        if (
            not db.session.query(ApprovedLanguage)
            .filter_by(code=target_language, is_active=True)
            .first()
        ):
            raise ValueError(
                f"Language '{target_language}' is not approved for translation"
            )

        # Get the default language for the system
        default_lang = ApprovedLanguage.get_default_language()
        if not default_lang:
            raise ValueError("No default language configured")

        # Validate the entity is ready for translation
        if not await handler.validate_entity(entity):
            raise ValueError(f"Entity {entity.__tablename__} not valid for translation")

        # Determine which fields to translate
        fields_to_translate = fields or handler.get_translatable_fields()
        results: Dict[str, bool] = {}

        try:
            # Pre-translation hook
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

            # Post-translation hook
            await handler.post_translate(entity, results)

            return results

        except Exception as e:
            current_app.logger.error(f"Translation error: {e}")
            # Mark any unprocessed fields as False
            for f in fields_to_translate:
                if f not in results:
                    results[f] = False
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
        Translate a single field from source_language to target_language.
        """
        try:
            # Get the source content
            source_content = entity.get_translation(field, source_language)
            if not source_content:
                # fallback to the field's direct value if no translation
                source_content = getattr(entity, field, "")

            # Build prompt
            prompt = TranslatorService._build_translation_prompt(
                content=source_content,
                source_language=source_language,
                target_language=target_language,
                entity_type=handler.get_entity_type(),
                field=field,
            )

            # Make the async AI call
            generation_started_at = datetime.now(timezone.utc)
            translated_text = await self.generate_content(
                prompt=prompt, message_history=[]
            )

            if not translated_text:
                raise ValueError("Empty translation response from AI")

            # Create or update the translation record
            translation = await handler.create_translation(
                entity=entity,
                field=field,
                language=target_language,
                content=translated_text,
                generation_started_at=generation_started_at,
                model_id=self.agent.model.id,
            )

            return translation is not None

        except Exception as e:
            current_app.logger.error(
                f"Error translating {handler.get_entity_type()}.{field}: {e}"
            )
            return False

    @staticmethod
    def _build_translation_prompt(
        content: str,
        source_language: str,
        target_language: str,
        entity_type: str,
        field: str,
    ) -> str:
        """
        Build the prompt for the translation agent using either the 'translate_metadata' or 'translate_content' template.
        """
        # Determine which template name to use
        if field in ["title", "name", "alt_text"]:
            template = TRANSLATE_METADATA_PROMPT
        else:
            template = TRANSLATE_CONTENT_PROMPT

        # Render the final prompt
        prompt = template.format(
            content=content,
            source_language=source_language,
            target_language=target_language,
            entity_type=entity_type,
            field=field,
        )
        return prompt


# noinspection PyTypeChecker
def register_translation_handlers() -> None:
    """
    Register your translation handlers for different entity types.
    """
    from services.handlers import (
        ArticleTranslationHandler,
        CategoryTranslationHandler,
        MediaTranslationHandler,
        SocialMediaPostTranslationHandler,
        TaxonomyTranslationHandler,
        TagTranslationHandler,
    )

    TranslatorService.register_handler("taxonomies", TaxonomyTranslationHandler)
    TranslatorService.register_handler("categories", CategoryTranslationHandler)
    TranslatorService.register_handler("tags", TagTranslationHandler)
    TranslatorService.register_handler("articles", ArticleTranslationHandler)
    TranslatorService.register_handler("media", MediaTranslationHandler)
    TranslatorService.register_handler(
        "social_media_posts", SocialMediaPostTranslationHandler
    )
