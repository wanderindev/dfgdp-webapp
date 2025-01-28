import asyncio

import click
from flask.cli import AppGroup

from content.models import (
    Category,
    Article,
    ArticleSuggestion,
    Research,
    ContentStatus,
    MediaSuggestion,
)
from extensions import db
from services.content_manager_service import ContentManagerService
from services.media_manager_service import MediaManagerService
from services.researcher_service import ResearcherService
from services.social_media_manager_service import SocialMediaManagerService
from services.wikimedia_service import WikimediaService
from services.writer_service import WriterService

# Create the CLI group
content_cli = AppGroup("content")


@content_cli.command("generate-suggestions")
@click.argument("category_id", type=int)
@click.option(
    "--count",
    "-n",
    default=3,
    help="Number of suggestions to generate",
    type=click.IntRange(1, 15),
)
def generate_suggestions(category_id: int, count: int) -> None:
    """
    Generate article suggestions for a category.
    """
    # Verify category exists
    category = db.session.query(Category).get(category_id)
    if not category:
        click.echo(f"Error: Category {category_id} not found", err=True)
        return

    click.echo(f"Generating {count} suggestions for category: {category.name}")

    try:
        # Initialize service
        service = ContentManagerService()

        # Create event loop for async operation
        loop = asyncio.get_event_loop()

        # Run the async operation
        with click.progressbar(length=count, label="Generating suggestions") as bar:
            suggestions = loop.run_until_complete(
                service.generate_suggestions(
                    category_id=category_id, num_suggestions=count
                )
            )
            bar.update(count)

        # Display results
        click.echo("\nGenerated suggestions:")
        for i, suggestion in enumerate(suggestions, 1):
            click.echo(f"\n{i}. {suggestion.title}")
            click.echo("   " + "-" * len(suggestion.title))
            click.echo(
                f"   Main topic: {suggestion.main_topic if suggestion.main_topic else 'N/A'}"
            )
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
    """
    # Verify suggestion exists
    suggestion = db.session.query(ArticleSuggestion).get(suggestion_id)
    if not suggestion:
        click.echo(f"Error: ArticleSuggestion {suggestion_id} not found", err=True)
        return

    click.echo(f"Generating research for article suggestion: {suggestion.title}")

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


# noinspection DuplicatedCode
@content_cli.command("generate-article")
@click.argument("research_id", type=int)
def generate_article(research_id: int) -> None:
    """
    Generate an article from research content.

    Arguments:
        research_id: ID of the research to use as source
    """
    # Verify research exists and is approved
    research = db.session.query(Research).get(research_id)
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


@content_cli.command("generate-story")
@click.argument("article_id", type=int)
def generate_story(article_id: int) -> None:
    """
    Generate an Instagram Story post to promote an article.

    Arguments:
        article_id: ID of the article to promote
    """
    # Verify article exists
    article = db.session.query(Article).get(article_id)
    if not article:
        click.echo(f"Error: Article {article_id} not found", err=True)
        return

    click.echo(f"Generating Instagram Story promotion for article: {article.title}")

    try:
        # Initialize service
        service = SocialMediaManagerService()

        # Create event loop for async operation
        loop = asyncio.get_event_loop()

        # Run the async operation with progress bar
        with click.progressbar(length=1, label="Generating story") as bar:
            post = loop.run_until_complete(
                service.generate_story_promotion(article_id=article_id)
            )
            bar.update(1)

        # Display results
        click.echo("\nStory generated successfully!")
        click.echo(f"\nContent:")
        click.echo("-" * 40)
        click.echo(post.content)
        click.echo("-" * 40)

        click.echo("\nHashtags:")
        click.echo(", ".join([f"#{tag}" for tag in post.hashtags]))

        click.echo(f"\nStory Link: {article.full_url}")

    except ValueError as e:
        click.echo(f"Error: {str(e)}", err=True)
    except Exception as e:
        click.echo(f"Unexpected error: {str(e)}", err=True)


@content_cli.command("generate-did-you-know")
@click.argument("article_id", type=int)
@click.option(
    "--count",
    "-n",
    default=3,
    help="Number of posts to generate",
    type=click.IntRange(1, 10),
)
def generate_did_you_know(article_id: int, count: int) -> None:
    """
    Generate Instagram feed posts with interesting facts from an article's research.
    """
    # Verify article exists
    article = db.session.query(Article).get(article_id)
    if not article:
        click.echo(f"Error: Article {article_id} not found", err=True)
        return

    click.echo(f"Generating {count} 'Did you know?' posts for article: {article.title}")

    try:
        # Initialize service
        service = SocialMediaManagerService()

        # Create event loop for async operation
        loop = asyncio.get_event_loop()

        # Run the async operation with progress bar
        with click.progressbar(length=count, label="Generating posts") as bar:
            posts = loop.run_until_complete(
                service.generate_did_you_know_posts(
                    article_id=article_id, num_posts=count
                )
            )
            bar.update(count)

        # Display results
        click.echo(f"\nSuccessfully generated {len(posts)} posts:")

        for i, post in enumerate(posts, 1):
            click.echo(f"\n{i}. Did you know post:")
            click.echo("-" * 40)
            click.echo(post.content)
            click.echo("-" * 40)
            click.echo("Hashtags:")
            click.echo(", ".join([f"#{tag}" for tag in post.hashtags]))

    except ValueError as e:
        click.echo(f"Error: {str(e)}", err=True)
    except Exception as e:
        click.echo(f"Unexpected error: {str(e)}", err=True)


# noinspection DuplicatedCode
@content_cli.command("generate-media-suggestions")
@click.argument("research_id", type=int)
def generate_media_suggestions(research_id: int) -> None:
    """
    Generate media suggestions for research content.
    """
    # Verify research exists and is approved
    research = db.session.query(Research).get(research_id)
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

    click.echo(f"Generating media suggestions for research: {suggestion.title}")
    click.echo(f"Category: {suggestion.category.name}")

    try:
        # Initialize service
        service = MediaManagerService()

        # Create event loop for async operation
        loop = asyncio.get_event_loop()

        # Run the async operation with progress bar
        with click.progressbar(length=1, label="Generating suggestions") as bar:
            media_suggestion = loop.run_until_complete(
                service.generate_suggestions(research_id=research_id)
            )
            bar.update(1)

        # Display results
        click.echo("\nSuggestions generated successfully!")
        click.echo("\nWikimedia Commons Categories:")
        click.echo("-" * 40)
        for category in media_suggestion.commons_categories:
            click.echo(f"- {category}")

        click.echo("\nSearch Queries:")
        click.echo("-" * 40)
        for query in media_suggestion.search_queries:
            click.echo(f"- {query}")

        click.echo("\nIllustration Topics:")
        click.echo("-" * 40)
        for topic in media_suggestion.illustration_topics:
            click.echo(f"- {topic}")

        click.echo("\nReasoning:")
        click.echo("-" * 40)
        click.echo(media_suggestion.reasoning)
        click.echo("-" * 40)

    except ValueError as e:
        click.echo(f"Error: {str(e)}", err=True)
    except Exception as e:
        click.echo(f"Unexpected error: {str(e)}", err=True)


@content_cli.command("fetch-media-candidates")
@click.argument("suggestion_id", type=int)
@click.option(
    "--max-per-query",
    "-m",
    default=5,
    help="Maximum images to fetch per query/category",
    type=click.IntRange(1, 20),
)
def fetch_media_candidates(suggestion_id: int, max_per_query: int) -> None:
    """
    Fetch media candidates from Wikimedia Commons for a suggestion.
    """
    # Verify suggestion exists
    suggestion = db.session.query(MediaSuggestion).get(suggestion_id)
    if not suggestion:
        click.echo(f"Error: MediaSuggestion {suggestion_id} not found", err=True)
        return

    click.echo(f"Fetching media candidates for suggestion: {suggestion_id}")
    click.echo(
        f"Processing {len(suggestion.commons_categories)} categories and {len(suggestion.search_queries)} queries"
    )

    async def run_service():
        async with WikimediaService() as service:
            return await service.process_suggestion(
                suggestion_id=suggestion_id, max_per_query=max_per_query
            )

    try:
        # Create event loop for async operation
        loop = asyncio.get_event_loop()

        # Run the async operation with progress bar
        total_items = len(suggestion.commons_categories) + len(
            suggestion.search_queries
        )
        with click.progressbar(length=total_items, label="Fetching candidates") as bar:
            candidates = loop.run_until_complete(run_service())
            bar.update(total_items)

        # Display results
        click.echo(f"\nFetched {len(candidates)} candidates:")

        for candidate in candidates:
            click.echo("\n" + "-" * 40)
            click.echo(f"Title: {candidate.title}")
            click.echo(f"Author: {candidate.author or 'Unknown'}")
            click.echo(f"License: {candidate.license}")
            click.echo(f"Dimensions: {candidate.width}x{candidate.height}")
            click.echo(f"URL: {candidate.commons_url}")

        click.echo("\nUse the admin interface to review and approve candidates.")

    except Exception as e:
        click.echo(f"Error fetching candidates: {str(e)}", err=True)
