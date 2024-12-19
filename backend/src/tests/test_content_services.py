import json
from unittest.mock import patch, Mock

import pytest
from sqlalchemy.exc import IntegrityError

from agents.models import AgentType
from content.models import (
    ArticleSuggestion,
    ContentStatus,
    ArticleLevel,
    Article,
    Research,
)
from content.services import ContentManagerService, ResearcherService


# noinspection DuplicatedCode
@pytest.mark.asyncio
async def test_generate_suggestions_success(
    app,
    db_session,
    test_category,
    test_agent,
    mock_anthropic_client,
    mock_anthropic_response,
):
    """Test successful generation of article suggestions."""
    # Initialize service
    service = ContentManagerService()

    # Generate suggestions
    suggestions = await service.generate_suggestions(
        category_id=test_category.id,
        level=ArticleLevel.HIGH_SCHOOL.value,
        num_suggestions=1,
    )

    # Verify suggestions were created
    assert len(suggestions) == 1
    suggestion = suggestions[0]
    assert isinstance(suggestion, ArticleSuggestion)
    assert suggestion.category_id == test_category.id
    assert suggestion.title == "Test Article"
    assert suggestion.main_topic == "Main topic description"
    assert suggestion.sub_topics == ["Topic 1", "Topic 2"]
    assert suggestion.level == ArticleLevel.HIGH_SCHOOL
    assert suggestion.status == ContentStatus.PENDING

    # Verify API was called with correct parameters
    mock_anthropic_client.assert_called_once()
    call_args = mock_anthropic_client.call_args
    prompt = call_args.args[0]
    assert test_category.name in prompt
    assert "HIGH_SCHOOL" in prompt

    # Verify model metadata was recorded
    assert suggestion.model_id == test_agent.model.id
    assert suggestion.tokens_used > 0  # Should be 150 (input + output tokens)
    assert suggestion.generation_started_at is not None


@pytest.mark.asyncio
async def test_generate_suggestions_invalid_category(
    app,
    db_session,
    test_agent,
    mock_anthropic_client,
):
    """Test suggestion generation with invalid category ID."""
    service = ContentManagerService()

    with pytest.raises(ValueError, match="Category 999 not found"):
        await service.generate_suggestions(
            category_id=999,  # Non-existent category ID
            level=ArticleLevel.HIGH_SCHOOL.value,
            num_suggestions=1,
        )

    # Verify no API call was made
    mock_anthropic_client.assert_not_called()

    # Verify no suggestions were created
    assert ArticleSuggestion.query.count() == 0


@pytest.mark.asyncio
async def test_generate_suggestions_invalid_level(
    app,
    db_session,
    test_category,
    test_agent,
    mock_anthropic_client,
):
    """Test suggestion generation with invalid article level."""
    service = ContentManagerService()

    with pytest.raises(ValueError, match="Invalid level: INVALID_LEVEL"):
        await service.generate_suggestions(
            category_id=test_category.id,
            level="INVALID_LEVEL",  # Invalid level
            num_suggestions=1,
        )

    # Verify no API call was made
    mock_anthropic_client.assert_not_called()

    # Verify no suggestions were created
    assert ArticleSuggestion.query.count() == 0


@pytest.mark.asyncio
async def test_generate_suggestions_invalid_count(
    app,
    db_session,
    test_category,
    test_agent,
    mock_anthropic_client,
):
    """Test suggestion generation with invalid number of suggestions."""
    service = ContentManagerService()

    with pytest.raises(ValueError, match="Number of suggestions must be at least 1"):
        await service.generate_suggestions(
            category_id=test_category.id,
            level=ArticleLevel.HIGH_SCHOOL.value,
            num_suggestions=0,  # Invalid count
        )

    # Verify no API call was made
    mock_anthropic_client.assert_not_called()

    # Verify no suggestions were created
    assert ArticleSuggestion.query.count() == 0


@pytest.mark.asyncio
async def test_generate_suggestions_api_error(
    app,
    db_session,
    test_category,
    test_agent,
    mock_anthropic_client,
    caplog,
):
    """Test handling of API errors during suggestion generation."""
    # Configure mock to raise a raw API error
    mock_anthropic_client.side_effect = Exception("Raw API Error")

    service = ContentManagerService()

    # The service should wrap the raw error in its own ValueError
    with pytest.raises(Exception):
        await service.generate_suggestions(
            category_id=test_category.id,
            level=ArticleLevel.HIGH_SCHOOL.value,
            num_suggestions=1,
        )

    # Verify the error was logged
    assert "Error generating suggestions: Raw API Error" in [
        r.message for r in caplog.records
    ]

    # Verify API was called (and failed)
    mock_anthropic_client.assert_called_once()

    # Verify no suggestions were created and session was rolled back
    assert ArticleSuggestion.query.count() == 0


