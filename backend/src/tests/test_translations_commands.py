from unittest.mock import AsyncMock, Mock

from click.testing import CliRunner
from flask.cli import ScriptInfo

from content.models import ContentStatus
from translations.commands import (
    check_missing_translations,
    list_languages,
    translate_entity,
    list_translatable_content,
    MissingTranslationChecker,
)
from translations.models import Translation


# noinspection PyTypeChecker
def test_list_languages(app, test_languages):
    """Test listing of configured languages."""
    runner = CliRunner()
    result = runner.invoke(
        list_languages,
        obj=ScriptInfo(create_app=lambda info: app),
    )

    assert result.exit_code == 0
    assert "Configured languages:" in result.output
    assert "en: English [DEFAULT, ACTIVE]" in result.output
    assert "es: Spanish [ACTIVE]" in result.output
    assert "fr: French [INACTIVE]" in result.output


# noinspection PyTypeChecker,DuplicatedCode
def test_check_missing_translations_success(
    app,
    db_session,
    test_article,
    test_languages,
    mock_translation_service,
    mock_event_loop,
):
    """Test checking for missing translations with success scenario."""
    # Set up mock handler correctly
    handler = mock_translation_service.initialized_handlers["articles"]
    handler.get_translatable_fields.return_value = ["title", "content"]
    handler.validate_entity = AsyncMock(return_value=True)
    handler.check_entity = Mock(return_value={"title": {"es"}, "content": {"es"}})

    # Mock the model_registry of the checker
    mock_translation_service.model_registry = {"articles": test_article.__class__}

    # Ensure the article is approved and has some content
    test_article.status = ContentStatus.APPROVED
    test_article.title = "Test Title"
    test_article.content = "Test Content"
    db_session.commit()

    runner = CliRunner()
    result = runner.invoke(
        check_missing_translations,
        ["--model-type", "articles", "--language", "es"],
        obj=ScriptInfo(create_app=lambda info: app),
    )

    assert result.exit_code == 0
    assert "Found missing translations in 1 articles:" in result.output


# noinspection PyTypeChecker,DuplicatedCode
def test_check_missing_translations_with_fix(
    app,
    db_session,
    test_article,
    test_languages,
    mock_translation_service,
    mock_event_loop,
):
    """Test checking and fixing missing translations."""
    # Set up mock handler correctly
    handler = mock_translation_service.initialized_handlers["articles"]
    handler.get_translatable_fields.return_value = ["title", "content"]
    handler.validate_entity = AsyncMock(return_value=True)
    handler.check_entity = Mock(return_value={"title": {"es"}, "content": {"es"}})

    # Mock the model_registry of the checker
    mock_translation_service.model_registry = {"articles": test_article.__class__}

    # Ensure the article is approved
    test_article.status = ContentStatus.APPROVED
    test_article.title = "Test Title"
    test_article.content = "Test Content"
    db_session.commit()

    # Mock successful translation
    # noinspection PyUnusedLocal
    async def mock_translate(*args, **kwargs):
        return {"title": True, "content": True}

    mock_translation_service.translate_entity.side_effect = mock_translate

    runner = CliRunner()
    result = runner.invoke(
        check_missing_translations,
        ["--model-type", "articles", "--language", "es", "--fix"],
        obj=ScriptInfo(create_app=lambda info: app),
    )

    assert result.exit_code == 0
    assert "Found missing translations in 1 articles:" in result.output
    assert "✓ Generated" in result.output


# noinspection PyTypeChecker
def test_check_missing_translations_specific_language(
    app, db_session, test_article, test_languages, mock_translation_service
):
    """Test checking translations for a specific language."""
    # Mock the handler's get_translatable_fields method
    handler = mock_translation_service.initialized_handlers["articles"]
    handler.get_translatable_fields.return_value = ["title", "content"]

    runner = CliRunner()
    result = runner.invoke(
        check_missing_translations,
        ["--model-type", "articles", "--language", "es"],
        obj=ScriptInfo(create_app=lambda info: app),
    )

    assert result.exit_code == 0
    assert "Checking articles..." in result.output
    # Should only show Spanish missing translations
    assert "fr" not in result.output


# noinspection PyTypeChecker
def test_translate_entity_success(
    app,
    db_session,
    test_article,
    test_languages,
    mock_translation_service,
    mock_event_loop,
):
    """Test successful translation of an entity."""

    # Set up mock service response
    # noinspection PyUnusedLocal
    async def mock_translate(*args, **kwargs):
        return {"title": True, "content": True}

    mock_translation_service.translate_entity.side_effect = mock_translate

    runner = CliRunner()
    result = runner.invoke(
        translate_entity,
        ["article", str(test_article.id), "-l", "es"],
        obj=ScriptInfo(create_app=lambda info: app),
    )

    assert result.exit_code == 0
    assert "Translation results for article" in result.output
    assert "✓ title" in result.output
    assert "✓ content" in result.output


# noinspection PyTypeChecker
def test_translate_entity_invalid_language(
    app, db_session, test_article, test_languages
):
    """Test translation with invalid language code."""
    runner = CliRunner()
    result = runner.invoke(
        translate_entity,
        ["article", str(test_article.id), "-l", "invalid"],
        obj=ScriptInfo(create_app=lambda info: app),
    )

    assert result.exit_code == 0
    assert "Error: Language invalid not approved" in result.output


