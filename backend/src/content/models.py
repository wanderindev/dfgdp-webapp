import enum
from datetime import datetime, timezone

from sqlalchemy import func

from extensions import db


# Enums
class ArticleLevel(enum.Enum):
    ELEMENTARY = "elementary"
    MIDDLE_SCHOOL = "middle_school"
    HIGH_SCHOOL = "high_school"
    COLLEGE = "college"
    GENERAL = "general"


class ContentStatus(enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class Platform(enum.Enum):
    INSTAGRAM = "instagram"


# Base class for common fields
class TimestampMixin:
    created_at = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class AIGenerationMixin:
    """Mixin for tracking AI content generation metadata"""

    tokens_used = db.Column(db.Integer, nullable=True)
    model_id = db.Column(db.Integer, db.ForeignKey("ai_models.id"), nullable=True)
    generation_started_at = db.Column(db.DateTime, nullable=True)
    last_generation_error = db.Column(db.Text, nullable=True)


class Taxonomy(db.Model, TimestampMixin):
    """Main content hierarchy"""

    __tablename__ = "taxonomies"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    slug = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=False)

    categories = db.relationship("Category", backref="taxonomy", lazy=True)


class Category(db.Model, TimestampMixin):
    """Sub-categories within taxonomies"""

    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    taxonomy_id = db.Column(db.Integer, db.ForeignKey("taxonomies.id"), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)

    __table_args__ = (
        db.UniqueConstraint(
            "taxonomy_id", "slug", name="unique_category_slug_per_taxonomy"
        ),
    )


class Tag(db.Model, TimestampMixin):
    """Content tags with approval workflow"""

    __tablename__ = "tags"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    slug = db.Column(db.String(50), nullable=False, unique=True)
    status = db.Column(
        db.Enum(ContentStatus), nullable=False, default=ContentStatus.PENDING
    )
    approved_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    approved_at = db.Column(db.DateTime(timezone=True), nullable=True)


article_tags = db.Table(
    "article_tags",
    db.Column("article_id", db.Integer, db.ForeignKey("articles.id"), primary_key=True),
    db.Column("tag_id", db.Integer, db.ForeignKey("tags.id"), primary_key=True),
)

article_relationships = db.Table(
    "article_relationships",
    db.Column("article_id", db.Integer, db.ForeignKey("articles.id"), primary_key=True),
    db.Column(
        "related_article_id", db.Integer, db.ForeignKey("articles.id"), primary_key=True
    ),
)


class ArticleSuggestion(db.Model, TimestampMixin, AIGenerationMixin):
    """Content manager's article suggestions"""

    __tablename__ = "article_suggestions"

    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    main_topic = db.Column(db.Text, nullable=False)
    sub_topics = db.Column(db.ARRAY(db.String(255)), nullable=False)
    point_of_view = db.Column(db.Text, nullable=False)
    level = db.Column(db.Enum(ArticleLevel), nullable=False)
    status = db.Column(
        db.Enum(ContentStatus), nullable=False, default=ContentStatus.PENDING
    )
    approved_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    approved_at = db.Column(db.DateTime(timezone=True), nullable=True)

    category = db.relationship("Category", backref="suggestions")
    research = db.relationship("Research", backref="suggestion", uselist=False)


class Research(db.Model, TimestampMixin, AIGenerationMixin):
    """Research results for article suggestions"""

    __tablename__ = "research"

    id = db.Column(db.Integer, primary_key=True)
    suggestion_id = db.Column(
        db.Integer, db.ForeignKey("article_suggestions.id"), nullable=False
    )
    content = db.Column(db.Text, nullable=False)
    status = db.Column(
        db.Enum(ContentStatus), nullable=False, default=ContentStatus.PENDING
    )
    approved_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    approved_at = db.Column(db.DateTime(timezone=True), nullable=True)


