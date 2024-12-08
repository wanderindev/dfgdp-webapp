from datetime import datetime, timezone, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from flask import current_app

from agents.models import AIModel, Agent, PromptTemplate, Provider, AgentType, Usage
from extensions import db


# noinspection PyArgumentList
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


# noinspection PyArgumentList
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


# noinspection PyArgumentList
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


# noinspection PyArgumentList
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


# noinspection PyArgumentList
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


# noinspection PyArgumentList
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


# noinspection PyArgumentList
@pytest.mark.parametrize(
    "template_str,vars_,expected",
    [
        ("Hello {name}!", {"name": "World"}, "Hello World!"),
        ("Multi\nline", {}, "Multi\nline"),
        ("Count: {count}", {"count": 42}, "Count: 42"),
    ],
)
def test_prompt_template_rendering(db_session, template_str, vars_, expected):
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

    assert template.render(**vars_) == expected


# noinspection PyArgumentList
def test_usage_creation(db_session):
    """Test creating and querying usage records."""
    # Create an AI model first
    model = AIModel(
        name="GPT-4", provider=Provider.OPENAI, model_id="gpt-4", is_active=True
    )
    db_session.add(model)
    db_session.commit()

    # Create usage record
    usage = Usage(
        provider=Provider.OPENAI,
        model_id=model.model_id,
        input_tokens=100,
        output_tokens=50,
        cost=0.0015,  # Example cost
        timestamp=datetime.now(timezone.utc),
    )
    db_session.add(usage)
    db_session.commit()

    assert usage.id is not None
    assert usage.input_tokens == 100
    assert usage.output_tokens == 50
    assert usage.cost == 0.0015


# noinspection PyArgumentList
def test_usage_summary(db_session):
    """Test getting usage summary for a date range."""
    # Create some usage records
    now = datetime.now(timezone.utc)
    model_id = "gpt-4"

    usages = [
        Usage(
            provider=Provider.OPENAI,
            model_id=model_id,
            input_tokens=100,
            output_tokens=50,
            cost=0.0015,
            timestamp=now - timedelta(days=1),
        ),
        Usage(
            provider=Provider.OPENAI,
            model_id=model_id,
            input_tokens=200,
            output_tokens=100,
            cost=0.003,
            timestamp=now,
        ),
        # This one should not be included in summary
        Usage(
            provider=Provider.OPENAI,
            model_id=model_id,
            input_tokens=300,
            output_tokens=150,
            cost=0.0045,
            timestamp=now - timedelta(days=10),
        ),
    ]
    db.session.add_all(usages)
    db.session.commit()

    # Get summary for last 7 days
    start_date = now - timedelta(days=7)
    summary = Usage.get_usage_summary(start_date, now)

    assert len(summary) == 1  # One provider
    provider_summary = summary[0]
    assert provider_summary.total_input_tokens == 300  # 100 + 200
    assert provider_summary.total_output_tokens == 150  # 50 + 100
    assert provider_summary.total_cost == pytest.approx(0.0045)


# noinspection PyArgumentList
@pytest.mark.asyncio
async def test_agent_get_client(db_session):
    """Test agent's get_client method."""
    # Mock both client classes
    with patch("agents.clients.openai_client.AsyncOpenAI") as mock_openai, patch(
        "agents.clients.anthropic_client.AsyncAnthropic"
    ) as mock_anthropic:
        # Create AI model
        model = AIModel(
            name="GPT-4", provider=Provider.OPENAI, model_id="gpt-4", is_active=True
        )
        db_session.add(model)

        # Create agent
        agent = Agent(
            name="Test Agent",
            type=AgentType.RESEARCHER,
            model=model,
            temperature=0.7,
            max_tokens=1000,
            is_active=True,
        )
        db_session.add(agent)
        db_session.commit()

        # Get client
        client = agent.get_client()

        # Verify the correct client was instantiated
        mock_openai.assert_called_once()
        mock_anthropic.assert_not_called()

        # Test client configuration
        assert client.model == model.model_id
        assert client.temperature == agent.temperature
        assert client.max_tokens == agent.max_tokens


# noinspection PyArgumentList
@pytest.mark.asyncio
async def test_agent_generate_content(db_session):
    """Test agent's generate_content method."""
    mock_usage = SimpleNamespace(
        prompt_tokens=10, completion_tokens=20, total_tokens=30
    )
    mock_message = SimpleNamespace(content="Generated test content")
    mock_choice = SimpleNamespace(message=mock_message)
    mock_completion = SimpleNamespace(choices=[mock_choice], usage=mock_usage)

    mock_client = AsyncMock()

    # noinspection PyUnusedLocal
    async def async_return(*args, **kwargs):
        return mock_completion

    mock_client.chat.completions.create = AsyncMock(side_effect=async_return)

    async def async_commit():
        return None

    with patch(
        "agents.clients.openai_client.AsyncOpenAI", return_value=mock_client
    ), patch.dict(current_app.config, {"OPENAI_API_KEY": "test-key"}), patch(
        "agents.models.db.session.commit", new=async_commit
    ):
        model = AIModel(
            name="GPT-4", provider=Provider.OPENAI, model_id="gpt-4", is_active=True
        )
        db_session.add(model)
        db_session.commit()

        agent = Agent(
            name="Test Agent",
            type=AgentType.RESEARCHER,
            model=model,
            temperature=0.7,
            max_tokens=1000,
            is_active=True,
        )
        db_session.add(agent)
        db_session.commit()

        response = await agent.generate_content("Test prompt")

        assert response == "Generated test content"
        mock_client.chat.completions.create.assert_called_once_with(
            model=model.model_id,
            messages=[
                {"role": "system", "content": "You are a helpful AI assistant."},
                {"role": "user", "content": "Test prompt"},
            ],
            temperature=agent.temperature,
            max_tokens=agent.max_tokens,
        )
