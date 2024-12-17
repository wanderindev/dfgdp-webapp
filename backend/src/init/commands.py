from typing import NoReturn

import click
from flask.cli import AppGroup
from sqlalchemy.exc import IntegrityError

from init.initial_agents import INITIAL_AI_MODELS, INITIAL_AGENTS
from agents.models import AIModel, Agent, PromptTemplate
from init.initial_categories import INITIAL_CATEGORIES
from init.initial_hashtags import INITIAL_HASHTAG_GROUPS
from init.initial_languages import INITIAL_LANGUAGES
from init.initial_social_media_accounts import INITIAL_SOCIAL_MEDIA_ACCOUNTS
from init.initial_tags import INITIAL_TAGS
from init.initial_taxonomies import INITIAL_TAXONOMIES
from content.models import (
    Taxonomy,
    Category,
    ContentStatus,
    SocialMediaAccount,
    HashtagGroup,
    Tag,
)
from extensions import db
from translations.models import ApprovedLanguage

# Create the CLI group
init_cli: AppGroup = AppGroup("init")


# noinspection PyArgumentList
@init_cli.command("agents")
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


# noinspection PyArgumentList
@init_cli.command("taxonomies")
def init_taxonomies() -> None:
    """Initialize taxonomies and categories with default configurations."""
    try:
        # First, create taxonomies
        for taxonomy_data in INITIAL_TAXONOMIES:
            if not Taxonomy.query.filter_by(name=taxonomy_data["name"]).first():
                taxonomy = Taxonomy(**taxonomy_data)
                db.session.add(taxonomy)
                click.echo(
                    f"Created taxonomy: {taxonomy_data['name']} (slug: {taxonomy.slug})"
                )
        db.session.commit()

        # Then create categories
        for category_data in INITIAL_CATEGORIES:
            # Make a copy of the data to avoid modifying the original
            category_dict = category_data.copy()

            # Get the referenced taxonomy
            taxonomy = Taxonomy.query.filter_by(name=category_dict["taxonomy"]).first()
            if not taxonomy:
                click.echo(f"Error: Taxonomy {category_dict['taxonomy']} not found")
                continue

            # Remove taxonomy name from data and add taxonomy_id
            category_dict.pop("taxonomy")
            category_dict["taxonomy_id"] = taxonomy.id

            # Check if category already exists
            if not Category.query.filter_by(
                taxonomy_id=taxonomy.id, name=category_dict["name"]
            ).first():
                category = Category(**category_dict)
                db.session.add(category)
                click.echo(
                    f"Created category: {category_dict['name']} (slug: {category.slug})"
                )

        db.session.commit()
        click.echo("Successfully initialized taxonomies and categories.")

    except IntegrityError as e:
        db.session.rollback()
        click.echo(f"Error: Database integrity error - {str(e)}")
    except Exception as e:
        db.session.rollback()
        click.echo(f"Error: {str(e)}")


# noinspection PyArgumentList
@init_cli.command("tags")
def init_tags() -> None:
    """Initialize tags with sample data."""
    try:
        # Create tags
        for tag_data in INITIAL_TAGS:
            if not Tag.query.filter_by(name=tag_data["name"]).first():
                tag = Tag(
                    name=tag_data["name"], status=ContentStatus[tag_data["status"]]
                )
                db.session.add(tag)
                click.echo(f"Created tag: {tag_data['name']}")

        db.session.commit()
        click.echo("Successfully initialized tags.")

    except IntegrityError as e:
        db.session.rollback()
        click.echo(f"Error: Database integrity error - {str(e)}")
    except Exception as e:
        db.session.rollback()
        click.echo(f"Error: {str(e)}")


# noinspection PyArgumentList
@init_cli.command("social-accounts")
def init_social_accounts() -> None:
    """Initialize social media accounts with default configurations."""
    try:
        # Create social media accounts
        for account_data in INITIAL_SOCIAL_MEDIA_ACCOUNTS:
            if not SocialMediaAccount.query.filter_by(
                platform=account_data["platform"], username=account_data["username"]
            ).first():
                account = SocialMediaAccount(**account_data)
                db.session.add(account)
                click.echo(
                    f"Created social media account: {account_data['username']} "
                    f"({account_data['platform'].value})"
                )

        db.session.commit()
        click.echo("Successfully initialized social media accounts.")

    except IntegrityError as e:
        db.session.rollback()
        click.echo(f"Error: Database integrity error - {str(e)}")
    except Exception as e:
        db.session.rollback()
        click.echo(f"Error: {str(e)}")


# noinspection PyArgumentList
@init_cli.command("hashtags")
def init_hashtags() -> None:
    """Initialize hashtag groups with default configurations."""
    try:
        # Create hashtag groups
        for group_data in INITIAL_HASHTAG_GROUPS:
            if not HashtagGroup.query.filter_by(name=group_data["name"]).first():
                group = HashtagGroup(**group_data)
                db.session.add(group)
                click.echo(
                    f"Created hashtag group: {group_data['name']} "
                    f"({'core' if group_data['is_core'] else 'optional'})"
                )
                click.echo(f"Hashtags: {', '.join(group_data['hashtags'])}\n")

        db.session.commit()
        click.echo("Successfully initialized hashtag groups.")

    except IntegrityError as e:
        db.session.rollback()
        click.echo(f"Error: Database integrity error - {str(e)}")
    except Exception as e:
        db.session.rollback()
        click.echo(f"Error: {str(e)}")


# noinspection PyArgumentList
@init_cli.command("languages")
def init_languages() -> None:
    """Initialize approved languages with default configurations."""
    try:
        # Create languages
        for lang_data in INITIAL_LANGUAGES:
            if not ApprovedLanguage.query.filter_by(code=lang_data["code"]).first():
                lang = ApprovedLanguage(**lang_data)
                db.session.add(lang)
                click.echo(
                    f"Created language: {lang_data['name']} "
                    f"({'default' if lang_data['is_default'] else 'additional'})"
                )

        db.session.commit()
        click.echo("Successfully initialized languages.")

    except IntegrityError as e:
        db.session.rollback()
        click.echo(f"Error: Database integrity error - {str(e)}")
    except Exception as e:
        db.session.rollback()
        click.echo(f"Error: {str(e)}")
