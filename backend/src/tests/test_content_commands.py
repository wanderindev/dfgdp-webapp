from unittest.mock import AsyncMock, patch

import pytest
from click.testing import CliRunner
from flask.cli import ScriptInfo

from content.commands import (
    generate_suggestions,
    generate_research,
    generate_article,
    generate_story,
    generate_did_you_know,
    generate_media_suggestions,
    fetch_media_candidates,
)
from content.models import (
    ArticleSuggestion,
    Research,
    Article,
    SocialMediaPost,
    MediaSuggestion,
    MediaCandidate,
    ArticleLevel,
    ContentStatus,
)


@pytest.fixture
def mock_content_manager_service():
    with patch("content.commands.ContentManagerService") as mock:
        # Mock the async generate_suggestions method
        service_instance = mock.return_value
        service_instance.generate_suggestions = AsyncMock()
        yield service_instance


@pytest.fixture
def mock_researcher_service():
    with patch("content.commands.ResearcherService") as mock:
        service_instance = mock.return_value
        service_instance.generate_research = AsyncMock()
        yield service_instance


@pytest.fixture
def mock_writer_service():
    with patch("content.commands.WriterService") as mock:
        service_instance = mock.return_value
        service_instance.generate_article = AsyncMock()
        yield service_instance


@pytest.fixture
def mock_social_media_service():
    with patch("content.commands.SocialMediaManagerService") as mock:
        service_instance = mock.return_value
        service_instance.generate_story_promotion = AsyncMock()
        service_instance.generate_did_you_know_posts = AsyncMock()
        yield service_instance


@pytest.fixture
def mock_media_manager_service():
    with patch("content.commands.MediaManagerService") as mock:
        service_instance = mock.return_value
        service_instance.generate_suggestions = AsyncMock()
        yield service_instance


@pytest.fixture
def mock_wikimedia_service():
    with patch("content.commands.WikimediaService") as mock:
        service_instance = mock.return_value
        service_instance.process_suggestion = AsyncMock()
        service_instance.__aenter__ = AsyncMock(return_value=service_instance)
        service_instance.__aexit__ = AsyncMock()
        yield service_instance


# noinspection PyArgumentList,PyTypeChecker
def test_generate_suggestions_success(
    app, db_session, test_category, mock_content_manager_service
):
    """Test successful generation of article suggestions."""
    # Prepare mock response
    mock_suggestions = [
        ArticleSuggestion(
            category_id=test_category.id,
            title="Test Article",
            main_topic="Test Topic",
            sub_topics=["Topic 1", "Topic 2"],
            point_of_view="Test POV",
            level=ArticleLevel.HIGH_SCHOOL,
        )
    ]
    mock_content_manager_service.generate_suggestions.return_value = mock_suggestions

    runner = CliRunner()
    result = runner.invoke(
        generate_suggestions,
        [str(test_category.id), "HIGH_SCHOOL", "--count", "1"],
        obj=ScriptInfo(create_app=lambda info: app),
    )

    assert result.exit_code == 0
    assert "Successfully generated 1 suggestions" in result.output

    # Verify service was called correctly
    mock_content_manager_service.generate_suggestions.assert_called_once_with(
        category_id=test_category.id,
        level="HIGH_SCHOOL",
        num_suggestions=1,
    )


# noinspection PyArgumentList,PyTypeChecker
def test_generate_suggestions_invalid_category(
    app, db_session, mock_content_manager_service
):
    """Test suggestion generation with invalid category ID."""
    runner = CliRunner()
    result = runner.invoke(
        generate_suggestions,
        ["999999", "HIGH_SCHOOL"],  # Non-existent category ID
        obj=ScriptInfo(create_app=lambda info: app),
    )

    assert result.exit_code == 0  # Click convention for handled errors
    assert "Error: Category 999999 not found" in result.output
    mock_content_manager_service.generate_suggestions.assert_not_called()