# noinspection PyTypeChecker
@pytest.mark.asyncio
async def test_generate_suggestions_database_error(
    app,
    db_session,
    test_category,
    test_agent,
    mock_anthropic_client,
    mock_anthropic_response,
):
    """Test handling of database errors during suggestion creation."""
    mock_anthropic_client.return_value = mock_anthropic_response

    service = ContentManagerService()

    # Simulate database error during suggestion creation
    with patch("content.services.db.session.commit") as mock_commit:
        mock_commit.side_effect = IntegrityError(None, None, None)

        with pytest.raises(ValueError, match="Failed to save suggestions"):
            await service.generate_suggestions(
                category_id=test_category.id,
                level=ArticleLevel.HIGH_SCHOOL.value,
                num_suggestions=1,
            )

    # Verify API was called successfully
    mock_anthropic_client.assert_called_once()

    # Verify session was rolled back and no suggestions were created
    assert ArticleSuggestion.query.count() == 0


@pytest.mark.asyncio
async def test_generate_suggestions_invalid_response_format(
    app,
    db_session,
    test_category,
    test_agent,
    mock_anthropic_client,
):
    """Test handling of invalid API response format."""
    # Configure mock to return invalid JSON
    mock_response = Mock()
    mock_response.content = [Mock(text="Invalid JSON")]
    mock_response.usage = Mock(input_tokens=100, output_tokens=50)
    mock_anthropic_client.return_value = mock_response

    service = ContentManagerService()

    with pytest.raises(ValueError, match="Invalid API response format"):
        await service.generate_suggestions(
            category_id=test_category.id,
            level=ArticleLevel.HIGH_SCHOOL.value,
            num_suggestions=1,
        )

    # Verify API was called
    mock_anthropic_client.assert_called_once()

    # Verify no suggestions were created
    assert ArticleSuggestion.query.count() == 0


@pytest.mark.asyncio
async def test_generate_suggestions_missing_required_fields(
    app,
    db_session,
    test_category,
    test_agent,
    mock_anthropic_client,
):
    """Test handling of API response missing required fields."""
    # Configure mock to return incomplete suggestion data
    mock_response = Mock()
    mock_response.content = [
        Mock(
            text=json.dumps(
                {
                    "suggestions": [
                        {
                            "title": "Test Article",
                            # Missing main_topic and other required fields
                        }
                    ]
                }
            )
        )
    ]
    mock_response.usage = Mock(input_tokens=100, output_tokens=50)
    mock_anthropic_client.return_value = mock_response

    service = ContentManagerService()

    with pytest.raises(KeyError, match="main_topic"):
        await service.generate_suggestions(
            category_id=test_category.id,
            level=ArticleLevel.HIGH_SCHOOL.value,
            num_suggestions=1,
        )

    # Verify API was called
    mock_anthropic_client.assert_called_once()

    # Verify no suggestions were created
    assert ArticleSuggestion.query.count() == 0


@pytest.mark.asyncio
async def test_generate_suggestions_multiple(
    app,
    db_session,
    test_category,
    test_agent,
    mock_anthropic_client,
):
    """Test generating multiple suggestions at once."""
    # Configure mock response with multiple suggestions
    mock_response = Mock()
    mock_response.content = [
        Mock(
            text=json.dumps(
                {
                    "suggestions": [
                        {
                            "title": f"Test Article {i}",
                            "main_topic": f"Main topic description {i}",
                            "sub_topics": [f"Topic {i}.1", f"Topic {i}.2"],
                            "point_of_view": f"Academic analysis {i}",
                        }
                        for i in range(3)
                    ]
                }
            )
        )
    ]
    mock_response.usage = Mock(input_tokens=300, output_tokens=150)
    mock_anthropic_client.return_value = mock_response

    service = ContentManagerService()

    # Generate multiple suggestions
    suggestions = await service.generate_suggestions(
        category_id=test_category.id,
        level=ArticleLevel.HIGH_SCHOOL.value,
        num_suggestions=3,
    )

    # Verify correct number of suggestions created
    assert len(suggestions) == 3
    assert ArticleSuggestion.query.count() == 3

    # Verify each suggestion has unique content
    titles = {s.title for s in suggestions}
    assert len(titles) == 3

    # Verify token distribution
    total_tokens = 450  # 300 input + 150 output
    tokens_per_suggestion = total_tokens // 3
    for suggestion in suggestions:
        assert suggestion.tokens_used == tokens_per_suggestion
        assert suggestion.model_id == test_agent.model.id
        assert suggestion.generation_started_at is not None
        assert suggestion.status == ContentStatus.PENDING

    # Verify content of each suggestion
    for i, suggestion in enumerate(suggestions):
        assert suggestion.title == f"Test Article {i}"
        assert suggestion.main_topic == f"Main topic description {i}"
        assert suggestion.sub_topics == [f"Topic {i}.1", f"Topic {i}.2"]
        assert suggestion.point_of_view == f"Academic analysis {i}"
        assert suggestion.level == ArticleLevel.HIGH_SCHOOL


