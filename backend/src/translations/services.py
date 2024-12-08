import json
from datetime import datetime, timezone
from typing import Any, List, TypeVar, Union, Optional

from sqlalchemy.orm import DeclarativeMeta

from .models import ApprovedLanguage, db, Translation

# Define a type variable for models that can be translated
T = TypeVar("T", bound=DeclarativeMeta)


def get_translation(obj: T, field: str, language: Optional[str] = None) -> Any:
    """Get translation for a field in specified language."""
    if language is None:
        default_lang = ApprovedLanguage.get_default_language()
        language = default_lang.code if default_lang else "en"

    translation = Translation.query.filter_by(
        entity_type=obj.__tablename__,
        entity_id=obj.id,
        field=field,
        language=language,
    ).first()

    if translation:
        try:
            return json.loads(translation.content)
        except json.JSONDecodeError:
            return translation.content

    value = getattr(obj, field)
    if isinstance(value, (list, dict)):
        return value
    return value


# noinspection PyArgumentList
def set_translation(
    obj: T,
    field: str,
    language: str,
    content: Union[str, dict, list],
    is_generated: bool = True,
    model_id: Optional[int] = None,
) -> None:
    """Set translation for a field in specified language."""
    if not isinstance(content, str):
        content = json.dumps(content)

    translation = Translation.query.filter_by(
        entity_type=obj.__tablename__,
        entity_id=obj.id,
        field=field,
        language=language,
    ).first()

    if translation:
        translation.content = content
        if is_generated:
            translation.is_generated = True
            translation.generated_at = datetime.now(timezone.utc)
            translation.generated_by_id = model_id
    else:
        translation = Translation(
            entity_type=obj.__tablename__,
            entity_id=obj.id,
            field=field,
            language=language,
            content=content,
            is_generated=is_generated,
            generated_at=datetime.now(timezone.utc) if is_generated else None,
            generated_by_id=model_id if is_generated else None,
        )
        db.session.add(translation)


def get_available_translations(obj: T, field: str) -> List[str]:
    """Get list of available language codes for a field."""
    translations = Translation.query.filter_by(
        entity_type=obj.__tablename__, entity_id=obj.id, field=field
    ).all()
    return [t.language for t in translations]
