import json
from datetime import datetime, timezone

import pytest
from sqlalchemy.exc import IntegrityError

from agents.models import AIModel, Provider
from content.models import (
    Article,
    Tag,
    Category,
    Taxonomy,
    ArticleLevel,
    ContentStatus,
    SocialMediaPost,
    Media,
    MediaType,
    MediaSource,
)
from translations.models import ApprovedLanguage, Translation


# noinspection PyArgumentList
def test_approved_language_creation(db_session):
    """Test creating approved languages."""
    english = ApprovedLanguage(
        code="en", name="English", is_active=True, is_default=True
    )
    spanish = ApprovedLanguage(
        code="es", name="Spanish", is_active=True, is_default=False
    )
    db_session.add_all([english, spanish])
    db_session.commit()

    assert english.id is not None
    assert spanish.id is not None
    assert english.is_default
    assert not spanish.is_default


# noinspection PyArgumentList
def test_approved_language_methods(db_session):
    """Test ApprovedLanguage class methods."""
    # Create languages
    english = ApprovedLanguage(
        code="en", name="English", is_active=True, is_default=True
    )
    spanish = ApprovedLanguage(code="es", name="Spanish", is_active=True)
    inactive = ApprovedLanguage(code="fr", name="French", is_active=False)
    db_session.add_all([english, spanish, inactive])
    db_session.commit()

    # Test get_active_languages
    active = ApprovedLanguage.get_active_languages()
    assert len(active) == 2
    assert all(lang.is_active for lang in active)

    # Test get_default_language
    default = ApprovedLanguage.get_default_language()
    assert default.code == "en"
    assert default.is_default


# noinspection PyArgumentList
def test_translation_creation(db_session):
    """Test creating translations."""
    # Create required language
    english = ApprovedLanguage(
        code="en", name="English", is_active=True, is_default=True
    )
    db_session.add(english)

    # Create AI model for tracking
    model = AIModel(
        name="Test Model", provider=Provider.ANTHROPIC, model_id="test-model"
    )
    db_session.add(model)
    db_session.commit()

    translation = Translation(
        entity_type="article",
        entity_id=1,
        field="title",
        language="en",
        content="Test Title",
        is_generated=True,
        generated_by_id=model.id,
        generated_at=datetime.now(timezone.utc),
    )
    db_session.add(translation)
    db_session.commit()

    assert translation.id is not None
    assert translation.is_generated
    assert translation.generated_by_id == model.id


# noinspection PyArgumentList
def test_approved_language_default_constraint(db_session):
    """Ensure default language must be active."""
    language = ApprovedLanguage(
        code="de", name="German", is_active=False, is_default=True
    )
    db_session.add(language)
    with pytest.raises(Exception):  # Adjust exception type based on DB error
        db_session.commit()


# noinspection PyArgumentList
def test_translation_unique_constraint(db_session):
    """Ensure Translation uniqueness is enforced."""
    # Create necessary language and translation
    language = ApprovedLanguage(code="en", name="English", is_active=True)
    db_session.add(language)
    db_session.commit()

    translation = Translation(
        entity_type="article",
        entity_id=1,
        field="title",
        language="en",
        content="Test Title",
    )
    duplicate = Translation(
        entity_type="article",
        entity_id=1,
        field="title",
        language="en",
        content="Duplicate Title",
    )
    db_session.add_all([translation, duplicate])
    with pytest.raises(IntegrityError):
        db_session.commit()


# noinspection PyArgumentList
def test_translation_cascade_delete(db_session):
    """Test cascading delete for translations when language is removed."""
    language = ApprovedLanguage(code="es", name="Spanish", is_active=True)
    db_session.add(language)
    db_session.commit()

    translation = Translation(
        entity_type="article",
        entity_id=1,
        field="title",
        language="es",
        content="Título de prueba",
    )
    db_session.add(translation)
    db_session.commit()

    # Delete language
    db_session.delete(language)
    db_session.commit()

    # Ensure translation is deleted
    assert Translation.query.filter_by(language="es").count() == 0


# noinspection PyArgumentList
def test_translatable_mixin_with_article(db_session, test_category, test_research):
    """Test TranslatableMixin functionality with Article model."""
    # Create languages
    english = ApprovedLanguage(
        code="en", name="English", is_active=True, is_default=True
    )
    spanish = ApprovedLanguage(code="es", name="Spanish", is_active=True)
    db_session.add_all([english, spanish])

    # Create article
    article = Article(
        category=test_category,
        research=test_research,
        title="Original Title",
        content="Original Content",
        excerpt="Original Excerpt",
        level=ArticleLevel.HIGH_SCHOOL,
    )
    db_session.add(article)
    db_session.commit()

    # Create translations directly in the Translation model
    translation_title = Translation(
        entity_type="articles",
        entity_id=article.id,
        field="title",
        language="es",
        content="Título en Español",
    )
    translation_content = Translation(
        entity_type="articles",
        entity_id=article.id,
        field="content",
        language="es",
        content="Contenido en Español",
    )
    translation_excerpt = Translation(
        entity_type="articles",
        entity_id=article.id,
        field="excerpt",
        language="es",
        content="Extracto en Español",
    )
    db_session.add_all([translation_title, translation_content, translation_excerpt])
    db_session.commit()

    # Test retrieving translations
    assert article.get_translation("title", "es") == "Título en Español"
    assert article.get_translation("content", "es") == "Contenido en Español"
    assert article.get_translation("excerpt", "es") == "Extracto en Español"

    # Test fallback to original content
    assert article.get_translation("title", "fr") == "Original Title"

    # Test available translations
    available = article.get_available_translations("title")
    assert "es" in available
    assert len(available) == 1  # Only Spanish, as English is the original


