from datetime import datetime, timezone

import pytest

from agents.models import AIModel, Agent, PromptTemplate, Provider, AgentType


def test_ai_model_creation(db_session):
    """Test creating an AI model."""
    model = AIModel(
        name="GPT-4 Turbo",
        provider=Provider.OPENAI,
        model_id="gpt-4-turbo",
        description="Latest GPT-4 model",
        is_active=True,
    )
    db_session.add(model)
    db_session.commit()

    assert model.id is not None
    assert model.name == "GPT-4 Turbo"
    assert model.provider == Provider.OPENAI
    assert model.is_active
    assert model.created_at is not None
    assert model.updated_at is not None


def test_ai_model_update(db_session):
    """Test updating an AI model."""
    model = AIModel(
        name="GPT-4",
        provider=Provider.OPENAI,
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


def test_agent_creation(db_session):
    """Test creating an agent with templates."""
    # Create AI model first
    model = AIModel(
        name="GPT-4",
        provider=Provider.OPENAI,
        model_id="gpt-4",
        description="Test model",
        is_active=True,
    )
    db_session.add(model)
    db_session.commit()

    # Create agent
    agent = Agent(
        name="Test Agent",
        type=AgentType.RESEARCHER,
        description="Test agent",
        model=model,
        temperature=0.7,
        max_tokens=1000,
        is_active=True,
    )
    db_session.add(agent)
    db_session.commit()

    assert agent.id is not None
    assert agent.name == "Test Agent"
    assert agent.type == AgentType.RESEARCHER
    assert agent.model_id == model.id


def test_prompt_template_creation(db_session):
    """Test creating and using prompt templates."""
    # Create model and agent first
    model = AIModel(
        name="GPT-4", provider=Provider.OPENAI, model_id="gpt-4", is_active=True
    )
    db_session.add(model)

    agent = Agent(
        name="Test Agent",
        type=AgentType.RESEARCHER,
        model=model,
        temperature=0.7,
        max_tokens=1000,
    )
    db_session.add(agent)
    db_session.commit()

    # Create template
    template = PromptTemplate(
        agent=agent,
        name="test_template",
        description="Test template",
        template="Hello {name}!",
        is_active=True,
    )
    db_session.add(template)
    db_session.commit()

    assert template.id is not None
    assert template.name == "test_template"

    # Test template rendering
    rendered = template.render(name="World")
    assert rendered == "Hello World!"


def test_agent_helper_methods(db_session):
    """Test agent helper methods."""
    # Create model and agent with template
    model = AIModel(
        name="GPT-4", provider=Provider.OPENAI, model_id="gpt-4", is_active=True
    )
    db_session.add(model)

    agent = Agent(
        name="Test Agent",
        type=AgentType.RESEARCHER,
        model=model,
        temperature=0.7,
        max_tokens=1000,
    )
    db_session.add(agent)

    template = PromptTemplate(
        agent=agent,
        name="test_template",
        description="Test template",
        template="Hello {name}!",
        is_active=True,
    )
    db_session.add(template)  # Changed from db_session.add(agent)
    db_session.commit()

    # Test get_template
    assert agent.get_template("test_template") == template
    assert agent.get_template("nonexistent") is None

    # Test render_template
    assert agent.render_template("test_template", name="World") == "Hello World!"


def test_ai_generation_mixin_usage(db_session, test_category):
    """Test AIGenerationMixin fields in a model that uses it."""
    from content.models import ArticleSuggestion, ArticleLevel

    # First create an AI model
    model = AIModel(
        name="Claude",
        provider=Provider.ANTHROPIC,
        model_id="claude-3",
        description="Anthropic's latest model",
    )
    db_session.add(model)
    db_session.commit()

    # Create an article suggestion with test_category
    suggestion = ArticleSuggestion(
        category=test_category,
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


@pytest.mark.parametrize(
    "template_str,vars,expected",
    [
        ("Hello {name}!", {"name": "World"}, "Hello World!"),
        ("Multi\nline", {}, "Multi\nline"),
        ("Count: {count}", {"count": 42}, "Count: 42"),
    ],
)
def test_prompt_template_rendering(db_session, template_str, vars, expected):
    """Test different template rendering scenarios."""
    # Create necessary objects
    model = AIModel(
        name="Test", provider=Provider.OPENAI, model_id="test", is_active=True
    )
    db_session.add(model)

    agent = Agent(
        name="Test Agent",
        type=AgentType.RESEARCHER,
        model=model,
        temperature=0.7,
        max_tokens=1000,
    )
    db_session.add(agent)

    template = PromptTemplate(
        agent=agent, name="test", template=template_str, is_active=True
    )
    db_session.add(template)
    db_session.commit()

    assert template.render(**vars) == expected
