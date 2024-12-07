from datetime import datetime, timezone

from agents.models import AIModel, Provider
from content.models import Article, Tag, Category, Taxonomy, ArticleLevel, ContentStatus
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
def test_translatable_mixin_with_article(
    db_session, test_category, test_research
):  # Add test_research fixture
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
        research=test_research,  # Use the fixture instead of research_id=1
        title="Original Title",
        slug="original-title",
        content="Original Content",
        level=ArticleLevel.HIGH_SCHOOL,
    )
    db_session.add(article)
    db_session.commit()

    # Add translations
    article.set_translation("title", "es", "Título en Español")
    article.set_translation("content", "es", "Contenido en Español")
    db_session.commit()

    # Test retrieving translations
    assert article.get_translation("title", "es") == "Título en Español"
    assert article.get_translation("content", "es") == "Contenido en Español"

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
    taxonomy = Taxonomy(name="History", slug="history", description="Historical events")
    db_session.add(taxonomy)
    db_session.commit()

    # Add translations
    taxonomy.set_translation("name", "es", "Historia")
    taxonomy.set_translation("description", "es", "Eventos históricos")
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
        slug="ancient-greece",
        description="Ancient Greek history",
    )
    db_session.add(category)
    db_session.commit()

    # Add translations
    category.set_translation("name", "es", "Grecia Antigua")
    category.set_translation("description", "es", "Historia de la Antigua Grecia")
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
    tag = Tag(name="Philosophy", slug="philosophy", status=ContentStatus.APPROVED)
    db_session.add(tag)
    db_session.commit()

    # Add translation
    tag.set_translation("name", "es", "Filosofía")
    db_session.commit()

    assert tag.get_translation("name", "es") == "Filosofía"


# noinspection PyArgumentList
def test_translatable_mixin_with_social_media_post(
    db_session, test_article, test_social_media_account
):
    """Test TranslatableMixin functionality with SocialMediaPost model."""
    from content.models import SocialMediaPost

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
    post.set_translation("content", "es", "¡Mira nuestro nuevo artículo!")
    post.set_translation("hashtags", "es", ["#historia", "#educacion"])
    db_session.commit()

    assert post.get_translation("content", "es") == "¡Mira nuestro nuevo artículo!"
    assert post.get_translation("hashtags", "es") == ["#historia", "#educacion"]
