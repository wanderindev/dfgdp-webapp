import strawberry
from typing import List, Optional
from enum import Enum
from datetime import datetime
from flask_login import current_user


# Enums
@strawberry.enum
class ContentStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


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
        return query.order_by(ArticleSuggestion.created_at.desc()).all()


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


schema = strawberry.Schema(query=Query, mutation=Mutation)