class Article(db.Model, TimestampMixin, AIGenerationMixin):
    """Main article content"""

    __tablename__ = "articles"

    id = db.Column(db.Integer, primary_key=True)
    research_id = db.Column(db.Integer, db.ForeignKey("research.id"), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)

    title = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String(255), nullable=False, unique=True)
    content = db.Column(db.Text, nullable=False)
    excerpt = db.Column(db.Text, nullable=True)
    ai_summary = db.Column(db.Text, nullable=True)
    feature_image_url = db.Column(db.String(255), nullable=True)
    level = db.Column(db.Enum(ArticleLevel), nullable=False)

    status = db.Column(
        db.Enum(ContentStatus), nullable=False, default=ContentStatus.PENDING
    )
    approved_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    approved_at = db.Column(db.DateTime(timezone=True), nullable=True)
    published_at = db.Column(db.DateTime(timezone=True), nullable=True)

    category = db.relationship("Category", backref="articles")
    research = db.relationship("Research", backref="article")
    tags = db.relationship("Tag", secondary=article_tags, backref="articles")
    related_articles = db.relationship(
        "Article",
        secondary=article_relationships,
        primaryjoin=id == article_relationships.c.article_id,
        secondaryjoin=id == article_relationships.c.related_article_id,
        backref="referenced_by",
    )

    @property
    def word_count(self) -> int:
        """Calculate word count from content"""
        return len(self.content.split()) if self.content else 0

    @property
    def relevance_score(self) -> float:
        """Calculate article relevance score"""
        score = 0.0

        # Base score from status
        if self.status == ContentStatus.APPROVED:
            score += 2.0

        # Category relevance
        category_count = (
            db.session.query(func.count(Article.id))
            .filter(Article.category_id == self.category_id)
            .scalar()
        )
        score += min(category_count * 0.5, 5.0)  # Cap at 5.0

        # Tags count (approved tags weight more)
        approved_tags = sum(
            1 for tag in self.tags if tag.status == ContentStatus.APPROVED
        )
        pending_tags = len(self.tags) - approved_tags
        score += (approved_tags * 0.5) + (pending_tags * 0.2)

        # Related articles
        score += len(self.related_articles) * 0.3
        score += len(self.referenced_by) * 0.4  # Being referenced worth more

        # Level scores (adjust weights as needed)
        level_scores = {
            ArticleLevel.ELEMENTARY: 1.0,
            ArticleLevel.MIDDLE_SCHOOL: 2.0,
            ArticleLevel.HIGH_SCHOOL: 3.0,
            ArticleLevel.COLLEGE: 4.0,
            ArticleLevel.GENERAL: 2.0,
        }
        score += level_scores[self.level]

        return score


class SocialMediaAccount(db.Model, TimestampMixin):
    """Connected social media accounts"""

    __tablename__ = "social_media_accounts"

    id = db.Column(db.Integer, primary_key=True)
    platform = db.Column(db.Enum(Platform), nullable=False)
    username = db.Column(db.String(100), nullable=False)
    account_id = db.Column(db.String(100), nullable=False)
    is_active = db.Column(db.Boolean, default=True)

    # Store encrypted credentials securely
    credentials = db.Column(db.JSON, nullable=False)

    __table_args__ = (
        db.UniqueConstraint("platform", "username", name="unique_account_per_platform"),
    )


class SocialMediaPost(db.Model, TimestampMixin, AIGenerationMixin):
    """Generated social media content"""

    __tablename__ = "social_media_posts"

    id = db.Column(db.Integer, primary_key=True)
    article_id = db.Column(db.Integer, db.ForeignKey("articles.id"), nullable=False)
    account_id = db.Column(
        db.Integer, db.ForeignKey("social_media_accounts.id"), nullable=False
    )

    content = db.Column(db.Text, nullable=False)
    hashtags = db.Column(db.ARRAY(db.String(100)), nullable=False, default=list)
    image_url = db.Column(db.String(255), nullable=True)

    status = db.Column(
        db.Enum(ContentStatus), nullable=False, default=ContentStatus.PENDING
    )
    approved_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    approved_at = db.Column(db.DateTime(timezone=True), nullable=True)

    scheduled_for = db.Column(db.DateTime(timezone=True), nullable=True)
    posted_at = db.Column(db.DateTime(timezone=True), nullable=True)
    post_url = db.Column(db.String(255), nullable=True)

    article = db.relationship("Article", backref="social_media_posts")
    account = db.relationship("SocialMediaAccount", backref="posts")

    @property
    def platform(self):
        """Get the platform from the associated account"""
        return self.account.platform if self.account else None
