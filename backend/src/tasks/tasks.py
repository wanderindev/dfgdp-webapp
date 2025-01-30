import asyncio
import logging
from functools import wraps
from typing import Optional

from rq import get_current_job
from sqlalchemy.orm import Session

from content.models import (
    ArticleSuggestion,
    Research,
    Category,
    ContentStatus,
)
from extensions import db
from services.content_manager_service import ContentManagerService
from services.researcher_service import ResearcherService
from services.writer_service import WriterService

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_DELAY = 5


def create_app_context():
    """Create a new application context for RQ tasks."""
    from app import create_app

    app = create_app()
    return app.app_context()


def async_task(f):
    """Decorator to handle async tasks properly in RQ."""

    @wraps(f)
    def wrapper(*args, **kwargs):
        with create_app_context():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(f(*args, **kwargs))
                return result
            finally:
                loop.close()

    return wrapper


def with_retry(max_retries: int = MAX_RETRIES, delay: int = RETRY_DELAY):
    """Decorator to add retry logic to async operations."""

    def decorator(func):
        @wraps(func)
        async def wrapper(*a, **kw):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return await func(*a, **kw)
                except Exception as e:
                    last_exception = e
                    logger.warning(
                        f"Attempt {attempt + 1} failed for {func.__name__}: {str(e)}"
                    )
                    if attempt < max_retries - 1:
                        await asyncio.sleep(delay)
            raise last_exception

        return wrapper

    return decorator


class TaskProgressTracker:
    """Track progress of long-running tasks."""

    def __init__(self, total_items: int):
        self.total_items = total_items
        self.current_item = 0
        self.job = get_current_job()

    def update_progress(self, message: Optional[str] = None):
        self.current_item += 1
        if self.job:
            progress = (self.current_item / self.total_items) * 100
            self.job.meta["progress"] = progress
            if message:
                self.job.meta["status_message"] = message
            self.job.save_meta()


@async_task
@with_retry()
async def generate_suggestions_task(category_id: int, count: int) -> str:
    """
    RQ task to generate new article suggestions for a given category.
    Uses ContentManagerService in the background.
    """
    logger.info(
        f"generate_suggestions_task started (category_id={category_id}, count={count})"
    )

    try:
        # Track progress: just 1 item in this example
        progress = TaskProgressTracker(total_items=1)
        progress.update_progress("Starting suggestion generation")

        category = db.session.query(Category).get(category_id)
        if not category:
            raise ValueError(f"Category {category_id} not found")

        service = ContentManagerService()
        # Because it's async, call it with await
        suggestions = await service.generate_suggestions(
            category_id=category_id,
            num_suggestions=count,
        )
        db.session.commit()

        logger.info(
            f"Generated {len(suggestions)} suggestions for category {category_id}"
        )

        progress.update_progress("Completed suggestion generation")
        return "Suggestion generation completed"

    except Exception as e:
        logger.error(f"generate_suggestions_task failed: {str(e)}")
        raise


@async_task
@with_retry()
async def generate_research_task(suggestion_id: int) -> str:
    """
    RQ task to generate research content for an approved article suggestion.
    Uses ResearcherService in the background.
    """
    logger.info(f"generate_research_task started (suggestion_id={suggestion_id})")

    try:
        progress = TaskProgressTracker(total_items=1)
        progress.update_progress("Starting research generation")

        suggestion = db.session.query(ArticleSuggestion).get(suggestion_id)
        if not suggestion:
            raise ValueError(f"ArticleSuggestion {suggestion_id} not found")

        if suggestion.status != ContentStatus.APPROVED:
            raise ValueError("Can only generate research for approved suggestions")

        researcher = ResearcherService()
        await researcher.generate_research(suggestion_id=suggestion_id)

        progress.update_progress("Completed research generation")
        logger.info(f"Research generated for suggestion {suggestion.id}")
        return "Research generation completed"

    except Exception as e:
        logger.error(f"generate_research_task failed: {str(e)}")
        raise


@async_task
@with_retry()
async def generate_article_task(research_id: int) -> str:
    """
    RQ task to generate an article (or series) from approved research.
    Uses WriterService in the background.
    """
    logger.info(f"generate_article_task started (research_id={research_id})")

    try:
        progress = TaskProgressTracker(total_items=1)
        progress.update_progress("Starting article generation")

        research = db.session.query(Research).get(research_id)
        if not research:
            raise ValueError(f"Research {research_id} not found")

        if research.status != ContentStatus.APPROVED:
            raise ValueError("Can only generate articles from approved research")

        writer = WriterService()
        await writer.generate_article(research_id=research_id)
        db.session.commit()

        progress.update_progress("Completed article generation")
        logger.info(f"Article generated for research {research.id}")
        return "Article generation completed"

    except Exception as e:
        logger.error(f"generate_article_task failed: {str(e)}")
        raise


# Example: Bulk generation task (already in your code)
@async_task
async def bulk_generation_task():
    """Main task for bulk content generation."""
    logger.info("bulk_generation_task started")

    try:
        # Initialize services
        researcher = ResearcherService()
        writer = WriterService()

        suggestions = (
            db.session.query(ArticleSuggestion)
            .filter(ArticleSuggestion.status == ContentStatus.APPROVED)
            .filter(ArticleSuggestion.research == None)
            .all()
        )

        # Initialize progress tracking
        progress = TaskProgressTracker(len(suggestions))

        for suggestion in suggestions:
            try:
                # Generate and approve research
                await process_suggestion(
                    suggestion, researcher, writer, db.session, progress
                )
            except Exception as e:
                logger.error(f"Failed to process suggestion {suggestion.id}: {str(e)}")
                # Continue with next suggestion instead of failing entire batch
                continue

        return "Bulk generation task completed successfully"

    except Exception as e:
        logger.error(f"Bulk generation task failed: {str(e)}")
        raise


@with_retry()
async def process_suggestion(
    suggestion: ArticleSuggestion,
    researcher: ResearcherService,
    writer: WriterService,
    session: Session,
    progress: TaskProgressTracker,
):
    """Process a single suggestion with retries."""

    # Generate Research
    logger.info(f"Generating research for suggestion {suggestion.id}")
    progress.update_progress(f"Researching suggestion {suggestion.id}")

    research = await researcher.generate_research(suggestion.id)

    # Approve Research
    research.status = ContentStatus.APPROVED
    research.approved_by_id = 1
    research.approved_at = db.func.now()
    session.commit()

    # Generate Article
    logger.info(f"Generating article for research {research.id}")
    progress.update_progress(f"Writing article for research {research.id}")

    await writer.generate_article(research.id)

    progress.update_progress(f"Completed processing suggestion {suggestion.id}")
