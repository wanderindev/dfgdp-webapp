import enum
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Any

from flask import current_app
from slugify import slugify
from sqlalchemy import event, func, text, Index
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Mapped, relationship, backref
from werkzeug.utils import secure_filename

from extensions import db
from mixins.mixins import AIGenerationMixin, TimestampMixin
from mixins.mixins import TranslatableMixin


# Enums
class ArticleLevel(str, enum.Enum):
    ELEMENTARY = "ELEMENTARY"
    MIDDLE_SCHOOL = "MIDDLE_SCHOOL"
    HIGH_SCHOOL = "HIGH_SCHOOL"
    COLLEGE = "COLLEGE"
    GENERAL = "GENERAL"


class ContentStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class Platform(str, enum.Enum):
    INSTAGRAM = "INSTAGRAM"


class MediaType(str, enum.Enum):
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"
    DOCUMENT = "DOCUMENT"
    PDF = "PDF"
    SPREADSHEET = "SPREADSHEET"
    OTHER = "OTHER"


class MediaSource(str, enum.Enum):
    LOCAL = "LOCAL"
    YOUTUBE = "YOUTUBE"
    S3 = "S3"


class InstagramMediaType(str, enum.Enum):
    SQUARE = "SQUARE"  # 1:1
    PORTRAIT = "PORTRAIT"  # 4:5
    LANDSCAPE = "LANDSCAPE"  # 1.91:1
    STORY = "STORY"  # 9:16
    REEL = "REEL"  # 9:16


class PostType(str, enum.Enum):
    FEED = "FEED"  # Regular feed post (Did You Know?)
    STORY = "STORY"  # Story post (Article Promotion)


