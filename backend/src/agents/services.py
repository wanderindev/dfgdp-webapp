from typing import List, Dict

from flask import current_app

from agents.models import Agent, AgentType
from .models import db, Provider
from translations.models import Translation, ApprovedLanguage


# noinspection PyArgumentList
class TranslationService:
    """Service for handling content translations"""

    def __init__(self):
        self.agent = Agent.query.filter_by(
            type=AgentType.TRANSLATOR, is_active=True
        ).first()

        if not self.agent:
            raise ValueError("No active translator agent found")

    async def translate_content(
        self,
        entity_type: str,
        entity_id: int,
        fields: List[str],
        target_language: str,
        special_instructions: str = "",
    ) -> Dict[str, bool]:
        """
        Translate specified fields of an entity to target language.

        Args:
            entity_type: Type of entity (article, tag, etc.)
            entity_id: ID of the entity
            fields: List of fields to translate
            target_language: Target language code
            special_instructions: Any special translation instructions

        Returns:
            Dictionary of field names and success status
        """
        try:
            # Validate target language
            if not ApprovedLanguage.query.filter_by(
                code=target_language, is_active=True
            ).first():
                raise ValueError(
                    f"Language {target_language} not approved for translation"
                )

            results = {}

            # Get source language (default language)
            source_lang = ApprovedLanguage.get_default_language()
            if not source_lang:
                raise ValueError("No default language configured")

            for field in fields:
                # Get original content
                original = Translation.query.filter_by(
                    entity_type=entity_type,
                    entity_id=entity_id,
                    field=field,
                    language=source_lang.code,
                ).first()

                if not original and field != "level":  # Handle enum values differently
                    current_app.logger.error(
                        f"No content found for {entity_type}.{field} in {source_lang.code}"
                    )
                    results[field] = False
                    continue

                try:
                    # Choose appropriate template based on field type
                    template_name = (
                        "translate_metadata"
                        if field in ["title", "level", "tags"]
                        else "translate_content"
                    )

                    # Get appropriate content
                    content = original.content if original else field

                    # Generate translation
                    translated_content = await self._generate_translation(
                        content=content,
                        source_language=source_lang.code,
                        target_language=target_language,
                        content_type=entity_type,
                        field_type=field,
                        special_instructions=special_instructions,
                        template_name=template_name,
                    )

                    # Store translation
                    translation = Translation(
                        entity_type=entity_type,
                        entity_id=entity_id,
                        field=field,
                        language=target_language,
                        content=translated_content,
                        is_generated=True,
                        generated_by_id=self.agent.model_id,
                    )
                    db.session.add(translation)
                    results[field] = True

                except Exception as e:
                    current_app.logger.error(
                        f"Error translating {entity_type}.{field}: {str(e)}"
                    )
                    results[field] = False

            db.session.commit()
            return results

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Translation error: {str(e)}")
            raise

    async def _generate_translation(
        self,
        content: str,
        source_language: str,
        target_language: str,
        content_type: str,
        field_type: str,
        special_instructions: str,
        template_name: str,
    ) -> str:
        """Generate translation using the AI agent."""
        # Validate agent configuration
        is_valid, error = self.agent.validate_config()
        if not is_valid:
            raise ValueError(f"Invalid agent configuration: {error}")

        # Render prompt template
        prompt = self.agent.render_template(
            template_name,
            source_language=source_language,
            target_language=target_language,
            content_type=content_type,
            field_type=field_type,
            special_instructions=special_instructions,
            content=content,
        )

        if not prompt:
            raise ValueError("Failed to render translation prompt")

        # Use appropriate client based on agent model
        client = self._get_client()

        # Generate translation
        response = await client.generate(prompt)

        return response.strip()

    def _get_client(self):
        """Get appropriate API client based on agent model."""
        if self.agent.model.provider == Provider.ANTHROPIC:
            from agents.clients.base import AnthropicClient

            return AnthropicClient()
        elif self.agent.model.provider == Provider.OPENAI:
            from agents.clients.base import OpenAIClient

            return OpenAIClient()
        else:
            raise ValueError(f"Unsupported provider: {self.agent.model.provider}")
