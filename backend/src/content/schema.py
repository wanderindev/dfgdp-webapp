from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

import strawberry
from flask_login import current_user
from sqlalchemy.orm import joinedload


# Enums
@strawberry.enum
class ContentStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


@strawberry.enum
class ArticleLevel(str, Enum):
    ELEMENTARY = "ELEMENTARY"
    MIDDLE_SCHOOL = "MIDDLE_SCHOOL"
    HIGH_SCHOOL = "HIGH_SCHOOL"
    COLLEGE = "COLLEGE"
    GENERAL = "GENERAL"


@strawberry.enum
class MediaType(str, Enum):
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"
    DOCUMENT = "DOCUMENT"
    PDF = "PDF"
    SPREADSHEET = "SPREADSHEET"
    OTHER = "OTHER"


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
class Research:
    id: int
    suggestion_id: int = strawberry.field(name="suggestionId")
    content: str
    status: ContentStatus
    tokens_used: Optional[int] = None
    approved_by_id: Optional[int] = strawberry.field(name="approvedById")
    approved_at: Optional[datetime] = strawberry.field(name="approvedAt")
    suggestion: "ArticleSuggestion"
    article: Optional["Article"] = strawberry.field(default=None)


@strawberry.type
class ArticleSuggestion:
    id: int
    category_id: int = strawberry.field(name="categoryId")
    title: str
    main_topic: str = strawberry.field(name="mainTopic")
    sub_topics: List[str] = strawberry.field(name="subTopics")
    point_of_view: str = strawberry.field(name="pointOfView")
    level: ArticleLevel
    status: ContentStatus
    approved_by_id: Optional[int] = strawberry.field(name="approvedById")
    approved_at: Optional[datetime] = strawberry.field(name="approvedAt")
    category: Category
    research: Optional[Research] = None


@strawberry.type
class Article:
    id: int
    title: str
    content: str
    excerpt: Optional[str]
    ai_summary: Optional[str]
    level: ArticleLevel
    status: ContentStatus
    research: Research
    category: Category
    tags: List[Tag]
    approved_by_id: Optional[int] = strawberry.field(name="approvedById")
    approved_at: Optional[datetime] = strawberry.field(name="approvedAt")
    published_at: Optional[datetime] = strawberry.field(name="publishedAt")


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
    external_url: Optional[str] = strawberry.field(name="externalUrl")
    width: Optional[int]
    height: Optional[int]
    attribution: Optional[str]
    instagram_media_type: Optional[str] = strawberry.field(name="instagramMediaType")


@strawberry.input
class MediaMetadataInput:
    title: Optional[str]
    caption: Optional[str]
    alt_text: Optional[str] = strawberry.field(name="altText")
    instagram_media_type: Optional[str] = strawberry.field(name="instagramMediaType")


@strawberry.input
class ArticleInput:
    title: str
    content: str
    excerpt: Optional[str]
    ai_summary: Optional[str]
    level: ArticleLevel
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
    level: ArticleLevel


