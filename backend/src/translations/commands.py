import asyncio
from contextlib import contextmanager
from typing import Any, Dict, List, Optional, Set, Tuple

import click
from flask import current_app
from flask.cli import AppGroup
from sqlalchemy import inspect

from content.models import (
    Article,
    Category,
    ContentStatus,
    Media,
    SocialMediaPost,
    Tag,
    Taxonomy,
)
from extensions import db
from translations.models import ApprovedLanguage, Translation
from translations.services import TranslationService

# Create CLI group
translations_cli = AppGroup("translations")


# noinspection PyProtectedMember
class MissingTranslationChecker:
    """Utility class for checking missing translations"""

    def __init__(self, service: TranslationService) -> None:
        self.service = service
        self.model_registry = {
            "articles": Article,
            "taxonomies": Taxonomy,
            "categories": Category,
            "tags": Tag,
            "media": Media,
            "social_media_posts": SocialMediaPost,
        }

    def check_entity(
        self, entity: Any, languages: Optional[List[str]] = None
    ) -> Dict[str, Set[str]]:
        """
        Check missing translations for a single entity.

        Args:
            entity: Entity to check
            languages: Optional list of language codes to check.
                      If None, checks all active languages.

        Returns:
            Dict mapping field names to set of missing language codes
        """
        handler = self.service.initialized_handlers.get(entity.__tablename__)
        if not handler:
            return {}

        # Get languages to check
        if not languages:
            default_lang = ApprovedLanguage.get_default_language()
            if not default_lang:
                return {}

            languages = [
                lang.code
                for lang in ApprovedLanguage.get_active_languages()
                if lang.code != default_lang.code
            ]

        # Get translatable fields
        fields = handler.get_translatable_fields()

        # Check each field
        missing: Dict[str, Set[str]] = {}

        # Get entity ID using inspect
        instance_state = inspect(entity)
        try:
            mapper = instance_state.mapper
            pk = mapper.primary_key[0]
            entity_id = getattr(entity, pk.name)
        except (AttributeError, IndexError):
            return {}

        for field in fields:
            missing_langs = set()

            for lang in languages:
                # Check if translation exists
                translation = Translation.query.filter_by(
                    entity_type=entity.__tablename__,
                    entity_id=entity_id,
                    field=field,
                    language=lang,
                ).first()

                if not translation:
                    missing_langs.add(lang)

            if missing_langs:
                missing[field] = missing_langs

        return missing

    def check_model_type(
        self,
        model_type: str,
        languages: Optional[List[str]] = None,
        report_progress: bool = False,
    ) -> List[Tuple[Any, Dict[str, Set[str]]]]:
        """
        Check missing translations for all entities of a model type.

        Args:
            model_type: Name of model to check
            languages: Optional list of language codes to check
            report_progress: Whether to report progress (for CLI use)

        Returns:
            List of tuples (entity, missing_translations)
        """
        handler = self.service.initialized_handlers.get(model_type)
        if not handler:
            return []

        # Get model class from registry
        model = self.model_registry.get(model_type)
        if not model:
            current_app.logger.error(f"Unknown model type: {model_type}")
            return []

        # Build query
        query = model.query

        # Add status filter if applicable
        if hasattr(model, "status"):
            query = query.filter_by(status=ContentStatus.APPROVED)

        # Get all entities
        entities = query.all()
        results = []

        for i, entity in enumerate(entities):
            if report_progress:
                click.echo(f"Checking {model_type} {i+1}/{len(entities)}...")

            missing = self.check_entity(entity, languages)
            if missing:
                results.append((entity, missing))

        return results


