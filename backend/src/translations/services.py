from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Type

from flask import current_app
from sqlalchemy import inspect

from agents.clients import AnthropicClient
from agents.models import Agent, AgentType, Provider
from extensions import db
from translations.models import Translation, ApprovedLanguage


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
        generation_started_at: Optional[datetime] = None,
        tokens_used: Optional[int] = None,
        model_id: Optional[int] = None,
    ) -> Optional[Translation]:
        """
        Create or update a translation record.

        Args:
            entity: The entity being translated
            field: Field name being translated
            language: Target language code
            content: Translated content
            generation_started_at: Optional timestamp when generation started
            tokens_used: Optional number of tokens used for generation
            model_id: Optional ID of the AI model used for generation

        Returns:
            Created/updated Translation object or None if failed
        """
        try:
            # Get entity ID using inspect
            instance_state = inspect(entity)
            try:
                mapper = instance_state.mapper
                pk = mapper.primary_key[0]
                entity_id = getattr(entity, pk.name)
            except (AttributeError, IndexError):
                raise ValueError("Could not determine entity primary key")

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
                translation.generation_started_at = generation_started_at
                translation.tokens_used = translation.tokens_used + tokens_used
                translation.model_id = model_id
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
                    generation_started_at=generation_started_at,
                    tokens_used=tokens_used,
                    model_id=model_id,
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


# noinspection PyProtectedMember
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

        # Initialize the appropriate client
        if self.agent.model.provider == Provider.ANTHROPIC:
            self.client = AnthropicClient(
                model=self.agent.model.model_id,
                temperature=self.agent.temperature,
                max_tokens=self.agent.max_tokens,
            )
        elif self.agent.model.provider == Provider.OPENAI:
            self.client = AnthropicClient(
                model=self.agent.model.model_id,
                temperature=self.agent.temperature,
                max_tokens=self.agent.max_tokens,
            )
        else:
            raise ValueError(f"Unsupported provider: {self.agent.model.provider}")

        self.client._init_client()

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

            # Generate translation using client
            prompt = self._build_translation_prompt(
                content=source_content,
                source_language=source_language,
                target_language=target_language,
                entity_type=handler.get_entity_type(),
                field=field,
            )

            generation_started_at = datetime.now(timezone.utc)
            response = self.client._generate_content(prompt)
            if not response:
                raise ValueError("Empty response from API")

            translated_content = self.client._extract_content(response)

            # Track usage
            total_tokens = self.client._track_usage(response)

            # Create translation record
            translation = await handler.create_translation(
                entity=entity,
                field=field,
                language=target_language,
                content=translated_content,
                generation_started_at=generation_started_at,
                tokens_used=total_tokens,
                model_id=self.agent.model_id,
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

        prompt = template.render(
            content=content,
            source_language=source_language,
            target_language=target_language,
            entity_type=entity_type,
            field=field,
        )
        print(prompt)

        return template.render(
            content=content,
            source_language=source_language,
            target_language=target_language,
            entity_type=entity_type,
            field=field,
        )


def register_translation_handlers() -> None:
    """Register all translation handlers with the service"""
    from translations.handlers import (
        ArticleTranslationHandler,
        CategoryTranslationHandler,
        MediaTranslationHandler,
        SocialMediaPostTranslationHandler,
        TaxonomyTranslationHandler,
        TagTranslationHandler,
    )

    # Register handlers
    TranslationService.register_handler("taxonomies", TaxonomyTranslationHandler)
    TranslationService.register_handler("categories", CategoryTranslationHandler)
    TranslationService.register_handler("tags", TagTranslationHandler)
    TranslationService.register_handler("articles", ArticleTranslationHandler)
    TranslationService.register_handler("media", MediaTranslationHandler)
    TranslationService.register_handler(
        "social_media_posts", SocialMediaPostTranslationHandler
    )