class Taxonomy(db.Model, TimestampMixin, TranslatableMixin):
    """Main content hierarchy"""

    __tablename__ = "taxonomies"

    id: Mapped[int] = db.Column(db.Integer, primary_key=True)
    name: Mapped[str] = db.Column(db.String(100), nullable=False, unique=True)
    description: Mapped[str] = db.Column(db.Text, nullable=False)

    categories: Mapped[List["Category"]] = relationship(
        "Category",
        backref="taxonomy",
        lazy=True,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    __table_args__ = (
        Index("idx_taxonomy_name", "name"),
        {"comment": "Main content categorization hierarchy"},
    )

    @property
    def slug(self) -> str:
        """Generate slug from name"""
        return slugify(self.name)


class Category(db.Model, TimestampMixin, TranslatableMixin):
    """Sub-categories within taxonomies"""

    __tablename__ = "categories"

    id: Mapped[int] = db.Column(db.Integer, primary_key=True)
    taxonomy_id: Mapped[int] = db.Column(
        db.Integer,
        db.ForeignKey("taxonomies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = db.Column(db.String(100), nullable=False)
    description: Mapped[str] = db.Column(db.Text, nullable=False)

    __table_args__ = (
        db.UniqueConstraint("taxonomy_id", "name", name="uq_category_taxonomy_name"),
        Index("idx_category_name", "name"),
        {"comment": "Sub-categories within taxonomies"},
    )

    @property
    def slug(self) -> str:
        """Generate slug from name"""
        return slugify(self.name)


# noinspection PyArgumentList
class Tag(db.Model, TimestampMixin, TranslatableMixin):
    """Content tags with approval workflow"""

    __tablename__ = "tags"

    id: Mapped[int] = db.Column(db.Integer, primary_key=True)
    name: Mapped[str] = db.Column(db.String(50), nullable=False, unique=True)
    status: Mapped[ContentStatus] = db.Column(
        db.Enum(ContentStatus, name="content_status_type"),
        nullable=False,
        server_default=text("'PENDING'"),
    )
    approved_by_id: Mapped[Optional[int]] = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    approved_at: Mapped[Optional[datetime]] = db.Column(
        db.DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        Index("idx_tag_status", "status"),
        Index("idx_tag_name", "name"),
        {"comment": "Content categorization tags with approval workflow"},
    )

    @property
    def slug(self) -> str:
        return slugify(self.name)

    @staticmethod
    def create_tag(name: str) -> Optional["Tag"]:
        """Create a new tag in pending state."""
        try:
            tag = Tag(name=name, status=ContentStatus.PENDING)
            db.session.add(tag)
            db.session.commit()
            return tag
        except IntegrityError:
            db.session.rollback()
            return None

    @classmethod
    def get_or_create(cls, name: str) -> Optional["Tag"]:
        """Get an existing tag by name or create a new one if it doesn't exist."""
        tag = cls.query.filter_by(name=name).first()
        if tag:
            return tag

        return cls.create_tag(name)


# Association tables with explicit naming and constraints
article_tags = db.Table(
    "article_tags",
    db.Column(
        "article_id",
        db.Integer,
        db.ForeignKey("articles.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    db.Column(
        "tag_id",
        db.Integer,
        db.ForeignKey("tags.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Index("idx_article_tags_article", "article_id"),
    Index("idx_article_tags_tag", "tag_id"),
)

article_relationships = db.Table(
    "article_relationships",
    db.Column(
        "article_id",
        db.Integer,
        db.ForeignKey("articles.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    db.Column(
        "related_article_id",
        db.Integer,
        db.ForeignKey("articles.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Index("idx_article_relationships_article", "article_id"),
    Index("idx_article_relationships_related", "related_article_id"),
)


class ArticleSuggestion(db.Model, TimestampMixin, AIGenerationMixin):
    """Content manager's article suggestions"""

    __tablename__ = "article_suggestions"

    id: Mapped[int] = db.Column(db.Integer, primary_key=True)
    category_id: Mapped[int] = db.Column(
        db.Integer,
        db.ForeignKey("categories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = db.Column(db.String(255), nullable=False)
    main_topic: Mapped[str] = db.Column(db.Text, nullable=False)
    sub_topics: Mapped[List[str]] = db.Column(
        db.ARRAY(db.String(255)),
        nullable=False,
        server_default=text("ARRAY[]::varchar[]"),
    )
    point_of_view: Mapped[str] = db.Column(db.Text, nullable=False)
    level: Mapped[ArticleLevel] = db.Column(
        db.Enum(ArticleLevel, name="article_level_type"), nullable=False
    )
    status: Mapped[ContentStatus] = db.Column(
        db.Enum(ContentStatus, name="content_status_type"),
        nullable=False,
        server_default=text("'PENDING'"),
    )
    approved_by_id: Mapped[Optional[int]] = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    approved_at: Mapped[Optional[datetime]] = db.Column(
        db.DateTime(timezone=True), nullable=True
    )

    category: Mapped["Category"] = relationship(
        "Category", backref=backref("suggestions", cascade="all, delete-orphan")
    )
    research: Mapped[Optional["Research"]] = relationship(
        "Research",
        backref=backref("suggestion", uselist=False),
        cascade="all, delete-orphan",
        single_parent=True,
    )

    __table_args__ = (
        Index("idx_article_suggestion_status", "status"),
        Index("idx_article_suggestion_level", "level"),
        {"comment": "Article suggestions pending research and development"},
    )


class Research(db.Model, TimestampMixin, AIGenerationMixin):
    """Research results for article suggestions"""

    __tablename__ = "research"

    id: Mapped[int] = db.Column(db.Integer, primary_key=True)
    suggestion_id: Mapped[int] = db.Column(
        db.Integer,
        db.ForeignKey("article_suggestions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    content: Mapped[str] = db.Column(db.Text, nullable=False)
    status: Mapped[ContentStatus] = db.Column(
        db.Enum(ContentStatus, name="content_status_type"),
        nullable=False,
        server_default=text("'PENDING'"),
    )
    approved_by_id: Mapped[Optional[int]] = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    approved_at: Mapped[Optional[datetime]] = db.Column(
        db.DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        Index("idx_research_status", "status"),
        {"comment": "Research content for article suggestions"},
    )


class Article(db.Model, TimestampMixin, AIGenerationMixin, TranslatableMixin):
    """Main article content"""

    __tablename__ = "articles"

    id: Mapped[int] = db.Column(db.Integer, primary_key=True)
    research_id: Mapped[int] = db.Column(
        db.Integer,
        db.ForeignKey("research.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    category_id: Mapped[int] = db.Column(
        db.Integer,
        db.ForeignKey("categories.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    feature_image_id: Mapped[Optional[int]] = db.Column(
        db.Integer, db.ForeignKey("media.id", ondelete="SET NULL"), nullable=True
    )

    title: Mapped[str] = db.Column(db.String(255), nullable=False)
    content: Mapped[str] = db.Column(db.Text, nullable=False)
    excerpt: Mapped[Optional[str]] = db.Column(db.Text, nullable=True)
    ai_summary: Mapped[Optional[str]] = db.Column(db.Text, nullable=True)
    level: Mapped[ArticleLevel] = db.Column(
        db.Enum(ArticleLevel, name="article_level_type"), nullable=False
    )

    status: Mapped[ContentStatus] = db.Column(
        db.Enum(ContentStatus, name="content_status_type"),
        nullable=False,
        server_default=text("'PENDING'"),
    )
    approved_by_id: Mapped[Optional[int]] = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    approved_at: Mapped[Optional[datetime]] = db.Column(
        db.DateTime(timezone=True), nullable=True
    )
    published_at: Mapped[Optional[datetime]] = db.Column(
        db.DateTime(timezone=True), nullable=True
    )

    category: Mapped["Category"] = relationship("Category", backref="articles")
    research: Mapped["Research"] = relationship("Research", backref="article")
    tags: Mapped[List["Tag"]] = relationship(
        "Tag", secondary=article_tags, backref="articles"
    )

    related_articles: Mapped[List["Article"]] = relationship(
        "Article",
        secondary=article_relationships,
        primaryjoin=(id == article_relationships.c.article_id),
        secondaryjoin=(id == article_relationships.c.related_article_id),
        backref=backref("referenced_by", lazy="select"),
    )

    __table_args__ = (
        Index("idx_article_status", "status"),
        Index("idx_article_level", "level"),
        Index("idx_article_published", "published_at"),
        {"comment": "Main article content with translations and relationships"},
    )

    @property
    def slug(self) -> str:
        """Generate slug from title"""
        return slugify(self.title)

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
        if category_count is not None:
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

        return score

    @property
    def public_url(self) -> Optional[str]:
        """Generate the full URL for the article"""
        try:
            base_url = current_app.config["BLOG_URL"].rstrip("/")
            category = self.category
            taxonomy = category.taxonomy
            return f"{base_url}/{taxonomy.slug}/{category.slug}/{self.slug}"
        except Exception as e:
            current_app.logger.error(f"Error generating public url: {str(e)}")
            return None

    def tag_article(self, tag_names: List[str]) -> List[Tag]:
        """Tag the article with provided tag names. Creates new tags if they don't exist."""
        applied_tags = []

        for name in tag_names:
            tag = Tag.get_or_create(name)
            if tag and tag not in self.tags:
                self.tags.append(tag)
                applied_tags.append(tag)

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return []

        return applied_tags

    def upload_feature_image(self, file) -> Optional["Media"]:
        """Upload and set feature image for article"""
        media = Media.create_from_upload(
            file,
            title=f"Feature image for {self.title}",
            alt_text=f"Feature image for {self.title}",
        )
        if media:
            self.feature_image_id = media.id
            try:
                db.session.commit()
                return media
            except Exception:
                db.session.rollback()
                media.delete()
        return None


social_media_post_media = db.Table(
    "social_media_post_media",
    db.Column(
        "post_id",
        db.Integer,
        db.ForeignKey("social_media_posts.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    db.Column(
        "media_id",
        db.Integer,
        db.ForeignKey("media.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    db.Column(
        "position",
        db.Integer,
        nullable=False,
        comment="Order position in carousel, starting from 0",
    ),
    Index("idx_social_media_post_media_post", "post_id"),
    Index("idx_social_media_post_media_position", "post_id", "position", unique=True),
)


# noinspection PyArgumentList
class Media(db.Model, TimestampMixin):
    """Media files management"""

    __tablename__ = "media"

    id: Mapped[int] = db.Column(db.Integer, primary_key=True)
    filename: Mapped[str] = db.Column(db.String(255), nullable=False)
    original_filename: Mapped[str] = db.Column(db.String(255), nullable=False)
    file_path: Mapped[str] = db.Column(db.String(512), nullable=False)
    file_size: Mapped[int] = db.Column(db.Integer, nullable=False)  # Size in bytes
    mime_type: Mapped[str] = db.Column(db.String(127), nullable=False)
    media_type: Mapped[MediaType] = db.Column(
        db.Enum(MediaType, name="media_type_type"), nullable=False
    )
    source: Mapped[MediaSource] = db.Column(
        db.Enum(MediaSource, name="media_source_type"), nullable=False
    )

    # Optional metadata
    title: Mapped[Optional[str]] = db.Column(db.String(255), nullable=True)
    caption: Mapped[Optional[str]] = db.Column(db.Text, nullable=True)
    alt_text: Mapped[Optional[str]] = db.Column(db.String(255), nullable=True)
    external_url: Mapped[Optional[str]] = db.Column(db.String(512), nullable=True)

    # Aspect ratio for images and videos
    width: Mapped[Optional[int]] = db.Column(db.Integer, nullable=True)
    height: Mapped[Optional[int]] = db.Column(db.Integer, nullable=True)
    instagram_media_type: Mapped[Optional[InstagramMediaType]] = db.Column(
        db.Enum(InstagramMediaType, name="instagram_media_type"), nullable=True
    )

    # Relationships
    feature_for_articles: Mapped[List["Article"]] = relationship(
        "Article",
        backref=backref(
            "feature_image",
            uselist=False,
        ),
        foreign_keys="Article.feature_image_id",
        passive_deletes=True,
    )

    __table_args__ = (
        Index("idx_media_type", "media_type"),
        Index("idx_media_source", "source"),
        Index("idx_media_mime_type", "mime_type"),
        {"comment": "Media files with metadata and relationships"},
    )

    @property
    def public_url(self) -> str:
        """Get the URL for accessing the media file"""
        if self.source == MediaSource.YOUTUBE:
            return self.external_url
        elif self.source == MediaSource.LOCAL:
            return f"/media/{self.filename}"
        else:
            return self.file_path

    @property
    def markdown_code(self) -> str:
        """Generate Markdown code for embedding the media"""
        if self.media_type == MediaType.IMAGE:
            md = f"![{self.alt_text or self.title or self.original_filename}]({self.public_url})"
            if self.caption:
                md += f"\n*{self.caption}*"
            return md
        elif self.media_type == MediaType.VIDEO and self.source == MediaSource.YOUTUBE:
            return f"[{self.alt_text or self.title or 'Video'}]({self.external_url})"
        else:
            return (
                f"[Download {self.title or self.original_filename}]({self.public_url})"
            )

    @classmethod
    def create_from_upload(
        cls,
        file,
        title: Optional[str] = None,
        caption: Optional[str] = None,
        alt_text: Optional[str] = None,
    ) -> Optional["Media"]:
        """Create a new Media entry from an uploaded file"""
        if not file:
            return None

        original_filename = secure_filename(file.filename)
        mime_type = file.content_type or "application/octet-stream"

        # Determine media type from mime_type
        media_type = cls._get_media_type(mime_type)

        # Generate unique filename
        filename = cls._generate_unique_filename(original_filename)

        # Create media directory if it doesn't exist
        media_dir = Path(current_app.config["UPLOAD_FOLDER"])
        media_dir.mkdir(exist_ok=True)

        # Save file
        file_path = media_dir / filename
        file.save(str(file_path))

        # Create media entry
        media = cls(
            filename=filename,
            original_filename=original_filename,
            file_path=str(file_path),
            file_size=os.path.getsize(str(file_path)),
            mime_type=mime_type,
            media_type=media_type,
            source=MediaSource.LOCAL,
            title=title,
            caption=caption,
            alt_text=alt_text,
        )

        try:
            db.session.add(media)
            db.session.commit()
            return media
        except Exception:
            if file_path.exists():
                file_path.unlink()
            db.session.rollback()
            return None

    @classmethod
    def create_from_youtube(
        cls, url: str, title: Optional[str] = None, caption: Optional[str] = None
    ) -> Optional["Media"]:
        """Create a new Media entry for a YouTube video"""
        if not url or "youtube.com" not in url and "youtu.be" not in url:
            return None

        media = cls(
            filename=url.split("/")[-1],
            original_filename=url,
            file_path=url,
            file_size=0,  # External resource
            mime_type="video/youtube",
            media_type=MediaType.VIDEO,
            source=MediaSource.YOUTUBE,
            external_url=url,
            title=title,
            caption=caption,
        )

        try:
            db.session.add(media)
            db.session.commit()
            return media
        except Exception:
            db.session.rollback()
            return None

    def update_metadata(
        self,
        title: Optional[str] = None,
        caption: Optional[str] = None,
        alt_text: Optional[str] = None,
    ) -> bool:
        """Update media metadata"""
        try:
            if title is not None:
                self.title = title
            if caption is not None:
                self.caption = caption
            if alt_text is not None:
                self.alt_text = alt_text
            db.session.commit()
            return True
        except Exception:
            db.session.rollback()
            return False

    def delete(self) -> bool:
        """Delete media entry and associated file"""
        try:
            if self.source == MediaSource.LOCAL:
                file_path = Path(self.file_path)
                if file_path.exists():
                    file_path.unlink()

            db.session.delete(self)
            db.session.commit()
            return True
        except Exception:
            db.session.rollback()
            return False

    @staticmethod
    def _get_media_type(mime_type: str) -> MediaType:
        """Determine MediaType from MIME type"""
        if mime_type.startswith("image/"):
            return MediaType.IMAGE
        elif mime_type.startswith("video/"):
            return MediaType.VIDEO
        elif mime_type == "application/pdf":
            return MediaType.PDF
        elif mime_type in [
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ]:
            return MediaType.DOCUMENT
        elif mime_type in [
            "application/vnd.ms-excel",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ]:
            return MediaType.SPREADSHEET
        else:
            return MediaType.OTHER

    @staticmethod
    def _generate_unique_filename(original_filename: str) -> str:
        """Generate unique filename based on timestamp and original filename"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name, ext = os.path.splitext(original_filename)
        return f"{name}_{timestamp}{ext}"


@event.listens_for(Media, "after_delete")
def delete_media_file(_mapper: Any, _connection: Any, target: Media) -> None:
    """Clean up file when media record is deleted"""
    if target.source == MediaSource.LOCAL:
        try:
            file_path = Path(target.file_path)
            if file_path.exists():
                file_path.unlink()
        except Exception as e:
            current_app.logger.error(
                f"Failed to delete file {target.file_path}: {str(e)}"
            )


class SocialMediaAccount(db.Model, TimestampMixin):
    """Connected social media accounts"""

    __tablename__ = "social_media_accounts"

    id: Mapped[int] = db.Column(db.Integer, primary_key=True)
    platform: Mapped[Platform] = db.Column(
        db.Enum(Platform, name="platform_type"), nullable=False
    )
    username: Mapped[str] = db.Column(db.String(100), nullable=False)
    account_id: Mapped[str] = db.Column(db.String(100), nullable=False)
    is_active: Mapped[bool] = db.Column(
        db.Boolean, nullable=False, server_default=text("true")
    )
    credentials: Mapped[dict] = db.Column(
        db.JSON, nullable=False, comment="Encrypted credentials for the platform"
    )

    # Relationships
    posts: Mapped[List["SocialMediaPost"]] = relationship(
        "SocialMediaPost",
        backref="account",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    __table_args__ = (
        db.UniqueConstraint(
            "platform", "username", name="uq_social_media_accounts_platform_username"
        ),
        Index("idx_social_media_account_platform", "platform"),
        Index("idx_social_media_account_active", "is_active"),
        {"comment": "Social media platform accounts configuration"},
    )


class SocialMediaPost(db.Model, TimestampMixin, AIGenerationMixin, TranslatableMixin):
    """Generated social media content with platform-specific constraints.

    Instagram-specific constraints:
    - Caption (content): Maximum 2,200 characters
    - Carousel posts: Maximum 10 images/videos
    - Mentions: Maximum 30 mentions per post
    - Hashtags: While Instagram allows up to 30 hashtags, best practices suggest using 3-15 relevant hashtags
    - Media aspect ratios:
        * Square: 1:1
        * Portrait: 4:5
        * Landscape: 1.91:1
        * Stories/Reels: 9:16

    Post Types:
    - FEED: Regular feed posts (Did You Know?) that remain permanently on the profile
    - STORY: 24-hour stories used for article promotion, can be saved as highlights
    """

    __tablename__ = "social_media_posts"

    id: Mapped[int] = db.Column(db.Integer, primary_key=True)
    article_id: Mapped[int] = db.Column(
        db.Integer,
        db.ForeignKey("articles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    account_id: Mapped[int] = db.Column(
        db.Integer,
        db.ForeignKey("social_media_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    content: Mapped[str] = db.Column(db.Text, nullable=False)
    hashtags: Mapped[List[str]] = db.Column(
        db.ARRAY(db.String(100)),
        nullable=False,
        server_default=text("ARRAY[]::varchar[]"),
    )
    post_type: Mapped[PostType] = db.Column(
        db.Enum(PostType, name="post_type"),
        nullable=False,
        server_default=text("'FEED'"),
    )
    is_highlight: Mapped[bool] = db.Column(
        db.Boolean,
        nullable=False,
        server_default=text("false"),
        comment="Whether this story is saved as a highlight",
    )

    status: Mapped[ContentStatus] = db.Column(
        db.Enum(ContentStatus, name="content_status_type"),
        nullable=False,
        server_default=text("'PENDING'"),
    )
    approved_by_id: Mapped[Optional[int]] = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    approved_at: Mapped[Optional[datetime]] = db.Column(
        db.DateTime(timezone=True), nullable=True
    )

    scheduled_for: Mapped[Optional[datetime]] = db.Column(
        db.DateTime(timezone=True), nullable=True
    )
    posted_at: Mapped[Optional[datetime]] = db.Column(
        db.DateTime(timezone=True), nullable=True
    )
    post_url: Mapped[Optional[str]] = db.Column(db.String(255), nullable=True)

    article: Mapped["Article"] = relationship("Article", backref="social_media_posts")

    media_items: Mapped[List["Media"]] = relationship(
        "Media",
        secondary=social_media_post_media,
        order_by="social_media_post_media.c.position",
        backref=backref(
            "social_media_posts", order_by="social_media_post_media.c.position"
        ),
    )

    __table_args__ = (
        Index("idx_social_media_post_status", "status"),
        Index("idx_social_media_post_scheduled", "scheduled_for"),
        Index("idx_social_media_post_posted", "posted_at"),
        {"comment": "Social media posts with scheduling and tracking"},
    )

    @property
    def aspect_ratio(self) -> Optional[float]:
        """Calculate aspect ratio if dimensions are available."""
        if self.width and self.height:
            return self.width / self.height
        return None

    @property
    def platform(self) -> Optional[Platform]:
        """Get the platform from the associated account"""
        return self.account.platform if self.account else None

    def upload_image(self, file, position: Optional[int] = None) -> Optional[Media]:
        """
        Upload and add an image to the social media post.

        Args:
            file: The image file to upload
            position: Position in carousel (0-based). If None, appends to end.
                     If position is specified and already occupied, shifts existing
                     images to make room.

        Returns:
            Media: The created Media object if successful, None otherwise
        """
        # Create media object
        media = Media.create_from_upload(
            file,
            title=f"Social media image for {self.article.title}",
            alt_text=f"Social media image for {self.article.title}",
        )
        if not media:
            return None

        try:
            # If position not specified, append to end
            if position is None:
                position = len(self.media_items)

            # Validate position
            if position < 0 or position > len(self.media_items):
                raise ValueError("Invalid position")

            # Get the association table
            assoc = social_media_post_media

            # If inserting at existing position, shift other images
            if position < len(self.media_items):
                # Shift existing items starting from the end
                db.session.execute(
                    assoc.update()
                    .where(
                        db.and_(
                            assoc.c.post_id == self.id, assoc.c.position >= position
                        )
                    )
                    .values(position=assoc.c.position + 1)
                )

            # Insert new media at specified position
            db.session.execute(
                assoc.insert().values(
                    post_id=self.id, media_id=media.id, position=position
                )
            )

            db.session.commit()
            return media

        except Exception:
            db.session.rollback()
            media.delete()
            return None

    def remove_image(self, position: int) -> bool:
        """
        Remove an image from the specified carousel position.

        Args:
            position: The position (0-based) of the image to remove

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if position < 0 or position >= len(self.media_items):
                return False

            # Get the association table
            assoc = social_media_post_media

            # Remove the image at specified position
            db.session.execute(
                assoc.delete().where(
                    db.and_(assoc.c.post_id == self.id, assoc.c.position == position)
                )
            )

            # Shift remaining images to fill the gap
            db.session.execute(
                assoc.update()
                .where(db.and_(assoc.c.post_id == self.id, assoc.c.position > position))
                .values(position=assoc.c.position - 1)
            )

            db.session.commit()
            return True

        except Exception:
            db.session.rollback()
            return False

    def reorder_images(self, old_position: int, new_position: int) -> bool:
        """
        Reorder images by moving an image from one position to another.

        Args:
            old_position: Current position of the image (0-based)
            new_position: New desired position (0-based)

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if (
                old_position < 0
                or old_position >= len(self.media_items)
                or new_position < 0
                or new_position >= len(self.media_items)
            ):
                return False

            if old_position == new_position:
                return True

            # Get the association table
            assoc = social_media_post_media

            # Get the media_id being moved
            media_id = self.media_items[old_position].id

            if new_position > old_position:
                # Moving forward: shift items in between backwards
                db.session.execute(
                    assoc.update()
                    .where(
                        db.and_(
                            assoc.c.post_id == self.id,
                            assoc.c.position > old_position,
                            assoc.c.position <= new_position,
                        )
                    )
                    .values(position=assoc.c.position - 1)
                )
            else:
                # Moving backward: shift items in between forward
                db.session.execute(
                    assoc.update()
                    .where(
                        db.and_(
                            assoc.c.post_id == self.id,
                            assoc.c.position >= new_position,
                            assoc.c.position < old_position,
                        )
                    )
                    .values(position=assoc.c.position + 1)
                )

            # Update the moved item's position
            db.session.execute(
                assoc.update()
                .where(
                    db.and_(assoc.c.post_id == self.id, assoc.c.media_id == media_id)
                )
                .values(position=new_position)
            )

            db.session.commit()
            return True

        except Exception:
            db.session.rollback()
            return False

    def format_caption(self) -> str:
        """
        Format the complete caption including content, hashtags, and mentions.
        Returns the formatted caption ready for Instagram.
        """
        parts = [self.content]

        # Add mentions if any
        if self.mentions:
            mentions_text = " ".join(f"@{username}" for username in self.mentions)
            parts.append(mentions_text)

        # Add hashtags if any
        if self.hashtags:
            hashtags_text = " ".join(f"#{tag}" for tag in self.hashtags)
            parts.append(hashtags_text)

        return "\n\n".join(filter(None, parts))

    def validate_instagram_format(self) -> bool:
        """
        Validate if the image meets Instagram's requirements for the specified type.
        Returns False if validation fails.
        """
        if not self.instagram_media_type or not self.width or not self.height:
            return False

        ratio = self.aspect_ratio
        if not ratio:
            return False

        # Check aspect ratio requirements
        if self.instagram_media_type == InstagramMediaType.SQUARE:
            return abs(ratio - 1.0) < 0.01  # Allow small deviation
        elif self.instagram_media_type == InstagramMediaType.PORTRAIT:
            return abs(ratio - 0.8) < 0.01  # 4:5 ratio
        elif self.instagram_media_type == InstagramMediaType.LANDSCAPE:
            return abs(ratio - 1.91) < 0.01  # 1.91:1 ratio
        elif self.instagram_media_type in (
            InstagramMediaType.STORY,
            InstagramMediaType.REEL,
        ):
            return abs(ratio - 0.5625) < 0.01  # 9:16 ratio

        return False


class HashtagGroup(db.Model, TimestampMixin):
    """Groups of related hashtags for social media posts"""

    __tablename__ = "hashtag_groups"

    id: Mapped[int] = db.Column(db.Integer, primary_key=True)
    name: Mapped[str] = db.Column(db.String(100), nullable=False, unique=True)
    hashtags: Mapped[List[str]] = db.Column(
        db.ARRAY(db.String(100)),
        nullable=False,
        server_default=text("ARRAY[]::varchar[]"),
    )
    description: Mapped[str] = db.Column(db.Text, nullable=False)
    is_core: Mapped[bool] = db.Column(
        db.Boolean,
        nullable=False,
        server_default=text("false"),
        comment="Whether this is a core group that should be included in all posts",
    )

    __table_args__ = (
        Index("idx_hashtag_group_name", "name"),
        Index("idx_hashtag_group_core", "is_core"),
        {"comment": "Predefined groups of hashtags for social media posts"},
    )
