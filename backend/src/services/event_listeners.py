import asyncio
from functools import wraps
from typing import Any, Set, Optional

from flask import current_app
from sqlalchemy import event
from sqlalchemy.orm import AttributeState

from content.models import (
    Article,
    Category,
    ContentStatus,
    SocialMediaPost,
    Tag,
    Taxonomy,
)
from translations.models import ApprovedLanguage
from services.translator_service import TranslatorService


def async_handler(f):
    """Decorator to run async handlers in event loop"""

    @wraps(f)
    def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(f(*args, **kwargs))

    return wrapper


# noinspection PyProtectedMember,PyUnresolvedReferences
def get_changed_translatable_fields(target: Any, handler) -> Set[str]:
    """
    Get list of translatable fields that have changed.
    """
    if not hasattr(target, "_sa_instance_state"):
        return set()

    state: AttributeState = target._sa_instance_state
    if not state.committed_state:
        return set()  # New instance, all fields need translation

    changed_fields = set()
    translatable_fields = set(handler.get_translatable_fields())

    for field in state.committed_state:
        if field in translatable_fields:
            old_value = state.committed_state[field]
            new_value = getattr(target, field)
            if old_value != new_value:
                changed_fields.add(field)

    return changed_fields


async def handle_translation(
    target: Any, service: TranslatorService, fields: Optional[Set[str]] = None
) -> None:
    """
    Handle translation for an entity.
    """
    try:
        # Get active languages except default
        default_lang = ApprovedLanguage.get_default_language()
        if not default_lang:
            current_app.logger.error("No default language configured")
            return

        languages = [
            lang.code
            for lang in ApprovedLanguage.get_active_languages()
            if lang.code != default_lang.code
        ]

        # Translate to each active language
        for language in languages:
            try:
                await service.translate_entity(
                    entity=target,
                    target_language=language,
                    fields=list(fields) if fields else None,
                )
            except Exception as e:
                current_app.logger.error(f"Error translating to {language}: {str(e)}")

    except Exception as e:
        current_app.logger.error(f"Translation handling error: {str(e)}")


# Article events
# noinspection PyProtectedMember,PyUnresolvedReferences
@event.listens_for(Article, "after_update")
@async_handler
async def article_translation_trigger(_1, _2, target):
    """Trigger translation when article is approved or content changes"""
    if not isinstance(target, Article):
        return

    service = TranslatorService()
    handler = service.initialized_handlers.get("articles")
    if not handler:
        return

    # Check if status changed to APPROVED
    state: AttributeState = target._sa_instance_state
    old_status = state.committed_state.get("status")

    if old_status != ContentStatus.APPROVED and target.status == ContentStatus.APPROVED:
        # Article just approved, translate all fields
        await handle_translation(target, service)
    elif target.status == ContentStatus.APPROVED:
        # Already approved, check for content changes
        changed_fields = get_changed_translatable_fields(target, handler)
        if changed_fields:
            await handle_translation(target, service, changed_fields)


# Tag events
# noinspection PyProtectedMember,PyUnresolvedReferences
@event.listens_for(Tag, "after_update")
@async_handler
async def tag_translation_trigger(_1, _2, target):
    """Trigger translation when tag is approved or name changes"""
    if not isinstance(target, Tag):
        return

    service = TranslatorService()
    handler = service.initialized_handlers.get("tags")
    if not handler:
        return

    # Check if status changed to APPROVED
    state: AttributeState = target._sa_instance_state
    old_status = state.committed_state.get("status")

    if old_status != ContentStatus.APPROVED and target.status == ContentStatus.APPROVED:
        # Tag just approved, translate name
        await handle_translation(target, service)
    elif target.status == ContentStatus.APPROVED:
        # Already approved, check for name change
        changed_fields = get_changed_translatable_fields(target, handler)
        if changed_fields:
            await handle_translation(target, service, changed_fields)


# Taxonomy and Category events (no status field)
@event.listens_for(Taxonomy, "after_insert")
@event.listens_for(Taxonomy, "after_update")
@async_handler
async def taxonomy_translation_trigger(_1, _2, target):
    """Trigger translation for taxonomy changes"""
    if not isinstance(target, Taxonomy):
        return

    service = TranslatorService()
    handler = service.initialized_handlers.get("taxonomies")
    if not handler:
        return

    # For updates, check which fields changed
    if hasattr(target, "_sa_instance_state"):
        changed_fields = get_changed_translatable_fields(target, handler)
        if changed_fields:
            await handle_translation(target, service, changed_fields)
    else:
        # New taxonomy, translate all fields
        await handle_translation(target, service)


@event.listens_for(Category, "after_insert")
@event.listens_for(Category, "after_update")
@async_handler
async def category_translation_trigger(_1, _2, target):
    """Trigger translation for category changes"""
    if not isinstance(target, Category):
        return

    service = TranslatorService()
    handler = service.initialized_handlers.get("categories")
    if not handler:
        return

    # For updates, check which fields changed
    if hasattr(target, "_sa_instance_state"):
        changed_fields = get_changed_translatable_fields(target, handler)
        if changed_fields:
            await handle_translation(target, service, changed_fields)
    else:
        # New category, translate all fields
        await handle_translation(target, service)


# SocialMediaPost events
# noinspection PyProtectedMember,PyUnresolvedReferences
@event.listens_for(SocialMediaPost, "after_update")
@async_handler
async def social_media_post_translation_trigger(_1, _2, target):
    """Trigger translation when post is approved or content changes"""
    if not isinstance(target, SocialMediaPost):
        return

    service = TranslatorService()
    handler = service.initialized_handlers.get("social_media_posts")
    if not handler:
        return

    # Check if status changed to APPROVED
    state: AttributeState = target._sa_instance_state
    old_status = state.committed_state.get("status")

    if old_status != ContentStatus.APPROVED and target.status == ContentStatus.APPROVED:
        # Post just approved, translate all fields
        await handle_translation(target, service)
    elif target.status == ContentStatus.APPROVED and not target.posted_at:
        # Already approved but not posted, check for content changes
        changed_fields = get_changed_translatable_fields(target, handler)
        if changed_fields:
            await handle_translation(target, service, changed_fields)
