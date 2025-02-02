from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

import strawberry
from flask_login import current_user
from sqlalchemy import asc, desc
from sqlalchemy.orm import joinedload

from extensions import db
from tasks.config import default_queue
from tasks.tasks import (
    bulk_generation_task,
    generate_article_task,
    generate_research_task,
    generate_suggestions_task,
)


# Enums
@strawberry.enum
class ContentStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


@strawberry.enum
class MediaType(str, Enum):
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"
    DOCUMENT = "DOCUMENT"
    PDF = "PDF"
    SPREADSHEET = "SPREADSHEET"
    OTHER = "OTHER"


@strawberry.enum
class InstagramMediaType(str, Enum):
    SQUARE = "SQUARE"
    PORTRAIT = "PORTRAIT"
    LANDSCAPE = "LANDSCAPE"
    STORY = "STORY"


@strawberry.type
class Category:
    id: int
    name: str
    description: str
    slug: str
    taxonomy_id: int = strawberry.field(name="taxonomyId")
    created_at: datetime = strawberry.field(name="createdAt")
    updated_at: datetime = strawberry.field(name="updatedAt")


@strawberry.type
class Taxonomy:
    id: int
    name: str
    description: str
    slug: str
    created_at: datetime = strawberry.field(name="createdAt")
    updated_at: datetime = strawberry.field(name="updatedAt")
    categories: List[Category]


@strawberry.type
class Tag:
    id: int
    name: str
    status: ContentStatus
    approved_by_id: Optional[int] = strawberry.field(name="approvedById")
    approved_at: Optional[datetime] = strawberry.field(name="approvedAt")


@strawberry.type
class PaginatedTags:
    tags: List[Tag]
    total: int
    pages: int
    current_page: int


@strawberry.type
class Research:
    id: int
    suggestion_id: int = strawberry.field(name="suggestionId")
    content: str
    status: "ContentStatus"  # Replace with your actual ContentStatus enum/type
    approved_by_id: Optional[int] = strawberry.field(name="approvedById")
    approved_at: Optional[datetime] = strawberry.field(name="approvedAt")
    suggestion: "ArticleSuggestion"
    articles: Optional[List["Article"]] = strawberry.field(default=None)


@strawberry.type
class PaginatedResearch:
    research: List[Research]
    total: int
    pages: int
    current_page: int


@strawberry.type
class ArticleSuggestion:
    id: int
    category_id: int = strawberry.field(name="categoryId")
    title: str
    main_topic: Optional[str] = strawberry.field(name="mainTopic")
    sub_topics: Optional[List[str]] = strawberry.field(name="subTopics")
    point_of_view: str = strawberry.field(name="pointOfView")
    status: ContentStatus
    approved_by_id: Optional[int] = strawberry.field(name="approvedById")
    approved_at: Optional[datetime] = strawberry.field(name="approvedAt")
    category: Category
    research: Optional[Research] = None


@strawberry.type
class PaginatedArticleSuggestions:
    suggestions: List[ArticleSuggestion]
    total: int
    pages: int
    current_page: int


@strawberry.type
class Article:
    id: int
    title: str
    content: str
    excerpt: Optional[str]
    ai_summary: Optional[str]
    status: ContentStatus
    research: Research
    category: Category
    tags: List[Tag]
    approved_by_id: Optional[int] = strawberry.field(name="approvedById")
    approved_at: Optional[datetime] = strawberry.field(name="approvedAt")
    published_at: Optional[datetime] = strawberry.field(name="publishedAt")


@strawberry.type
class PaginatedArticles:
    articles: List[Article]
    total: int
    pages: int
    current_page: int


@strawberry.type
class MediaCandidate:
    id: int
    commons_id: str
    commons_url: str
    title: str
    description: Optional[str]
    author: Optional[str]
    license: str
    license_url: Optional[str]
    width: int
    height: int
    mime_type: str
    file_size: int
    status: ContentStatus
    suggestion_id: int = strawberry.field(name="suggestionId")
    suggestion: "MediaSuggestion"
    media_id: Optional[int] = strawberry.field(name="mediaId")


@strawberry.type
class MediaSuggestion:
    id: int
    research_id: int = strawberry.field(name="researchId")
    commons_categories: List[str] = strawberry.field(name="commonsCategories")
    search_queries: List[str] = strawberry.field(name="searchQueries")
    illustration_topics: List[str] = strawberry.field(name="illustrationTopics")
    reasoning: str
    research: Research
    candidates: List[MediaCandidate]