# Queries
# noinspection PyShadowingBuiltins,PyArgumentList
@strawberry.type
class Query:
    @strawberry.field
    def taxonomies(self) -> List[Taxonomy]:
        from content.models import Taxonomy

        return Taxonomy.query.all()

    @strawberry.field
    def taxonomy(self, id: int) -> Optional[Taxonomy]:
        from content.models import Taxonomy

        return Taxonomy.query.get(id)

    @strawberry.field
    def categories(
        self,
        taxonomy_id: Optional[int] = strawberry.field(name="taxonomyId", default=None),
    ) -> List[Category]:
        from content.models import Category

        query = Category.query
        if taxonomy_id:
            query = query.filter_by(taxonomy_id=taxonomy_id)
        return query.all()

    @strawberry.field
    def category(self, id: int) -> Optional[Category]:
        from content.models import Category

        return Category.query.get(id)

    @strawberry.field
    def tags(self, status: Optional[ContentStatus] = None) -> List[Tag]:
        from content.models import Tag

        query = Tag.query
        if status:
            query = query.filter_by(status=status)
        return query.all()

    @strawberry.field
    def tag(self, id: int) -> Optional[Tag]:
        from content.models import Tag

        return Tag.query.get(id)

    @strawberry.field
    def article_suggestions(
        self, status: Optional[ContentStatus] = None
    ) -> List[ArticleSuggestion]:
        """Get article suggestions with optional status filter."""
        from content.models import ArticleSuggestion

        query = ArticleSuggestion.query
        if status:
            query = query.filter_by(status=status)
        query = query.options(joinedload(ArticleSuggestion.research))
        return query.order_by(ArticleSuggestion.created_at.desc()).all()

    @strawberry.field
    def research(self, status: Optional[ContentStatus] = None) -> List[Research]:
        """Get research items with optional status filter."""
        from content.models import Research

        query = Research.query

        if status:
            query = query.filter_by(status=status)

        query = query.options(
            joinedload(Research.suggestion), joinedload(Research.article)
        )

        return query.order_by(Research.created_at.desc()).all()

    @strawberry.field
    def research_item(self, id: int) -> Optional[Research]:
        """Get a specific research item by ID."""
        from content.models import Research

        return Research.query.get_or_404(id)

    @strawberry.field
    def articles(self, status: Optional[ContentStatus] = None) -> List[Article]:
        """Get articles with optional status filter."""
        from content.models import Article

        query = Article.query
        if status:
            query = query.filter_by(status=status)

        query = query.options(
            joinedload(Article.research),
            joinedload(Article.category),
            joinedload(Article.tags),
        )

        return query.order_by(Article.created_at.desc()).all()

    @strawberry.field
    def article(self, id: int) -> Optional[Article]:
        """Get a specific article by ID."""
        from content.models import Article

        return Article.query.get(id)

    @strawberry.field
    def media_suggestions(self) -> List[MediaSuggestion]:
        """Get all media suggestions with their candidates."""
        from content.models import MediaSuggestion
        from sqlalchemy.orm import joinedload

        return (
            MediaSuggestion.query.options(joinedload(MediaSuggestion.research))
            .options(joinedload(MediaSuggestion.candidates))
            .all()
        )

    @strawberry.field
    def media_candidates(
        self, status: Optional[ContentStatus] = None
    ) -> List[MediaCandidate]:
        """Get media candidates with optional status filter."""
        from content.models import MediaCandidate
        from sqlalchemy.orm import joinedload

        query = MediaCandidate.query
        if status:
            query = query.filter_by(status=status)

        return (
            query.options(joinedload(MediaCandidate.suggestion))
            .order_by(MediaCandidate.created_at.desc())
            .all()
        )

    @strawberry.field
    def media_library(self, media_type: Optional[str] = None) -> List[Media]:
        """Get media library items with optional type filter."""
        from content.models import Media, MediaType

        query = Media.query
        if media_type:
            query = query.filter_by(media_type=MediaType(media_type))

        return query.order_by(Media.created_at.desc()).all()


