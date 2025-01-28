import asyncio
import logging
from functools import wraps
from typing import Optional

from rq import get_current_job
from sqlalchemy.orm import Session

from content.models import ArticleSuggestion, ContentStatus
from extensions import db
from services.researcher_service import ResearcherService
from services.writer_service import WriterService

logger = logging.getLogger(__name__)

# Number of retries for failed operations
MAX_RETRIES = 3
RETRY_DELAY = 5


def create_app_context():
    """Create a new application context for the task."""
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
    """Decorator to add retry logic to operations."""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
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


# noinspection PyTypeChecker
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