@strawberry.type
class Media:
    id: int
    filename: str
    original_filename: str = strawberry.field(name="originalFilename")
    file_path: str = strawberry.field(name="filePath")
    file_size: int = strawberry.field(name="fileSize")
    mime_type: str = strawberry.field(name="mimeType")
    media_type: str = strawberry.field(name="mediaType")
    source: str
    title: Optional[str]
    caption: Optional[str]
    alt_text: Optional[str] = strawberry.field(name="altText")
    public_url: Optional[str] = strawberry.field(name="publicUrl")
    external_url: Optional[str] = strawberry.field(name="externalUrl")
    width: Optional[int]
    height: Optional[int]
    attribution: Optional[str]
    instagram_media_type: Optional[str] = strawberry.field(name="instagramMediaType")


@strawberry.type
class JobEnqueueResponse:
    success: bool
    message: str


@strawberry.input
class MediaMetadataInput:
    title: Optional[str] = strawberry.field(default=None)
    caption: Optional[str] = strawberry.field(default=None)
    altText: Optional[str] = strawberry.field(name="altText", default=None)
    instagramMediaType: Optional[InstagramMediaType] = strawberry.field(
        name="instagramMediaType", default=None
    )


@strawberry.input
class ArticleInput:
    title: str
    content: str
    excerpt: Optional[str]
    ai_summary: Optional[str]
    tag_ids: List[int] = strawberry.field(name="tagIds")


# Inputs
@strawberry.input
class TaxonomyInput:
    name: str
    description: str


@strawberry.input
class CategoryInput:
    name: str
    description: str
    taxonomy_id: int = strawberry.field(name="taxonomyId")


@strawberry.input
class TagInput:
    name: str


@strawberry.input
class ArticleSuggestionInput:
    title: str
    main_topic: str = strawberry.field(name="mainTopic")
    sub_topics: List[str] = strawberry.field(name="subTopics")
    point_of_view: str = strawberry.field(name="pointOfView")