# Mutations
# noinspection PyArgumentList,PyShadowingBuiltins
@strawberry.type
class Mutation:
    @strawberry.mutation
    def create_taxonomy(self, input: TaxonomyInput) -> Taxonomy:
        from content.models import Taxonomy
        from extensions import db

        taxonomy = Taxonomy(name=input.name, description=input.description)
        db.session.add(taxonomy)
        db.session.commit()
        return taxonomy

    @strawberry.mutation
    def update_taxonomy(self, id: int, input: TaxonomyInput) -> Taxonomy:
        from content.models import Taxonomy
        from extensions import db

        taxonomy = Taxonomy.query.get_or_404(id)
        taxonomy.name = input.name
        taxonomy.description = input.description
        db.session.commit()
        return taxonomy

    @strawberry.mutation
    def delete_taxonomy(self, id: int) -> bool:
        from content.models import Taxonomy
        from extensions import db

        taxonomy = Taxonomy.query.get_or_404(id)
        db.session.delete(taxonomy)
        db.session.commit()
        return True

    @strawberry.mutation
    def create_category(self, input: CategoryInput) -> Category:
        from content.models import Category
        from extensions import db

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
        from extensions import db

        category = Category.query.get_or_404(id)
        category.name = input.name
        category.description = input.description
        category.taxonomy_id = input.taxonomy_id
        db.session.commit()
        return category

    @strawberry.mutation
    def delete_category(self, id: int) -> bool:
        from content.models import Category
        from extensions import db

        category = Category.query.get_or_404(id)
        db.session.delete(category)
        db.session.commit()
        return True

    @strawberry.mutation
    def create_tag(self, input: TagInput) -> Tag:
        from content.models import Tag
        from extensions import db

        tag = Tag(name=input.name)
        db.session.add(tag)
        db.session.commit()
        return tag

    @strawberry.mutation
    def update_tag(self, id: int, input: TagInput) -> Tag:
        from content.models import Tag
        from extensions import db

        tag = Tag.query.get_or_404(id)
        tag.name = input.name
        db.session.commit()
        return tag

    @strawberry.mutation
    def update_tag_status(self, id: int, status: ContentStatus) -> Tag:
        from content.models import Tag
        from extensions import db
        from datetime import datetime, timezone

        tag = Tag.query.get_or_404(id)
        tag.status = status
        if status == ContentStatus.APPROVED:
            tag.approved_at = datetime.now(timezone.utc)
            tag.approved_by_id = current_user.id
        db.session.commit()
        return tag

    @strawberry.mutation
    def generate_suggestions(
        self, category_id: int, level: str, count: int = 3
    ) -> List[ArticleSuggestion]:
        """Generate new article suggestions."""
        from content.services import ContentManagerService
        import asyncio

        service = ContentManagerService()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            suggestions = loop.run_until_complete(
                service.generate_suggestions(
                    category_id=category_id, level=level, num_suggestions=count
                )
            )
            return suggestions
        finally:
            loop.close()

    @strawberry.mutation
    def update_suggestion(
        self, id: int, input: ArticleSuggestionInput
    ) -> ArticleSuggestion:
        """Update an existing article suggestion."""
        from content.models import ArticleSuggestion
        from extensions import db

        suggestion = ArticleSuggestion.query.get_or_404(id)
        suggestion.title = input.title
        suggestion.main_topic = input.main_topic
        suggestion.sub_topics = input.sub_topics
        suggestion.point_of_view = input.point_of_view
        suggestion.level = input.level

        db.session.commit()
        return suggestion

    @strawberry.mutation
    def update_suggestion_status(
        self, id: int, status: ContentStatus
    ) -> ArticleSuggestion:
        """Update the status of an article suggestion."""
        from content.models import ArticleSuggestion
        from extensions import db
        from datetime import datetime, timezone

        suggestion = ArticleSuggestion.query.get_or_404(id)
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
    def generate_research(self, suggestion_id: int) -> ArticleSuggestion:
        """Generate research for an approved article suggestion."""
        from content.services import ResearcherService
        from content.models import ArticleSuggestion, ContentStatus
        import asyncio

        suggestion = ArticleSuggestion.query.get_or_404(suggestion_id)
        if suggestion.status != ContentStatus.APPROVED:
            raise ValueError("Can only generate research for approved suggestions")

        service = ResearcherService()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            loop.run_until_complete(
                service.generate_research(suggestion_id=suggestion_id)
            )
            return suggestion
        finally:
            loop.close()

    @strawberry.mutation
    def update_research(self, id: int, content: str) -> Research:
        """Update research content."""
        from content.models import Research
        from extensions import db

        research = Research.query.get_or_404(id)
        research.content = content
        db.session.commit()
        return research

    @strawberry.mutation
    def update_research_status(self, id: int, status: ContentStatus) -> Research:
        """Update research status."""
        from content.models import Research
        from extensions import db

        research = Research.query.get_or_404(id)
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
    def generate_article(self, research_id: int) -> Research:
        """Generate article from approved research."""
        from content.models import Research, ContentStatus
        from content.services import WriterService
        import asyncio

        research = Research.query.get_or_404(research_id)

        if research.status != ContentStatus.APPROVED:
            raise ValueError("Can only generate articles from approved research")

        if research.article:
            raise ValueError("Article already exists for this research")

        # Initialize writer service and use event loop
        service = WriterService()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            loop.run_until_complete(service.generate_article(research_id=research_id))
            return research
        finally:
            loop.close()

    @strawberry.mutation
    def generate_media_suggestions(self, research_id: int) -> Research:
        """Generate media suggestions for approved research."""
        from content.models import Research, ContentStatus
        from content.services import MediaManagerService
        import asyncio

        research = Research.query.get_or_404(research_id)
        if research.status != ContentStatus.APPROVED:
            raise ValueError("Can only generate suggestions for approved research")

        service = MediaManagerService()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            loop.run_until_complete(
                service.generate_suggestions(research_id=research_id)
            )
            return research
        finally:
            loop.close()

    @strawberry.mutation
    def update_article(self, id: int, input: ArticleInput) -> Article:
        """Update article content and metadata."""
        from content.models import Article, Tag
        from extensions import db

        article = Article.query.get_or_404(id)
        article.title = input.title
        article.content = input.content
        article.excerpt = input.excerpt
        article.ai_summary = input.ai_summary
        article.level = input.level

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
        from extensions import db
        from datetime import datetime, timezone

        article = Article.query.get_or_404(id)
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
    def generate_story_promotion(self, article_id: int) -> Article:
        """Generate Instagram story promotion for an article."""
        from content.models import Article, ContentStatus
        from content.services import SocialMediaManagerService
        import asyncio

        article = Article.query.get_or_404(article_id)
        if article.status != ContentStatus.APPROVED:
            raise ValueError("Can only generate promotions for approved articles")

        service = SocialMediaManagerService()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            loop.run_until_complete(
                service.generate_story_promotion(article_id=article_id)
            )
            return article
        finally:
            loop.close()

    @strawberry.mutation
    def generate_did_you_know_posts(self, article_id: int, count: int = 3) -> Article:
        """Generate Instagram feed posts with interesting facts."""
        from content.models import Article, ContentStatus
        from content.services import SocialMediaManagerService
        import asyncio

        article = Article.query.get_or_404(article_id)
        if article.status != ContentStatus.APPROVED:
            raise ValueError("Can only generate posts for approved articles")

        if count < 1 or count > 10:
            raise ValueError("Count must be between 1 and 10")

        service = SocialMediaManagerService()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            loop.run_until_complete(
                service.generate_did_you_know_posts(
                    article_id=article_id, num_posts=count
                )
            )
            return article
        finally:
            loop.close()

    @strawberry.mutation
    def fetch_media_candidates(
        self, suggestion_id: int, max_per_query: int = 20
    ) -> MediaSuggestion:
        """Fetch media candidates from Wikimedia Commons."""
        from content.models import MediaSuggestion
        from content.services import WikimediaService
        from sqlalchemy.orm import joinedload
        import asyncio

        # Create service and event loop for async operation
        async def run_wikimedia_service():
            async with WikimediaService() as service:
                await service.process_suggestion(
                    suggestion_id=suggestion_id, max_per_query=max_per_query
                )

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            loop.run_until_complete(run_wikimedia_service())
            # Refresh the suggestion to get the newly created candidates
            suggestion = MediaSuggestion.query.options(
                joinedload(MediaSuggestion.candidates)
            ).get(suggestion_id)
            return suggestion
        except Exception as e:
            raise ValueError(f"Failed to fetch candidates: {str(e)}")
        finally:
            loop.close()

    @strawberry.mutation
    def update_candidate_status(
        self, id: int, status: ContentStatus, notes: Optional[str] = None
    ) -> MediaCandidate:
        """Update media candidate status."""
        from content.models import MediaCandidate
        from extensions import db
        from datetime import datetime, timezone

        candidate = MediaCandidate.query.get_or_404(id)
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

        candidate = MediaCandidate.query.get_or_404(id)
        media = candidate.approve(current_user.id, notes)

        if not media:
            raise ValueError("Failed to create media entry")

        return candidate

    @strawberry.mutation
    def fetch_media_candidates(
        self, suggestion_id: int, max_per_query: int = 5
    ) -> MediaSuggestion:
        """Fetch media candidates from Wikimedia Commons."""
        from content.models import MediaSuggestion
        from content.services import WikimediaService
        import asyncio

        suggestion = MediaSuggestion.query.get_or_404(suggestion_id)

        # Create service and event loop for async operation
        async def run_service():
            async with WikimediaService() as service:
                return await service.process_suggestion(
                    suggestion_id=suggestion_id, max_per_query=max_per_query
                )

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            loop.run_until_complete(run_service())
            return suggestion
        except Exception as e:
            raise ValueError(f"Failed to fetch candidates: {str(e)}")
        finally:
            loop.close()

    @strawberry.mutation
    def update_media_metadata(self, id: int, input: MediaMetadataInput) -> Media:
        """Update media metadata."""
        from content.models import Media
        from extensions import db

        media = Media.query.get_or_404(id)

        if input.title is not None:
            media.title = input.title
        if input.caption is not None:
            media.caption = input.caption
        if input.alt_text is not None:
            media.alt_text = input.alt_text
        if input.instagram_media_type is not None:
            media.instagram_media_type = input.instagram_media_type

        db.session.commit()
        return media


schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    types=[Taxonomy, Category, Tag, ArticleSuggestion, Research, Article],
)
