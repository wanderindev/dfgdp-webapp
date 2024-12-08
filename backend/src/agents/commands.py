from typing import NoReturn

import click
from flask.cli import AppGroup
from sqlalchemy.exc import IntegrityError

from extensions import db
from .initial_agents import INITIAL_AI_MODELS, INITIAL_AGENTS
from .models import AIModel, Agent, PromptTemplate

# Create the CLI group
agents_cli: AppGroup = AppGroup("agents")


# noinspection PyArgumentList
@agents_cli.command("init")
def init_agents() -> NoReturn:
    """Initialize AI models and agents with default configurations."""
    try:
        # First, create AI models
        for model_data in INITIAL_AI_MODELS:
            if not AIModel.query.filter_by(name=model_data["name"]).first():
                model = AIModel(**model_data)
                db.session.add(model)
                click.echo(f"Created AI model: {model_data['name']}")
        db.session.commit()

        # Then create agents and their prompt templates
        for agent_data in INITIAL_AGENTS:
            # Get the referenced model
            model = AIModel.query.filter_by(name=agent_data["model"]).first()
            if not model:
                click.echo(f"Error: Model {agent_data['model']} not found")
                continue

            # Check if agent already exists
            if not Agent.query.filter_by(name=agent_data["name"]).first():
                # Create agent
                agent = Agent(
                    name=agent_data["name"],
                    type=agent_data["type"],
                    description=agent_data["description"],
                    model_id=model.id,
                    temperature=agent_data["temperature"],
                    max_tokens=agent_data["max_tokens"],
                )
                db.session.add(agent)
                db.session.commit()

                # Create prompt templates
                for prompt_data in agent_data["prompts"]:
                    template = PromptTemplate(
                        agent_id=agent.id,
                        name=prompt_data["name"],
                        description=prompt_data["description"],
                        template=prompt_data["template"],
                    )
                    db.session.add(template)

                click.echo(f"Created agent: {agent_data['name']}")

        db.session.commit()
        click.echo("Successfully initialized agents and models.")

    except IntegrityError as e:
        db.session.rollback()
        click.echo(f"Error: Database integrity error - {str(e)}")
    except Exception as e:
        db.session.rollback()
        click.echo(f"Error: {str(e)}")