# noinspection PyArgumentList,PyTypeChecker
def test_generate_research_success(
    app, db_session, test_suggestion, mock_researcher_service
):
    """Test successful generation of research content."""
    # Prepare mock response
    mock_research = Research(
        suggestion_id=test_suggestion.id,
        content="Test research content",
        status=ContentStatus.PENDING,
    )
    mock_researcher_service.generate_research.return_value = mock_research

    runner = CliRunner()
    result = runner.invoke(
        generate_research,
        [str(test_suggestion.id)],
        obj=ScriptInfo(create_app=lambda info: app),
    )

    assert result.exit_code == 0
    assert "Research generated successfully!" in result.output

    # Verify service was called correctly
    mock_researcher_service.generate_research.assert_called_once_with(
        suggestion_id=test_suggestion.id
    )


# noinspection PyArgumentList,PyTypeChecker
def test_generate_research_invalid_suggestion(app, db_session, mock_researcher_service):
    """Test research generation with invalid suggestion ID."""
    runner = CliRunner()
    result = runner.invoke(
        generate_research,
        ["999999"],  # Non-existent suggestion ID
        obj=ScriptInfo(create_app=lambda info: app),
    )

    assert result.exit_code == 0
    assert "Error: ArticleSuggestion 999999 not found" in result.output
    mock_researcher_service.generate_research.assert_not_called()


# noinspection PyArgumentList,PyTypeChecker
def test_generate_article_success(app, db_session, test_research, mock_writer_service):
    """Test successful generation of an article."""
    # Set research status to approved
    test_research.status = ContentStatus.APPROVED
    db_session.commit()

    # Prepare mock response
    mock_article = Article(
        research_id=test_research.id,
        category_id=test_research.suggestion.category_id,
        title="Test Article",
        content="Test content",
        excerpt="Test excerpt",
        level=ArticleLevel.HIGH_SCHOOL,
    )
    mock_writer_service.generate_article.return_value = mock_article

    runner = CliRunner()
    result = runner.invoke(
        generate_article,
        [str(test_research.id)],
        obj=ScriptInfo(create_app=lambda info: app),
    )

    assert result.exit_code == 0
    assert "Article generated successfully!" in result.output

    # Verify service was called correctly
    mock_writer_service.generate_article.assert_called_once_with(
        research_id=test_research.id
    )


# noinspection PyArgumentList,PyTypeChecker
def test_generate_article_unapproved_research(
    app, db_session, test_research, mock_writer_service
):
    """Test article generation with unapproved research."""
    # Ensure research is not approved
    test_research.status = ContentStatus.PENDING
    db_session.commit()

    runner = CliRunner()
    result = runner.invoke(
        generate_article,
        [str(test_research.id)],
        obj=ScriptInfo(create_app=lambda info: app),
    )

    assert result.exit_code == 0
    assert f"Error: Research {test_research.id} is not approved" in result.output
    mock_writer_service.generate_article.assert_not_called()


# noinspection PyArgumentList,PyTypeChecker
def test_generate_story_success(
    app, db_session, test_article, mock_social_media_service
):
    """Test successful generation of an Instagram story."""
    # Prepare mock response
    mock_post = SocialMediaPost(
        article_id=test_article.id,
        account_id=1,  # This would come from your test fixture
        content="Test story content",
        hashtags=["test"],
        status=ContentStatus.PENDING,
    )
    mock_social_media_service.generate_story_promotion.return_value = mock_post

    runner = CliRunner()
    result = runner.invoke(
        generate_story,
        [str(test_article.id)],
        obj=ScriptInfo(create_app=lambda info: app),
    )

    assert result.exit_code == 0
    assert "Story generated successfully!" in result.output

    # Verify service was called correctly
    mock_social_media_service.generate_story_promotion.assert_called_once_with(
        article_id=test_article.id
    )


# noinspection PyArgumentList,PyTypeChecker
def test_generate_did_you_know_success(
    app, db_session, test_article, mock_social_media_service
):
    """Test successful generation of did-you-know posts."""
    # Prepare mock response
    mock_posts = [
        SocialMediaPost(
            article_id=test_article.id,
            account_id=1,
            content=f"Did you know fact {i}",
            hashtags=["test"],
            status=ContentStatus.PENDING,
        )
        for i in range(3)
    ]
    mock_social_media_service.generate_did_you_know_posts.return_value = mock_posts

    runner = CliRunner()
    result = runner.invoke(
        generate_did_you_know,
        [str(test_article.id), "--count", "3"],
        obj=ScriptInfo(create_app=lambda info: app),
    )

    assert result.exit_code == 0
    assert "Successfully generated 3 posts" in result.output

    # Verify service was called correctly
    mock_social_media_service.generate_did_you_know_posts.assert_called_once_with(
        article_id=test_article.id,
        num_posts=3,
    )