@contextmanager
def get_event_loop():
    """Context manager for handling event loop lifecycle"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    try:
        yield loop
    finally:
        loop.close()


@translations_cli.command("check-missing")
@click.option(
    "--model-type", help="Specific model type to check (e.g., articles, taxonomies)"
)
@click.option("--language", help="Specific language code to check")
@click.option("--fix", is_flag=True, help="Automatically generate missing translations")
def check_missing_translations(
    model_type: Optional[str] = None, language: Optional[str] = None, fix: bool = False
) -> None:
    """Check for missing translations and optionally fix them."""
    try:
        service = TranslationService()
        checker = MissingTranslationChecker(service)

        with get_event_loop() as loop:
            # Get or create event loop
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            # Determine which model types to check
            model_types = (
                [model_type]
                if model_type
                else list(service.initialized_handlers.keys())
            )

            # Determine which languages to check
            languages = None
            if language:
                if not ApprovedLanguage.query.filter_by(
                    code=language, is_active=True
                ).first():
                    click.echo(f"Error: Language {language} not approved")
                    return
                languages = [language]

            total_missing = 0

            for mt in model_types:
                click.echo(f"\nChecking {mt}...")
                results = checker.check_model_type(
                    mt, languages=languages, report_progress=True
                )

                if not results:
                    click.echo(f"No missing translations for {mt}")
                    continue

                # Report findings
                click.echo(f"\nFound missing translations in {len(results)} {mt}:")
                for entity, missing in results:
                    # Get entity ID using inspect
                    instance_state = inspect(entity)
                    try:
                        mapper = instance_state.mapper
                        pk = mapper.primary_key[0]
                        entity_id = getattr(entity, pk.name)
                    except (AttributeError, IndexError):
                        click.echo(f"\n  {mt} Unknown ID:")
                        continue

                    click.echo(f"\n  {mt} {entity_id}:")
                    for field, langs in missing.items():
                        langs_str = ", ".join(sorted(langs))
                        click.echo(f"    - {field}: {langs_str}")
                        total_missing += len(langs)

                    # Fix if requested
                    if fix:
                        click.echo(f"  Generating missing translations...")
                        for field, langs in missing.items():
                            for lang in langs:
                                try:
                                    # Run async operation in the event loop
                                    loop.run_until_complete(
                                        service.translate_entity(
                                            entity=entity,
                                            target_language=lang,
                                            fields=[field],
                                        )
                                    )
                                    click.echo(
                                        f"    ✓ Generated {field} translation for {lang}"
                                    )
                                except Exception as e:
                                    click.echo(
                                        f"    ✗ Error generating {field} translation "
                                        f"for {lang}: {str(e)}"
                                    )

            # Summary
            click.echo(f"\nTotal missing translations found: {total_missing}")
            if fix:
                click.echo("Translation generation complete")

    except Exception as e:
        click.echo(f"Error checking translations: {str(e)}")
    finally:
        # Clean up the event loop
        if "loop" in locals():
            loop.close()


@translations_cli.command("list-languages")
def list_languages() -> None:
    """List all approved languages and their status."""
    langs = ApprovedLanguage.query.order_by(
        ApprovedLanguage.is_default.desc(), ApprovedLanguage.code
    ).all()

    if not langs:
        click.echo("No languages configured")
        return

    click.echo("\nConfigured languages:")
    for lang in langs:
        status = []
        if lang.is_default:
            status.append("DEFAULT")
        if lang.is_active:
            status.append("ACTIVE")
        else:
            status.append("INACTIVE")

        status_str = ", ".join(status)
        click.echo(f"  {lang.code}: {lang.name} [{status_str}]")


def get_entity_by_type(entity_type: str, entity_id: int) -> Optional[db.Model]:
    """Get entity instance based on type and ID"""
    entity_types = {
        "article": Article,
        "taxonomy": Taxonomy,
        "category": Category,
        "tag": Tag,
        "media": Media,
        "social_media_post": SocialMediaPost,
    }

    model = entity_types.get(entity_type.lower())
    if not model:
        raise ValueError(f"Unknown entity type: {entity_type}")

    return model.query.get(entity_id)


@translations_cli.command("translate")
@click.argument("entity_type")
@click.argument("entity_id", type=int)
@click.option(
    "--language",
    "-l",
    required=True,
    help="Target language code (e.g., es for Spanish)",
)
@click.option(
    "--fields",
    "-f",
    multiple=True,
    help="Specific fields to translate (translates all if not specified)",
)
def translate_entity(
    entity_type: str, entity_id: int, language: str, fields: Optional[List[str]] = None
) -> None:
    """
    Translate specific entity content to target language.

    Examples:
        flask translations translate article 1 -l es
        flask translations translate taxonomy 2 -l es -f name -f description
        flask translations translate category 3 -l es --fields name --fields description
    """
    try:
        # Validate language
        if not ApprovedLanguage.query.filter_by(code=language, is_active=True).first():
            click.echo(f"Error: Language {language} not approved")
            return

        # Get entity
        try:
            entity = get_entity_by_type(entity_type, entity_id)
            if not entity:
                click.echo(f"Error: {entity_type} {entity_id} not found")
                return
        except ValueError as e:
            click.echo(f"Error: {str(e)}")
            return

        # Initialize service
        service = TranslationService()

        # Get handler for validation
        handler = service.initialized_handlers.get(entity.__tablename__)
        if not handler:
            click.echo(f"Error: No translation handler for {entity_type}")
            return

        # Validate fields if specified
        if fields:
            translatable_fields = set(handler.get_translatable_fields())
            invalid_fields = set(fields) - translatable_fields
            if invalid_fields:
                click.echo(
                    f"Error: Invalid fields for {entity_type}: {', '.join(invalid_fields)}"
                )
                click.echo(f"Available fields: {', '.join(translatable_fields)}")
                return

        # Run translation
        with get_event_loop() as loop:
            results = loop.run_until_complete(
                service.translate_entity(
                    entity=entity,
                    target_language=language,
                    fields=list(fields) if fields else None,
                )
            )

        # Report results
        click.echo(f"\nTranslation results for {entity_type} {entity_id}:")
        for field, success in results.items():
            status = "✓" if success else "✗"
            click.echo(f"{status} {field}")

        if all(results.values()):
            click.echo("\nAll translations completed successfully!")
        else:
            click.echo("\nSome translations failed. Check logs for details.")

    except Exception as e:
        click.echo(f"Error during translation: {str(e)}")


@translations_cli.command("list-translatable")
@click.argument("entity_type")
@click.argument("entity_id", type=int)
def list_translatable_content(entity_type: str, entity_id: int) -> None:
    """
    List translatable fields and their current translations for an entity.

    Examples:
        flask translations list-translatable article 1
        flask translations list-translatable taxonomy 2
    """
    try:
        # Get entity
        try:
            entity = get_entity_by_type(entity_type, entity_id)
            if not entity:
                click.echo(f"Error: {entity_type} {entity_id} not found")
                return
        except ValueError as e:
            click.echo(f"Error: {str(e)}")
            return

        # Initialize service
        service = TranslationService()

        # Get handler
        handler = service.initialized_handlers.get(entity.__tablename__)
        if not handler:
            click.echo(f"Error: No translation handler for {entity_type}")
            return

        # Get translatable fields
        fields = handler.get_translatable_fields()

        # Get available languages
        languages = ApprovedLanguage.get_active_languages()

        click.echo(f"\nTranslatable content for {entity_type} {entity_id}:")
        for field in fields:
            click.echo(f"\nField: {field}")
            original_value = getattr(entity, field)
            if isinstance(original_value, (list, dict)):
                original_value = str(original_value)
            click.echo(f"Original: {original_value[:100]}...")

            click.echo("Translations:")
            for lang in languages:
                if lang.is_default:
                    continue

                translation = entity.get_translation(field, lang.code)
                status = "✓" if translation else "✗"
                click.echo(f"  {status} {lang.name} ({lang.code})")
                if translation:
                    if isinstance(translation, (list, dict)):
                        translation = str(translation)
                    click.echo(f"    {translation[:100]}...")

    except Exception as e:
        click.echo(f"Error: {str(e)}")