# noinspection PyArgumentList,DuplicatedCode
@pytest.mark.asyncio
async def test_generate_suggestions_considers_existing_articles(
    app,
    db_session,
    test_category,
    test_agent,
    mock_anthropic_client,
):
    """Test that suggestion generation considers existing articles."""
    # Create existing articles with their required relationships
    articles_data = []
    for i in range(2):
        # Create suggestion
        suggestion = ArticleSuggestion(
            category_id=test_category.id,
            title=f"Existing Suggestion {i+1}",
            main_topic="Test topic",
            sub_topics=["Test subtopic"],
            point_of_view="Test POV",
            level=ArticleLevel.HIGH_SCHOOL,
        )
        db_session.add(suggestion)
        db_session.flush()  # Get ID assigned

        # Create research
        research = Research(
            suggestion_id=suggestion.id,
            content=f"Test research content {i+1}",
            status=ContentStatus.APPROVED,
        )
        db_session.add(research)
        db_session.flush()

        # Create article
        article = Article(
            research_id=research.id,
            category_id=test_category.id,
            title=f"Existing Article {i+1}",
            content=f"Test content {i+1}",
            ai_summary=f"Summary of article {i+1}",
            level=ArticleLevel.HIGH_SCHOOL,
            status=ContentStatus.APPROVED,
        )
        articles_data.append(article)

    db_session.add_all(articles_data)
    db_session.commit()

    # Set up mock response
    mock_response = Mock()
    mock_response.content = [
        Mock(
            text=json.dumps(
                {
                    "suggestions": [
                        {
                            "title": "New Test Article",
                            "main_topic": "Main topic description",
                            "sub_topics": ["Topic 1", "Topic 2"],
                            "point_of_view": "Academic analysis",
                        }
                    ]
                }
            )
        )
    ]
    mock_response.usage = Mock(input_tokens=100, output_tokens=50)
    mock_anthropic_client.return_value = mock_response

    service = ContentManagerService()

    # Generate new suggestion
    suggestions = await service.generate_suggestions(
        category_id=test_category.id,
        level=ArticleLevel.HIGH_SCHOOL.value,
        num_suggestions=1,
    )

    # Verify API was called with existing article summaries in prompt
    mock_anthropic_client.assert_called_once()
    call_args = mock_anthropic_client.call_args
    prompt = call_args.args[0]

    # Check that existing article information is in the prompt
    assert "Existing Article 1" in prompt
    assert "Summary of article 1" in prompt
    assert "Existing Article 2" in prompt
    assert "Summary of article 2" in prompt

    # Verify new suggestion was created
    assert len(suggestions) == 1
    new_suggestion = suggestions[0]
    assert new_suggestion.title == "New Test Article"


@pytest.mark.asyncio
async def test_generate_suggestions_no_active_agent(app, db_session):
    """Test service initialization with no active content manager agent."""
    # No need to create any agent

    with pytest.raises(ValueError, match="No active content manager agent found"):
        ContentManagerService()


# noinspection PyArgumentList,DuplicatedCode
@pytest.mark.asyncio
async def test_generate_suggestions_articles_without_summaries(
    app,
    db_session,
    test_category,
    test_agent,
    mock_anthropic_client,
):
    """Test that articles without AI summaries are handled properly."""
    # Create an article without AI summary
    suggestion = ArticleSuggestion(
        category_id=test_category.id,
        title="Existing Suggestion",
        main_topic="Test topic",
        sub_topics=["Test subtopic"],
        point_of_view="Test POV",
        level=ArticleLevel.HIGH_SCHOOL,
    )
    db_session.add(suggestion)
    db_session.flush()

    research = Research(
        suggestion_id=suggestion.id,
        content="Test research content",
        status=ContentStatus.APPROVED,
    )
    db_session.add(research)
    db_session.flush()

    article = Article(
        research_id=research.id,
        category_id=test_category.id,
        title="Article Without Summary",
        content="Test content",
        # No ai_summary
        level=ArticleLevel.HIGH_SCHOOL,
        status=ContentStatus.APPROVED,
    )
    db_session.add(article)
    db_session.commit()

    # Set up mock response
    mock_response = Mock()
    mock_response.content = [
        Mock(
            text=json.dumps(
                {
                    "suggestions": [
                        {
                            "title": "New Test Article",
                            "main_topic": "Main topic description",
                            "sub_topics": ["Topic 1", "Topic 2"],
                            "point_of_view": "Academic analysis",
                        }
                    ]
                }
            )
        )
    ]
    mock_response.usage = Mock(input_tokens=100, output_tokens=50)
    mock_anthropic_client.return_value = mock_response

    service = ContentManagerService()
    suggestions = await service.generate_suggestions(
        category_id=test_category.id,
        level=ArticleLevel.HIGH_SCHOOL.value,
        num_suggestions=1,
    )

    # Verify API was called with appropriate prompt
    mock_anthropic_client.assert_called_once()
    call_args = mock_anthropic_client.call_args
    prompt = call_args.args[0]

    # Article without summary should not be included
    assert "Article Without Summary" not in prompt

    # Verify new suggestion was still created successfully
    assert len(suggestions) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("test_agent", [AgentType.RESEARCHER], indirect=True)