# noinspection PyArgumentList,PyTypeChecker
def test_generate_media_suggestions_success(
    app, db_session, test_research, mock_media_manager_service
):
    """Test successful generation of media suggestions."""
    # Set research status to approved
    test_research.status = ContentStatus.APPROVED
    db_session.commit()

    # Prepare mock response
    mock_suggestion = MediaSuggestion(
        research_id=test_research.id,
        commons_categories=["Test Category"],
        search_queries=["Test Query"],
        illustration_topics=["Test Topic"],
        reasoning="Test reasoning",
    )
    mock_media_manager_service.generate_suggestions.return_value = mock_suggestion

    runner = CliRunner()
    result = runner.invoke(
        generate_media_suggestions,
        [str(test_research.id)],
        obj=ScriptInfo(create_app=lambda info: app),
    )

    assert result.exit_code == 0
    assert "Suggestions generated successfully!" in result.output

    # Verify service was called correctly
    mock_media_manager_service.generate_suggestions.assert_called_once_with(
        research_id=test_research.id
    )


# noinspection PyArgumentList,PyTypeChecker
def test_fetch_media_candidates_success(
    app, db_session, test_media_suggestion, mock_wikimedia_service
):
    """Test successful fetching of media candidates."""
    # Prepare mock response with realistic test data
    mock_candidates = [
        MediaCandidate(
            suggestion_id=test_media_suggestion.id,
            commons_id="File:Test_Image.jpg",
            commons_url="https://commons.wikimedia.org/wiki/File:Test_Image.jpg",
            title="Test Historical Image",
            description="A test image for historical content",
            author="Test Author",
            license="CC BY-SA 4.0",
            license_url="https://creativecommons.org/licenses/by-sa/4.0/",
            width=1920,
            height=1080,
            mime_type="image/jpeg",
            file_size=1024000,
        ),
        MediaCandidate(
            suggestion_id=test_media_suggestion.id,
            commons_id="File:Another_Test.jpg",
            commons_url="https://commons.wikimedia.org/wiki/File:Another_Test.jpg",
            title="Another Test Image",
            description="Another test image",
            author="Another Author",
            license="CC BY 4.0",
            license_url="https://creativecommons.org/licenses/by/4.0/",
            width=800,
            height=600,
            mime_type="image/jpeg",
            file_size=512000,
        ),
    ]
    mock_wikimedia_service.process_suggestion.return_value = mock_candidates

    runner = CliRunner()
    result = runner.invoke(
        fetch_media_candidates,
        [str(test_media_suggestion.id), "--max-per-query", "5"],
        obj=ScriptInfo(create_app=lambda info: app),
    )

    assert result.exit_code == 0
    assert f"Fetched {len(mock_candidates)} candidates" in result.output
    assert "Title: Test Historical Image" in result.output
    assert "Author: Test Author" in result.output
    assert "License: CC BY-SA 4.0" in result.output
    assert "Dimensions: 1920x1080" in result.output

    # Verify service was called correctly
    mock_wikimedia_service.process_suggestion.assert_called_once_with(
        suggestion_id=test_media_suggestion.id,
        max_per_query=5,
    )


# noinspection PyTypeChecker
def test_fetch_media_candidates_invalid_suggestion(
    app, db_session, mock_wikimedia_service
):
    """Test fetching media candidates with invalid suggestion ID."""
    runner = CliRunner()
    result = runner.invoke(
        fetch_media_candidates,
        ["999999"],  # Non-existent suggestion ID
        obj=ScriptInfo(create_app=lambda info: app),
    )

    assert result.exit_code == 0
    assert "Error: MediaSuggestion 999999 not found" in result.output
    mock_wikimedia_service.process_suggestion.assert_not_called()