# Queries
# noinspection PyShadowingBuiltins,PyArgumentList
@strawberry.type
class Query:
    @strawberry.field
    def taxonomies(self) -> List[Taxonomy]:
        from content.models import Taxonomy

        return db.session.query(Taxonomy).order_by(Taxonomy.id).all()

    @strawberry.field
    def taxonomy(self, id: int) -> Optional[Taxonomy]:
        from content.models import Taxonomy

        return db.session.query(Taxonomy).get(id)

    @strawberry.field
    def categories(
        self,
        taxonomy_id: Optional[int] = strawberry.field(name="taxonomyId", default=None),
    ) -> List[Category]:
        from content.models import Category

        query = db.session.query(Category).order_by(Category.id)
        if taxonomy_id:
            query = query.filter_by(taxonomy_id=taxonomy_id)
        return query.all()

    @strawberry.field
    def category(self, id: int) -> Optional[Category]:
        from content.models import Category

        return db.session.query(Category).get(id)

    @strawberry.field
    def tags(
        self,
        page: int = 1,
        page_size: int = 10,
        status: Optional["ContentStatus"] = None,
        search: Optional[str] = None,
        sort: str = "name",
        dir: str = "asc",
    ) -> PaginatedTags:
        from content.models import Tag

        # Define valid columns for sorting
        valid_columns = {"name": Tag.name}
        order_column = valid_columns.get(sort, Tag.name)

        # Build the base query
        query = db.session.query(Tag)

        # Apply filters
        if status:
            query = query.filter_by(status=status)
        if search:
            query = query.filter(Tag.name.ilike(f"%{search}%"))

        # Apply sorting
        query = query.order_by(
            desc(order_column) if dir.lower() == "desc" else asc(order_column)
        )

        # Apply pagination
        pagination = query.paginate(page=page, per_page=page_size, error_out=False)

        return PaginatedTags(
            tags=pagination.items,
            total=pagination.total,
            pages=pagination.pages,
            current_page=page,
        )

    @strawberry.field
    def all_tags(self, status: Optional["ContentStatus"] = None) -> List[Tag]:
        from content.models import Tag

        # Build the query and order by name
        query = db.session.query(Tag).order_by(Tag.name)
        if status:
            query = query.filter_by(status=status)
        return query.all()

    @strawberry.field
    def tag(self, id: int) -> Optional[Tag]:
        from content.models import Tag

        return db.session.query(Tag).get(id)

    @strawberry.field
    def article_suggestions(
        self,
        status: Optional[ContentStatus] = None,
        page: int = 1,
        page_size: int = 10,
        search: Optional[str] = None,
        sort: str = "created_at",
        dir: str = "desc",
    ) -> PaginatedArticleSuggestions:
        """Get paginated article suggestions with optional filtering and sorting."""
        from content.models import ArticleSuggestion

        # Define valid columns for sorting
        valid_columns = {
            "title": ArticleSuggestion.title,
        }
        order_column = valid_columns.get(sort, ArticleSuggestion.title)

        # Build query
        query = db.session.query(ArticleSuggestion)

        # Apply filters
        if status:
            query = query.filter_by(status=status)
        if search:
            query = query.filter((ArticleSuggestion.title.ilike(f"%{search}%")))

        # Apply sorting
        query = query.order_by(
            desc(order_column) if dir.lower() == "desc" else asc(order_column)
        )

        # Eager load relationships
        query = query.options(
            joinedload(ArticleSuggestion.research),
            joinedload(ArticleSuggestion.category),
        )

        # Apply pagination
        pagination = query.paginate(page=page, per_page=page_size, error_out=False)

        return PaginatedArticleSuggestions(
            suggestions=pagination.items,
            total=pagination.total,
            pages=pagination.pages,
            current_page=page,
        )

    @strawberry.field
    def research(
        self,
        page: int = 1,
        page_size: int = 10,
        status: Optional[
            "ContentStatus"
        ] = None,  # Replace with your actual ContentStatus type
        search: Optional[str] = None,
        sort: str = "suggestion.title",
        dir: str = "asc",
    ) -> PaginatedResearch:
        from content.models import Research, ArticleSuggestion

        # Start with a query that joins the suggestion for sorting/filtering by its title.
        query = db.session.query(Research).join(Research.suggestion)

        # Define valid sort keys and map them to actual columns.
        valid_columns = {
            "suggestion.title": ArticleSuggestion.title,
        }
        # Fallback to suggestion.title if provided sort key is not valid.
        order_column = valid_columns.get(sort, ArticleSuggestion.title)

        # Apply filters
        if status:
            query = query.filter(Research.status == status)
        if search:
            query = query.filter(
                (Research.content.ilike(f"%{search}%"))
                | (ArticleSuggestion.title.ilike(f"%{search}%"))
            )

        # Eager load relationships
        query = query.options(
            joinedload(Research.suggestion), joinedload(Research.articles)
        )

        # Apply sorting based on the provided direction
        query = query.order_by(
            desc(order_column) if dir.lower() == "desc" else asc(order_column)
        )

        # Apply pagination
        pagination = query.paginate(page=page, per_page=page_size, error_out=False)

        return PaginatedResearch(
            research=pagination.items,
            total=pagination.total,
            pages=pagination.pages,
            current_page=page,
        )

    @strawberry.field
    def research_item(self, id: int) -> Optional[Research]:
        """Get a specific research item by ID."""
        from content.models import Research

        return db.session.query(Research).get_or_404(id)

    @strawberry.field
    def articles(
        self,
        page: int = 1,
        page_size: int = 10,
        status: Optional["ContentStatus"] = None,
        search: Optional[str] = None,
        sort: str = "title",
        dir: str = "asc",
    ) -> PaginatedArticles:
        from content.models import Article

        # Define valid columns for sorting.
        valid_columns = {
            "title": Article.title,
        }
        order_column = valid_columns.get(sort, Article.title)

        # Build the query
        query = db.session.query(Article)

        # Apply status filter
        if status:
            query = query.filter(Article.status == status)

        # Apply search filter (searching in title and content)
        if search:
            query = query.filter(
                Article.title.ilike(f"%{search}%")
                | Article.content.ilike(f"%{search}%")
            )

        # Eager load relationships
        query = query.options(
            joinedload(Article.research),
            joinedload(Article.category),
            joinedload(Article.tags),
        )

        # Apply sorting based on provided direction
        query = query.order_by(
            desc(order_column) if dir.lower() == "desc" else asc(order_column)
        )

        # Apply pagination
        pagination = query.paginate(page=page, per_page=page_size, error_out=False)

        return PaginatedArticles(
            articles=pagination.items,
            total=pagination.total,
            pages=pagination.pages,
            current_page=page,
        )

    @strawberry.field
    def article(self, id: int) -> Optional[Article]:
        """Get a specific article by ID."""
        from content.models import Article

        return db.session.query(Article).get(id)

    @strawberry.field
    def media_suggestions(self) -> List[MediaSuggestion]:
        """Get all media suggestions with their candidates."""
        from content.models import MediaSuggestion

        return (
            db.session.query(MediaSuggestion)
            .options(joinedload(MediaSuggestion.research))
            .options(joinedload(MediaSuggestion.candidates))
            .all()
        )

    @strawberry.field
    def media_candidates(
        self, status: Optional[ContentStatus] = None
    ) -> List[MediaCandidate]:
        """Get media candidates with optional status filter."""
        from content.models import MediaCandidate

        query = db.session.query(MediaCandidate)
        if status:
            query = query.filter_by(status=status)

        return (
            query.options(joinedload(MediaCandidate.suggestion))
            .order_by(MediaCandidate.created_at.desc())
            .all()
        )

    @strawberry.field
    def media_library(self, media_type: Optional[MediaType] = None) -> List[Media]:
        """Get media library items with optional type filter."""
        from content.models import Media, MediaType as DBMediaType

        query = db.session.query(Media)
        if media_type:
            query = query.filter_by(media_type=DBMediaType[media_type])
        return query.order_by(Media.created_at.desc()).all()


