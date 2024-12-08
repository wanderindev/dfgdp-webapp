from unittest.mock import patch

from click.testing import CliRunner
from flask.cli import ScriptInfo

from agents.commands import init_agents
from agents.models import AIModel, Agent, Provider, AgentType

# Test data
TEST_AI_MODELS = [
    {
        "name": "Test GPT-4",
        "provider": Provider.OPENAI,
        "model_id": "gpt-4",
        "description": "Test model",
        "is_active": True,
    }
]

TEST_AGENTS = [
    {
        "name": "Test Agent",
        "type": AgentType.RESEARCHER,
        "description": "Test agent description",
        "model": "Test GPT-4",
        "temperature": 0.7,
        "max_tokens": 1000,
        "prompts": [
            {
                "name": "test_prompt",
                "description": "Test prompt",
                "template": "This is a test prompt for {topic}",
            }
        ],
    }
]


# noinspection PyTypeChecker
def test_init_agents_success(app, db_session):
    """Test successful initialization of agents and models."""
    with patch("agents.commands.INITIAL_AI_MODELS", TEST_AI_MODELS), patch(
        "agents.commands.INITIAL_AGENTS", TEST_AGENTS
    ):
        runner = CliRunner()
        result = runner.invoke(init_agents, obj=ScriptInfo(create_app=lambda info: app))

        assert result.exit_code == 0
        assert "Created AI model: Test GPT-4" in result.output
        assert "Created agent: Test Agent" in result.output

        # Verify database state
        model = AIModel.query.filter_by(name="Test GPT-4").first()
        assert model is not None
        assert model.provider == Provider.OPENAI

        agent = Agent.query.filter_by(name="Test Agent").first()
        assert agent is not None
        assert agent.type == AgentType.RESEARCHER
        assert len(agent.prompts) == 1


# noinspection PyTypeChecker
def test_init_agents_duplicate(app, db_session):
    """Test initialization with existing agents."""
    # First initialization
    with patch("agents.commands.INITIAL_AI_MODELS", TEST_AI_MODELS), patch(
        "agents.commands.INITIAL_AGENTS", TEST_AGENTS
    ):
        runner = CliRunner()
        runner.invoke(init_agents, obj=ScriptInfo(create_app=lambda info: app))

    # Second initialization
    with patch("agents.commands.INITIAL_AI_MODELS", TEST_AI_MODELS), patch(
        "agents.commands.INITIAL_AGENTS", TEST_AGENTS
    ):
        result = runner.invoke(init_agents, obj=ScriptInfo(create_app=lambda info: app))

        assert result.exit_code == 0
        assert "Created AI model" not in result.output  # Should not create duplicate
        assert "Created agent" not in result.output  # Should not create duplicate


# noinspection PyTypeChecker
def test_init_agents_invalid_model_reference(app, db_session):
    """Test initialization with invalid model reference."""
    invalid_agent = TEST_AGENTS.copy()
    invalid_agent[0] = invalid_agent[0].copy()
    invalid_agent[0]["model"] = "NonexistentModel"

    with patch("agents.commands.INITIAL_AI_MODELS", TEST_AI_MODELS), patch(
        "agents.commands.INITIAL_AGENTS", invalid_agent
    ):
        runner = CliRunner()
        result = runner.invoke(init_agents, obj=ScriptInfo(create_app=lambda info: app))

        assert "Error: Model NonexistentModel not found" in result.output


# noinspection PyTypeChecker
def test_init_agents_database_error(app, db_session):
    """Test handling of database errors."""
    with patch("agents.commands.INITIAL_AI_MODELS", TEST_AI_MODELS), patch(
        "agents.commands.INITIAL_AGENTS", TEST_AGENTS
    ), patch(
        "agents.commands.db.session.commit", side_effect=Exception("Database error")
    ):
        runner = CliRunner()
        result = runner.invoke(init_agents, obj=ScriptInfo(create_app=lambda info: app))

        assert "Error: Database error" in result.output
