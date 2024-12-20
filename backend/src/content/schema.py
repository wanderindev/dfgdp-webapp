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
    approved_by_id: int = strawberry.field(name="approvedById")
    approved_at: datetime = strawberry.field(name="approvedAt")


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


schema = strawberry.Schema(query=Query, mutation=Mutation)
