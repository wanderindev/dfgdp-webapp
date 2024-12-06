from datetime import datetime, timezone

from agents.models import AIModel


def test_ai_model_creation(db_session):
    """Test creating an AI model."""
    model = AIModel(
        name="GPT-4 Turbo",
        provider="openai",
        model_id="gpt-4-turbo",
        description="Latest GPT-4 model",
        is_active=True,
    )
    db_session.add(model)
    db_session.commit()

    assert model.id is not None
    assert model.name == "GPT-4 Turbo"
    assert model.provider == "openai"
    assert model.is_active
    assert model.created_at is not None
    assert model.updated_at is not None


def test_ai_model_update(db_session):
    """Test updating an AI model."""
    model = AIModel(
        name="GPT-4",
        provider="openai",
        model_id="gpt-4",
        description="Base GPT-4 model",
        is_active=True,
    )
    db_session.add(model)
    db_session.commit()

    original_updated_at = model.updated_at

    # Wait a moment to ensure timestamp difference
    import time

    time.sleep(0.1)

    # Update the model
    model.description = "Updated description"
    db_session.commit()

    assert model.description == "Updated description"
    assert model.updated_at > original_updated_at


# noinspection PyArgumentList
def test_ai_generation_mixin_usage(db_session, test_category):
    """Test AIGenerationMixin fields in a model that uses it."""
    from content.models import ArticleSuggestion, ArticleLevel

    # First create an AI model
    model = AIModel(
        name="Claude",
        provider="anthropic",
        model_id="claude-3",
        description="Anthropic's latest model",
    )
    db_session.add(model)
    db_session.commit()

    # Create an article suggestion that uses AIGenerationMixin
    suggestion = ArticleSuggestion(
        category_id=1,  # You might need to adjust this
        title="Test Suggestion",
        main_topic="Test Topic",
        sub_topics=["Topic 1", "Topic 2"],
        point_of_view="Test POV",
        level=ArticleLevel.HIGH_SCHOOL,
        # AIGenerationMixin fields
        tokens_used=1500,
        model_id=model.id,
        generation_started_at=datetime.now(timezone.utc),
    )
    db_session.add(suggestion)
    db_session.commit()

    assert suggestion.tokens_used == 1500
    assert suggestion.model_id == model.id
    assert suggestion.generation_started_at is not None
    assert suggestion.last_generation_error is None