async def test_generate_research_invalid_suggestion(
    app,
    db_session,
    test_agent,
    mock_anthropic_client,
):
    """Test research generation with invalid suggestion ID."""
    service = ResearcherService()

    with pytest.raises(ValueError, match="ArticleSuggestion 999 not found"):
        await service.generate_research(suggestion_id=999)

    # Verify no API call was made
    mock_anthropic_client.assert_not_called()

    # Verify no research was created
    assert Research.query.count() == 0


@pytest.mark.asyncio
@pytest.mark.parametrize("test_agent", [AgentType.RESEARCHER], indirect=True)
async def test_generate_research_api_error(
    app,
    db_session,
    test_suggestion,
    test_agent,
    mock_anthropic_client,
    caplog,
):
    """Test handling of API errors during research generation."""
    # Configure mock to raise an error
    mock_anthropic_client.side_effect = Exception("API Error")

    service = ResearcherService()

    with pytest.raises(Exception):
        await service.generate_research(suggestion_id=test_suggestion.id)

    # Verify error was logged
    assert "Error generating research: API Error" in [r.message for r in caplog.records]

    # Verify API was called
    mock_anthropic_client.assert_called_once()

    # Verify no research was created
    assert Research.query.count() == 0


# noinspection PyTypeChecker
@pytest.mark.asyncio
@pytest.mark.parametrize("test_agent", [AgentType.RESEARCHER], indirect=True)
async def test_generate_research_database_error(
    app,
    db_session,
    test_suggestion,
    test_agent,
    mock_anthropic_client,
):
    """Test handling of database errors during research creation."""
    # Configure mock response
    mock_response = Mock(
        content=[Mock(text="Test research content")],
        usage=Mock(input_tokens=100, output_tokens=50),
    )
    mock_anthropic_client.return_value = mock_response

    service = ResearcherService()

    # Simulate database error
    with patch("content.services.db.session.commit") as mock_commit:
        mock_commit.side_effect = IntegrityError(None, None, None)

        with pytest.raises(Exception):
            await service.generate_research(suggestion_id=test_suggestion.id)

    # Verify session was rolled back and no research was created
    assert Research.query.count() == 0


@pytest.mark.asyncio
@pytest.mark.parametrize("test_agent", [AgentType.RESEARCHER], indirect=True)
async def test_clean_markdown_method(
    app,
    db_session,
    test_agent,
):
    """Test the _clean_markdown static method."""
    # Test with Markdown code block
    content = "```markdown\nTest content\n```"
    cleaned = ResearcherService._clean_markdown(content)
    assert cleaned.strip() == "Test content"  # Use strip() to handle newlines

    # Test with regular code block
    content = "```\nTest content\n```"
    cleaned = ResearcherService._clean_markdown(content)
    assert cleaned.strip() == "Test content"

    # Test with no code block
    content = "Test content"
    cleaned = ResearcherService._clean_markdown(content)
    assert cleaned.strip() == "Test content"


@pytest.mark.asyncio
async def test_prepare_research_params(
    app,
    db_session,
    test_suggestion,
    test_category,
):
    """Test the _prepare_research_params static method."""
    params = ResearcherService._prepare_research_params(test_suggestion, test_category)

    # Verify structure and content of parameters
    assert "suggestion" in params
    assert "context" in params
    assert "constraints" in params

    # Verify suggestion parameters
    assert params["suggestion"]["title"] == test_suggestion.title
    assert params["suggestion"]["main_topic"] == test_suggestion.main_topic
    assert params["suggestion"]["level"] == "COLLEGE"

    # Verify context parameters
    assert params["context"]["taxonomy"] == test_category.taxonomy.name
    assert params["context"]["category"] == test_category.name

    # Verify format constraint
    assert params["constraints"]["format"] == "markdown"