# Mutations
# noinspection PyArgumentList,PyShadowingBuiltins
@strawberry.type
class Mutation:
    @strawberry.mutation
    def create_taxonomy(self, input: TaxonomyInput) -> Taxonomy:
        from content.models import Taxonomy

        taxonomy = Taxonomy(name=input.name, description=input.description)
        db.session.add(taxonomy)
        db.session.commit()
        return taxonomy

    @strawberry.mutation
    def update_taxonomy(self, id: int, input: TaxonomyInput) -> Taxonomy:
        from content.models import Taxonomy

        taxonomy = db.session.query(Taxonomy).get_or_404(id)
        taxonomy.name = input.name
        taxonomy.description = input.description
        db.session.commit()
        return taxonomy

    @strawberry.mutation
    def delete_taxonomy(self, id: int) -> bool:
        from content.models import Taxonomy

        taxonomy = db.session.query(Taxonomy).get_or_404(id)
        db.session.delete(taxonomy)
        db.session.commit()
        return True

    @strawberry.mutation
    def create_category(self, input: CategoryInput) -> Category:
        from content.models import Category

        category = Category(
            name=input.name,
            description=input.description,
            taxonomy_id=input.taxonomy_id,
        )
        db.session.add(category)
        db.session.commit()
        return category

    @strawberry.mutation
    def update_category(self, id: int, input: CategoryInput) -> Category:
        from content.models import Category

        category = db.session.query(Category).get_or_404(id)
        category.name = input.name
        category.description = input.description
        category.taxonomy_id = input.taxonomy_id
        db.session.commit()
        return category

    @strawberry.mutation
    def delete_category(self, id: int) -> bool:
        from content.models import Category

        category = db.session.query(Category).get_or_404(id)
        db.session.delete(category)
        db.session.commit()
        return True

    @strawberry.mutation
    def create_tag(self, input: TagInput) -> Tag:
        from content.models import Tag

        tag = Tag(name=input.name)
        db.session.add(tag)
        db.session.commit()
        return tag

    @strawberry.mutation
    def update_tag(self, id: int, input: TagInput) -> Tag:
        from content.models import Tag

        tag = db.session.query(Tag).get_or_404(id)
        tag.name = input.name
        db.session.commit()
        return tag

    @strawberry.mutation
    def update_tag_status(self, id: int, status: ContentStatus) -> Tag:
        from content.models import Tag

        tag = db.session.query(Tag).get_or_404(id)
        tag.status = status
        if status == ContentStatus.APPROVED:
            tag.approved_at = datetime.now(timezone.utc)
            tag.approved_by_id = current_user.id
        db.session.commit()
        return tag

    @strawberry.mutation
    def generate_suggestions(self, category_id: int, count: int) -> JobEnqueueResponse:
        """Generate new article suggestions."""
        try:
            default_queue.enqueue(generate_suggestions_task, category_id, count)
            return JobEnqueueResponse(success=True, message="Job created successfully")
        except Exception as e:
            return JobEnqueueResponse(
                success=False, message=f"Failed to create job: {str(e)}"
            )

    @strawberry.mutation
    def update_suggestion(
        self, id: int, input: ArticleSuggestionInput
    ) -> ArticleSuggestion:
        """Update an existing article suggestion."""
        from content.models import ArticleSuggestion

        suggestion = db.session.query(ArticleSuggestion).get_or_404(id)
        suggestion.title = input.title
        suggestion.main_topic = input.main_topic
        suggestion.sub_topics = input.sub_topics
        suggestion.point_of_view = input.point_of_view

        db.session.commit()
        return suggestion

    @strawberry.mutation
    def update_suggestion_status(
        self, id: int, status: ContentStatus
    ) -> ArticleSuggestion:
        """Update the status of an article suggestion."""
        from content.models import ArticleSuggestion

        suggestion = db.session.query(ArticleSuggestion).get_or_404(id)
        suggestion.status = status

        if status == ContentStatus.APPROVED:
            suggestion.approved_at = datetime.now(timezone.utc)
            suggestion.approved_by_id = current_user.id
        elif status == ContentStatus.PENDING:
            suggestion.approved_at = None
            suggestion.approved_by_id = None

        db.session.commit()
        return suggestion

    @strawberry.mutation
    def bulk_generate_articles(self, suggestion_id: int) -> JobEnqueueResponse:
        """Bulk generate articles for an approved article suggestion."""
        try:
            default_queue.enqueue(bulk_generation_task)
            return JobEnqueueResponse(success=True, message="Job created successfully")
        except Exception as e:
            return JobEnqueueResponse(
                success=False, message=f"Failed to create job: {str(e)}"
            )

    @strawberry.mutation
    def generate_research(self, suggestion_id: int) -> JobEnqueueResponse:
        """Generate research for an approved article suggestion."""
        from content.models import ArticleSuggestion, ContentStatus

        suggestion = db.session.query(ArticleSuggestion).get_or_404(suggestion_id)
        if suggestion.status != ContentStatus.APPROVED:
            raise ValueError("Can only generate research for approved suggestions")

        try:
            default_queue.enqueue(generate_research_task, suggestion_id)
            return JobEnqueueResponse(success=True, message="Job created successfully")
        except Exception as e:
            return JobEnqueueResponse(
                success=False, message=f"Failed to create job: {str(e)}"
            )

    @strawberry.mutation
    def update_research(self, id: int, content: str) -> Research:
        """Update research content."""
        from content.models import Research

        research = db.session.query(Research).get_or_404(id)
        research.content = content
        db.session.commit()
        return research

    @strawberry.mutation
    def update_research_status(self, id: int, status: ContentStatus) -> Research:
        """Update research status."""
        from content.models import Research

        research = db.session.query(Research).get_or_404(id)
        research.status = status

        if status == ContentStatus.APPROVED:
            research.approved_by_id = current_user.id
            research.approved_at = datetime.now(timezone.utc)
        elif status == ContentStatus.REJECTED:
            research.approved_by_id = None
            research.approved_at = None

        db.session.commit()
        return research

    @strawberry.mutation
    def generate_article(self, research_id: int) -> JobEnqueueResponse:
        """Generate article from approved research."""
        from content.models import Research, ContentStatus

        research = db.session.query(Research).get_or_404(research_id)
        if research.status != ContentStatus.APPROVED:
            raise ValueError("Can only generate articles from approved research")

        try:
            default_queue.enqueue(generate_article_task, research_id)
            return JobEnqueueResponse(success=True, message="Job created successfully")
        except Exception as e:
            return JobEnqueueResponse(
                success=False, message=f"Failed to create job: {str(e)}"
            )

    @strawberry.mutation
    def generate_media_suggestions(self, research_id: int) -> JobEnqueueResponse:
        """Generate media suggestions for approved research."""
        from content.models import Research, ContentStatus

        research = db.session.query(Research).get_or_404(research_id)
        if research.status != ContentStatus.APPROVED:
            raise ValueError("Can only generate suggestions for approved research")

        try:
            # default_queue.enqueue(generate_media_suggestions_task, research_id)
            return JobEnqueueResponse(success=True, message="Job created successfully")
        except Exception as e:
            return JobEnqueueResponse(
                success=False, message=f"Failed to create job: {str(e)}"
            )

    @strawberry.mutation
    def update_article(self, id: int, input: ArticleInput) -> Article:
        """Update article content and metadata."""
        from content.models import Article, Tag

        article = db.session.query(Article).get_or_404(id)
        article.title = input.title
        article.content = input.content
        article.excerpt = input.excerpt
        article.ai_summary = input.ai_summary

        # Update tags
        article.tags = []
        if input.tag_ids:
            tags = Tag.query.filter(Tag.id.in_(input.tag_ids)).all()
            article.tags.extend(tags)

        db.session.commit()
        return article

    @strawberry.mutation
    def update_article_status(self, id: int, status: ContentStatus) -> Article:
        """Update article status."""
        from content.models import Article

        article = db.session.query(Article).get_or_404(id)
        article.status = status

        if status == ContentStatus.APPROVED:
            article.approved_by_id = current_user.id
            article.approved_at = datetime.now(timezone.utc)
        elif status == ContentStatus.PENDING:
            article.approved_by_id = None
            article.approved_at = None

        db.session.commit()
        return article

    @strawberry.mutation
    def generate_story_promotion(self, article_id: int) -> JobEnqueueResponse:
        """Generate Instagram story promotion for an article."""
        from content.models import Article, ContentStatus

        article = db.session.query(Article).get_or_404(article_id)
        if article.status != ContentStatus.APPROVED:
            raise ValueError("Can only generate promotions for approved articles")

        try:
            # default_queue.enqueue(generate_story_promotion_task, research_id)
            return JobEnqueueResponse(success=True, message="Job created successfully")
        except Exception as e:
            return JobEnqueueResponse(
                success=False, message=f"Failed to create job: {str(e)}"
            )

    @strawberry.mutation
    def generate_did_you_know_posts(
        self, article_id: int, count: int = 3
    ) -> JobEnqueueResponse:
        """Generate Instagram feed posts with interesting facts."""
        from content.models import Article, ContentStatus

        article = db.session.query(Article).get_or_404(article_id)
        if article.status != ContentStatus.APPROVED:
            raise ValueError("Can only generate posts for approved articles")

        if count < 1 or count > 10:
            raise ValueError("Count must be between 1 and 10")

        try:
            # default_queue.enqueue(generate_did_you_know_posts_task, article_id, num_posts)
            return JobEnqueueResponse(success=True, message="Job created successfully")
        except Exception as e:
            return JobEnqueueResponse(
                success=False, message=f"Failed to create job: {str(e)}"
            )

    @strawberry.mutation
    def fetch_media_candidates(
        self, suggestion_id: int, max_per_query: int = 20
    ) -> JobEnqueueResponse:
        """Fetch media candidates from Wikimedia Commons."""

        try:
            # default_queue.enqueue(process_media_suggestion_task, suggestion_id, max_per_query)
            return JobEnqueueResponse(success=True, message="Job created successfully")
        except Exception as e:
            return JobEnqueueResponse(
                success=False, message=f"Failed to create job: {str(e)}"
            )

    @strawberry.mutation
    def update_candidate_status(
        self, id: int, status: ContentStatus, notes: Optional[str] = None
    ) -> MediaCandidate:
        """Update media candidate status."""
        from content.models import MediaCandidate

        candidate = db.session.query(MediaCandidate).get_or_404(id)
        candidate.status = status
        candidate.review_notes = notes
        candidate.reviewed_by_id = current_user.id
        candidate.reviewed_at = datetime.now(timezone.utc)

        db.session.commit()
        return candidate

    @strawberry.mutation
    def approve_candidate_and_create_media(
        self, id: int, notes: Optional[str] = None
    ) -> MediaCandidate:
        """Approve candidate and create media entry."""
        from content.models import MediaCandidate

        candidate = db.session.query(MediaCandidate).get_or_404(id)
        media = candidate.approve(current_user.id, notes)

        if not media:
            raise ValueError("Failed to create media entry")

        return candidate

    @strawberry.mutation
    def update_media_metadata(self, id: int, input: MediaMetadataInput) -> Media:
        """Update media metadata."""
        media = db.session.query(Media).get_or_404(id)

        if input.title is not None:
            media.title = input.title
        if input.caption is not None:
            media.caption = input.caption
        if input.altText is not None:
            media.alt_text = input.altText
        if input.instagramMediaType is not None:
            media.instagram_media_type = input.instagramMediaType

        try:
            db.session.commit()
            return media
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Failed to update media metadata: {str(e)}")


schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    types=[Taxonomy, Category, Tag, ArticleSuggestion, Research, Article],
)
