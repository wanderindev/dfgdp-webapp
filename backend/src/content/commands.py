import asyncio

import click
from flask.cli import AppGroup
from sqlalchemy.exc import IntegrityError

from extensions import db
from .constants import ARTICLE_LEVELS
from .initial_categories import INITIAL_CATEGORIES
from .initial_taxonomies import INITIAL_TAXONOMIES
from .models import Taxonomy, Category, ArticleSuggestion, Research, ContentStatus
from .services import ContentManagerService, ResearcherService, WriterService

# Create the CLI group
content_cli = AppGroup("content")


# noinspection PyArgumentList
@content_cli.command("init-taxonomies")
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


@content_cli.command("list")
def list_content_hierarchy() -> None:
    """List all taxonomies and their categories."""
    taxonomies = Taxonomy.query.all()

    if not taxonomies:
        click.echo("No taxonomies found.")
        return

    for taxonomy in taxonomies:
        click.echo(f"\nTaxonomy: {taxonomy.name}")
        click.echo(f"Description: {taxonomy.description}")
        click.echo("\nCategories:")

        for category in taxonomy.categories:
            click.echo(f"  - {category.name}: {category.description}")


def validate_level(_ctx, _param, value):
    """Validate the level parameter"""
    if value not in ARTICLE_LEVELS:
        valid_levels = ", ".join(ARTICLE_LEVELS.keys())
        raise click.BadParameter(f"Invalid level. Must be one of: {valid_levels}")
    return value


@content_cli.command("generate-suggestions")
@click.argument("category_id", type=int)
@click.argument(
    "level", type=click.Choice(list(ARTICLE_LEVELS.keys()), case_sensitive=False)
)
@click.option(
    "--count",
    "-n",
    default=3,
    help="Number of suggestions to generate",
    type=click.IntRange(1, 10),
)
def generate_suggestions(category_id: int, level: str, count: int) -> None:
    """
    Generate article suggestions for a category.

    Arguments:
        category_id: ID of the category to generate suggestions for
        level: Article level (ELEMENTARY, MIDDLE_SCHOOL, HIGH_SCHOOL, COLLEGE, GENERAL)
        count: Number of suggestions to generate (default: 3)
    """
    # Verify category exists
    category = Category.query.get(category_id)
    if not category:
        click.echo(f"Error: Category {category_id} not found", err=True)
        return

    click.echo(f"Generating {count} suggestions for category: {category.name}")
    click.echo(f"Level: {ARTICLE_LEVELS[level].description}")

    try:
        # Initialize service
        service = ContentManagerService()

        # Create event loop for async operation
        loop = asyncio.get_event_loop()

        # Run the async operation
        with click.progressbar(length=count, label="Generating suggestions") as bar:
            suggestions = loop.run_until_complete(
                service.generate_suggestions(
                    category_id=category_id, level=level, num_suggestions=count
                )
            )
            bar.update(count)

        # Display results
        click.echo("\nGenerated suggestions:")
        for i, suggestion in enumerate(suggestions, 1):
            click.echo(f"\n{i}. {suggestion.title}")
            click.echo("   " + "-" * len(suggestion.title))
            click.echo(f"   Main topic: {suggestion.main_topic}")
            click.echo("   Sub-topics:")
            for sub_topic in suggestion.sub_topics:
                click.echo(f"   - {sub_topic}")
            click.echo(f"   Point of view: {suggestion.point_of_view}")

        click.echo(f"\nSuccessfully generated {len(suggestions)} suggestions.")

    except ValueError as e:
        click.echo(f"Error: {str(e)}", err=True)
    except Exception as e:
        click.echo(f"Unexpected error: {str(e)}", err=True)


@content_cli.command("generate-research")
@click.argument("suggestion_id", type=int)
def generate_research(suggestion_id: int) -> None:
    """
    Generate research content for an article suggestion.

    Arguments:
        suggestion_id: ID of the suggestion to research
    """
    # Verify suggestion exists
    suggestion = ArticleSuggestion.query.get(suggestion_id)
    if not suggestion:
        click.echo(f"Error: ArticleSuggestion {suggestion_id} not found", err=True)
        return

    click.echo(f"Generating research for article suggestion: {suggestion.title}")
    click.echo(f"Level: {suggestion.level.value}")

    try:
        # Initialize service
        service = ResearcherService()

        # Create event loop for async operation
        loop = asyncio.get_event_loop()

        # Run the async operation with progress bar
        with click.progressbar(length=1, label="Generating research") as bar:
            research = loop.run_until_complete(
                service.generate_research(suggestion_id=suggestion_id)
            )
            bar.update(1)

        # Display results
        click.echo("\nResearch generated successfully!")
        click.echo(f"Word count: {len(research.content.split())}")
        click.echo(f"Tokens used: {research.tokens_used}")

        # Show preview of first 200 characters
        preview = (
            research.content[:200] + "..."
            if len(research.content) > 200
            else research.content
        )
        click.echo("\nPreview:")
        click.echo("-" * 40)
        click.echo(preview)
        click.echo("-" * 40)

    except ValueError as e:
        click.echo(f"Error: {str(e)}", err=True)
    except Exception as e:
        click.echo(f"Unexpected error: {str(e)}", err=True)


@content_cli.command("generate-article")
@click.argument("research_id", type=int)
def generate_article(research_id: int) -> None:
    """
    Generate an article from research content.

    Arguments:
        research_id: ID of the research to use as source
    """
    # Verify research exists and is approved
    research = Research.query.get(research_id)
    if not research:
        click.echo(f"Error: Research {research_id} not found", err=True)
        return

    if research.status != ContentStatus.APPROVED:
        click.echo(f"Error: Research {research_id} is not approved", err=True)
        return

    suggestion = research.suggestion
    if not suggestion:
        click.echo(f"Error: No suggestion found for research {research_id}", err=True)
        return

    click.echo(f"Generating article from research: {suggestion.title}")
    click.echo(f"Level: {suggestion.level.value}")
    click.echo(f"Category: {suggestion.category.name}")

    try:
        # Initialize service
        service = WriterService()

        # Create event loop for async operation
        loop = asyncio.get_event_loop()

        # Run the async operation with progress bar
        with click.progressbar(length=1, label="Generating article") as bar:
            article = loop.run_until_complete(
                service.generate_article(research_id=research_id)
            )
            bar.update(1)

        # Display results
        click.echo("\nArticle generated successfully!")
        click.echo(f"Title: {article.title}")
        click.echo(f"Word count: {article.word_count}")
        click.echo(f"Tokens used: {article.tokens_used}")

        # Show excerpt
        click.echo("\nExcerpt:")
        click.echo("-" * 40)
        click.echo(article.excerpt)
        click.echo("-" * 40)

        # Show AI summary
        click.echo("\nAI Summary:")
        click.echo("-" * 40)
        click.echo(article.ai_summary)
        click.echo("-" * 40)

        # Show preview of first 200 characters of main content
        preview = (
            article.content[:200] + "..."
            if len(article.content) > 200
            else article.content
        )
        click.echo("\nContent Preview:")
        click.echo("-" * 40)
        click.echo(preview)
        click.echo("-" * 40)

    except ValueError as e:
        click.echo(f"Error: {str(e)}", err=True)
    except Exception as e:
        click.echo(f"Unexpected error: {str(e)}", err=True)