# noinspection PyTypeChecker
def test_translate_entity_invalid_entity(
    app, db_session, test_languages, mock_translation_service
):
    """Test translation with invalid entity ID."""
    runner = CliRunner()
    result = runner.invoke(
        translate_entity,
        ["article", "999999", "-l", "es"],
        obj=ScriptInfo(create_app=lambda info: app),
    )

    assert result.exit_code == 0
    assert "Error: article 999999 not found" in result.output


# noinspection PyTypeChecker
def test_translate_entity_specific_fields(
    app,
    db_session,
    test_article,
    test_languages,
    mock_translation_service,
    mock_event_loop,
):
    """Test translating specific fields of an entity."""
    # Set up mock handler correctly
    handler = mock_translation_service.initialized_handlers["articles"]
    handler.get_translatable_fields.return_value = ["title", "content"]
    handler.validate_entity = AsyncMock(return_value=True)

    # Set up mock service response
    # noinspection PyUnusedLocal
    async def mock_translate(*args, **kwargs):
        return {"title": True}

    mock_translation_service.translate_entity.side_effect = mock_translate

    # Ensure we have content to translate
    test_article.title = "Test Title"
    test_article.content = "Test Content"
    db_session.commit()

    runner = CliRunner()
    result = runner.invoke(
        translate_entity,
        ["article", str(test_article.id), "-l", "es", "-f", "title"],
        obj=ScriptInfo(create_app=lambda info: app),
    )

    assert result.exit_code == 0
    assert "Translation results for article" in result.output
    assert "✓ title" in result.output

    # Verify service was called with correct parameters
    mock_translation_service.translate_entity.assert_awaited_once_with(
        entity=test_article, target_language="es", fields=["title"]
    )


# noinspection PyTypeChecker,PyArgumentList
def test_list_translatable_content_success(
    app, db_session, test_article, test_languages, test_agent, mock_translation_service
):
    """Test listing translatable content for an entity."""
    # Set up article content
    test_article.title = "Original Title"
    test_article.content = "Original Content"
    db_session.commit()

    # Create a test translation
    translation = Translation(
        entity_type="articles",
        entity_id=test_article.id,
        field="title",
        language="es",
        content="Título de prueba",
        is_generated=True,
        generated_by_id=test_agent.model_id,
    )
    db_session.add(translation)
    db_session.commit()

    # Set up mock handler
    handler = mock_translation_service.initialized_handlers["articles"]
    handler.get_translatable_fields.return_value = ["title", "content"]

    runner = CliRunner()
    result = runner.invoke(
        list_translatable_content,
        ["article", str(test_article.id)],
        obj=ScriptInfo(create_app=lambda info: app),
    )

    assert result.exit_code == 0
    assert "Translatable content for article" in result.output
    assert "Original Title" in result.output
    assert "✓ Spanish (es)" in result.output


# noinspection PyTypeChecker
def test_list_translatable_content_invalid_entity(app, db_session, test_languages):
    """Test listing translatable content for invalid entity."""
    runner = CliRunner()
    result = runner.invoke(
        list_translatable_content,
        ["article", "999999"],
        obj=ScriptInfo(create_app=lambda info: app),
    )

    assert result.exit_code == 0
    assert "Error: article 999999 not found" in result.output


def test_missing_translation_checker(
    app, db_session, test_article, test_languages, mock_translation_service
):
    """Test MissingTranslationChecker functionality."""
    handler = mock_translation_service.initialized_handlers["articles"]
    handler.get_translatable_fields.return_value = ["title", "content"]

    checker = MissingTranslationChecker(mock_translation_service)
    missing = checker.check_entity(test_article, languages=["es"])

    assert "title" in missing
    assert "content" in missing
    assert "es" in missing["title"]
    assert "es" in missing["content"]


# noinspection PyTypeChecker
def test_translation_service_error_handling(
    app,
    db_session,
    test_article,
    test_languages,
    mock_translation_service,
    mock_event_loop,
):
    """Test error handling in translation service."""

    # Set up mock service to raise an error
    # noinspection PyUnusedLocal
    async def mock_translate(*args, **kwargs):
        raise Exception("Translation API error")

    mock_translation_service.translate_entity.side_effect = mock_translate

    runner = CliRunner()
    result = runner.invoke(
        translate_entity,
        ["article", str(test_article.id), "-l", "es"],
        obj=ScriptInfo(create_app=lambda info: app),
    )

    assert result.exit_code == 0
    assert "Error during translation: Translation API error" in result.output


# noinspection PyTypeChecker
def test_check_missing_translations_no_entities(
    app, db_session, test_languages, mock_translation_service
):
    """Test checking translations when no entities exist."""
    runner = CliRunner()
    result = runner.invoke(
        check_missing_translations,
        ["--model-type", "articles"],
        obj=ScriptInfo(create_app=lambda info: app),
    )

    assert result.exit_code == 0
    assert "No missing translations for articles" in result.output