# noinspection PyArgumentList
def test_translatable_mixin_with_taxonomy(db_session):
    """Test TranslatableMixin functionality with Taxonomy model."""
    # Create languages
    english = ApprovedLanguage(
        code="en", name="English", is_active=True, is_default=True
    )
    spanish = ApprovedLanguage(code="es", name="Spanish", is_active=True)
    db_session.add_all([english, spanish])

    # Create taxonomy
    taxonomy = Taxonomy(name="History", description="Historical events")
    db_session.add(taxonomy)
    db_session.commit()

    # Add translations
    translation_name = Translation(
        entity_type="taxonomies",
        entity_id=taxonomy.id,
        field="name",
        language="es",
        content="Historia",
    )
    translation_description = Translation(
        entity_type="taxonomies",
        entity_id=taxonomy.id,
        field="description",
        language="es",
        content="Eventos históricos",
    )
    db_session.add_all([translation_name, translation_description])
    db_session.commit()

    assert taxonomy.get_translation("name", "es") == "Historia"
    assert taxonomy.get_translation("description", "es") == "Eventos históricos"


# noinspection PyArgumentList
def test_translatable_mixin_with_category(db_session, test_taxonomy):
    """Test TranslatableMixin functionality with Category model."""
    # Create languages
    english = ApprovedLanguage(
        code="en", name="English", is_active=True, is_default=True
    )
    spanish = ApprovedLanguage(code="es", name="Spanish", is_active=True)
    db_session.add_all([english, spanish])

    # Create category
    category = Category(
        taxonomy=test_taxonomy,
        name="Ancient Greece",
        description="Ancient Greek history",
    )
    db_session.add(category)
    db_session.commit()

    # Add translations
    translation_name = Translation(
        entity_type="categories",
        entity_id=category.id,
        field="name",
        language="es",
        content="Grecia Antigua",
    )
    translation_description = Translation(
        entity_type="categories",
        entity_id=category.id,
        field="description",
        language="es",
        content="Historia de la Antigua Grecia",
    )
    db_session.add_all([translation_name, translation_description])
    db_session.commit()

    assert category.get_translation("name", "es") == "Grecia Antigua"
    assert (
        category.get_translation("description", "es") == "Historia de la Antigua Grecia"
    )


# noinspection PyArgumentList
def test_translatable_mixin_with_tag(db_session):
    """Test TranslatableMixin functionality with Tag model."""
    # Create languages
    english = ApprovedLanguage(
        code="en", name="English", is_active=True, is_default=True
    )
    spanish = ApprovedLanguage(code="es", name="Spanish", is_active=True)
    db_session.add_all([english, spanish])

    # Create tag
    tag = Tag(name="Philosophy", status=ContentStatus.APPROVED)
    db_session.add(tag)
    db_session.commit()

    # Add translation
    translation_name = Translation(
        entity_type="tags",
        entity_id=tag.id,
        field="name",
        language="es",
        content="Filosofía",
    )
    db_session.add(translation_name)
    db_session.commit()

    assert tag.get_translation("name", "es") == "Filosofía"


# noinspection PyArgumentList
def test_translatable_mixin_with_social_media_post(
    db_session, test_article, test_social_media_account
):
    """Test TranslatableMixin functionality with SocialMediaPost model."""
    # Create languages
    english = ApprovedLanguage(
        code="en", name="English", is_active=True, is_default=True
    )
    spanish = ApprovedLanguage(code="es", name="Spanish", is_active=True)
    db_session.add_all([english, spanish])

    # Create post
    post = SocialMediaPost(
        article=test_article,
        account=test_social_media_account,
        content="Check out our new article!",
        hashtags=["#history", "#education"],
    )
    db_session.add(post)
    db_session.commit()

    # Add translations
    translation_content = Translation(
        entity_type="social_media_posts",
        entity_id=post.id,
        field="content",
        language="es",
        content="¡Mira nuestro nuevo artículo!",
    )
    translation_hashtags = Translation(
        entity_type="social_media_posts",
        entity_id=post.id,
        field="hashtags",
        language="es",
        content=json.dumps(["#historia", "#educacion"]),  # Store hashtags as JSON
    )
    db_session.add_all([translation_content, translation_hashtags])
    db_session.commit()

    assert post.get_translation("content", "es") == "¡Mira nuestro nuevo artículo!"
    assert post.get_translation("hashtags", "es") == ["#historia", "#educacion"]


# noinspection PyArgumentList
def test_translatable_mixin_with_media(db_session):
    """Test TranslatableMixin functionality with Media model."""
    # Create languages
    english = ApprovedLanguage(
        code="en", name="English", is_active=True, is_default=True
    )
    spanish = ApprovedLanguage(code="es", name="Spanish", is_active=True)
    db_session.add_all([english, spanish])

    # Create media
    media = Media(
        filename="image.jpg",
        original_filename="image.jpg",
        file_path="/media/image.jpg",
        file_size=1000000,
        mime_type="image/jpeg",
        media_type=MediaType.IMAGE,
        source=MediaSource.LOCAL,
        title="Original Title",
        alt_text="Original Alt Text",
    )
    db_session.add(media)
    db_session.commit()

    # Add translations
    translation_title = Translation(
        entity_type="media",
        entity_id=media.id,
        field="title",
        language="es",
        content="Título en Español",
    )
    translation_alt_text = Translation(
        entity_type="media",
        entity_id=media.id,
        field="alt_text",
        language="es",
        content="Texto alternativo en Español",
    )
    db_session.add_all([translation_title, translation_alt_text])
    db_session.commit()

    assert media.get_translation("title", "es") == "Título en Español"
    assert media.get_translation("alt_text", "es") == "Texto alternativo en Español"
