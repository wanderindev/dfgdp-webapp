import enum
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Any, Dict

from flask import current_app
from sqlalchemy import event, text, Index
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Mapped, relationship, backref
from werkzeug.utils import secure_filename

from extensions import db
from mixins.mixins import AIGenerationMixin, SlugMixin, TimestampMixin
from mixins.mixins import TranslatableMixin
from translations.models import ApprovedLanguage


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
    WIKIMEDIA = "WIKIMEDIA"


class InstagramMediaType(str, enum.Enum):
    SQUARE = "SQUARE"  # 1:1
    PORTRAIT = "PORTRAIT"  # 4:5
    LANDSCAPE = "LANDSCAPE"  # 1.91:1
    STORY = "STORY"  # 9:16
    REEL = "REEL"  # 9:16


class PostType(str, enum.Enum):
    FEED = "FEED"  # Regular feed post (Did You Know?)
    STORY = "STORY"  # Story post (Article Promotion)


class Taxonomy(db.Model, TimestampMixin, TranslatableMixin, SlugMixin):
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


class Category(db.Model, TimestampMixin, TranslatableMixin, SlugMixin):
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
    is_long_form: Mapped[bool] = db.Column(
        db.Boolean, nullable=False, server_default=text("true")
    )

    __table_args__ = (
        db.UniqueConstraint("taxonomy_id", "name", name="uq_category_taxonomy_name"),
        Index("idx_category_name", "name"),
        {"comment": "Sub-categories within taxonomies"},
    )


# noinspection PyArgumentList
class Tag(db.Model, TimestampMixin, TranslatableMixin, SlugMixin):
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
        tag = db.session.query(cls).filter_by(name=name).first()
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
    main_topic: Mapped[str] = db.Column(db.Text, nullable=True)
    sub_topics: Mapped[List[str]] = db.Column(
        db.ARRAY(db.String(255)),
        nullable=True,
        server_default=text("ARRAY[]::varchar[]"),
    )
    point_of_view: Mapped[str] = db.Column(db.Text, nullable=False)
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

    articles: Mapped[List["Article"]] = relationship(
        "Article", back_populates="research", lazy="select"
    )

    __table_args__ = (
        Index("idx_research_status", "status"),
        {"comment": "Research content for article suggestions"},
    )


class Article(
    db.Model, TimestampMixin, AIGenerationMixin, TranslatableMixin, SlugMixin
):
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
    series_order: Mapped[Optional[int]] = db.Column(
        db.Integer, nullable=True, comment="Order in article series, null if standalone"
    )
    series_parent_id: Mapped[Optional[int]] = db.Column(
        db.Integer,
        db.ForeignKey("articles.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="First article in the series",
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
    research: Mapped["Research"] = relationship(
        "Research",
        back_populates="articles",
    )
    tags: Mapped[List["Tag"]] = relationship(
        "Tag", secondary=article_tags, backref="articles"
    )

    series_parent: Mapped[Optional["Article"]] = relationship(
        "Article",
        remote_side=[id],
        backref=backref(
            "series_articles",
            order_by="Article.series_order",
            cascade="all, delete-orphan",
        ),
    )

    __table_args__ = (
        Index("idx_article_status", "status"),
        Index("idx_article_published", "published_at"),
        Index("idx_article_series", "series_parent_id", "series_order"),
        {"comment": "Main article content with translations and relationships"},
    )

    @property
    def word_count(self) -> int:
        """Calculate word count from content"""
        return len(self.content.split()) if self.content else 0

    @property
    def public_url(self) -> Optional[str]:
        """
        Generate the full URL for the article using the default language.
        Pattern: {base_url}/{language_code}/{taxonomy_slug}/{category_slug}/{article_slug}
        """
        try:
            base_url = current_app.config["BLOG_URL"].rstrip("/")

            default_lang = ApprovedLanguage.get_default_language()
            if not default_lang:
                current_app.logger.error("No default language configured")
                return None

            category = self.category
            taxonomy = category.taxonomy

            # Generate URL with default language code
            return f"{base_url}/{default_lang.code}/{taxonomy.slug}/{category.slug}/{self.slug}"

        except Exception as e:
            current_app.logger.error(f"Error generating public url: {str(e)}")
            return None

    @property
    def is_series(self) -> bool:
        """Check if article is part of a series."""
        return bool(self.series_parent_id or self.series_articles)

    @property
    def is_series_parent(self) -> bool:
        """Check if article is the first in a series."""
        return bool(self.series_articles)

    @property
    def full_series(self) -> List["Article"]:
        """Get all articles in the series, ordered."""
        if self.is_series_parent:
            return [self] + self.series_articles
        elif self.series_parent:
            return [self.series_parent] + [
                a for a in self.series_parent.series_articles if a.id != self.id
            ]
        return [self]

    @property
    def next_in_series(self) -> Optional["Article"]:
        """Get next article in series if it exists."""
        if not self.is_series:
            return None

        if self.is_series_parent:
            return self.series_articles[0] if self.series_articles else None

        parent = self.series_parent
        if not parent:
            return None

        series = parent.full_series
        try:
            current_index = series.index(self)
            return (
                series[current_index + 1] if current_index < len(series) - 1 else None
            )
        except ValueError:
            return None

    @property
    def previous_in_series(self) -> Optional["Article"]:
        """Get previous article in series if it exists."""
        if not self.is_series:
            return None

        if self.is_series_parent:
            return None

        parent = self.series_parent
        if not parent:
            return None

        series = parent.full_series
        try:
            current_index = series.index(self)
            return series[current_index - 1] if current_index > 0 else None
        except ValueError:
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


class MediaSuggestion(db.Model, TimestampMixin, AIGenerationMixin):
    """AI-generated suggestions for media content"""

    __tablename__ = "media_suggestions"

    id: Mapped[int] = db.Column(db.Integer, primary_key=True)
    research_id: Mapped[int] = db.Column(
        db.Integer,
        db.ForeignKey("research.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Suggested search parameters
    commons_categories: Mapped[List[str]] = db.Column(
        db.ARRAY(db.String(255)),
        nullable=False,
        server_default=text("ARRAY[]::varchar[]"),
        comment="Suggested Wikimedia Commons categories",
    )
    search_queries: Mapped[List[str]] = db.Column(
        db.ARRAY(db.String(255)),
        nullable=False,
        server_default=text("ARRAY[]::varchar[]"),
        comment="Suggested search queries",
    )
    illustration_topics: Mapped[List[str]] = db.Column(
        db.ARRAY(db.String(255)),
        nullable=False,
        server_default=text("ARRAY[]::varchar[]"),
        comment="Key topics needing illustration",
    )

    # Rationale for suggestions
    reasoning: Mapped[str] = db.Column(
        db.Text, nullable=False, comment="AI's explanation for suggestions"
    )

    # Relationships
    research: Mapped["Research"] = relationship("Research", backref="media_suggestions")
    candidates: Mapped[List["MediaCandidate"]] = relationship(
        "MediaCandidate", backref="suggestion", cascade="all, delete-orphan"
    )

    __table_args__ = (Index("idx_media_suggestion_research", "research_id"),)


# noinspection PyArgumentList,PyAttributeOutsideInit,PyUnboundLocalVariable
class MediaCandidate(db.Model, TimestampMixin):
    """Potential media items found from suggestions"""

    __tablename__ = "media_candidates"

    id: Mapped[int] = db.Column(db.Integer, primary_key=True)
    suggestion_id: Mapped[int] = db.Column(
        db.Integer,
        db.ForeignKey("media_suggestions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Wikimedia Commons metadata
    commons_id: Mapped[str] = db.Column(db.String(255), nullable=False)
    commons_url: Mapped[str] = db.Column(db.String(512), nullable=False)
    title: Mapped[str] = db.Column(db.String(255), nullable=False)
    description: Mapped[str] = db.Column(db.Text, nullable=True)
    author: Mapped[str] = db.Column(db.String(255), nullable=True)
    license: Mapped[str] = db.Column(db.String(100), nullable=False)
    license_url: Mapped[str] = db.Column(db.String(512), nullable=True)

    # Image metadata
    width: Mapped[int] = db.Column(db.Integer, nullable=False)
    height: Mapped[int] = db.Column(db.Integer, nullable=False)
    mime_type: Mapped[str] = db.Column(db.String(50), nullable=False)
    file_size: Mapped[int] = db.Column(db.Integer, nullable=False)

    # Local status
    status: Mapped[ContentStatus] = db.Column(
        db.Enum(ContentStatus, name="content_status_type"),
        nullable=False,
        server_default=text("'PENDING'"),
    )
    review_notes: Mapped[Optional[str]] = db.Column(db.Text, nullable=True)
    reviewed_by_id: Mapped[Optional[int]] = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    reviewed_at: Mapped[Optional[datetime]] = db.Column(
        db.DateTime(timezone=True), nullable=True
    )

    # Cache management
    thumbnail_path: Mapped[Optional[str]] = db.Column(db.String(512), nullable=True)
    cached_at: Mapped[Optional[datetime]] = db.Column(
        db.DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        Index("idx_media_candidate_suggestion", "suggestion_id"),
        Index("idx_media_candidate_status", "status"),
        db.UniqueConstraint(
            "suggestion_id", "commons_id", name="uq_media_candidate_commons"
        ),
    )

    @property
    def aspect_ratio(self) -> float:
        """Calculate aspect ratio"""
        return self.width / self.height if self.height else 0

    def approve(self, user_id: int, notes: Optional[str] = None) -> Optional["Media"]:
        """
        Approve candidate and create Media entry
        """
        try:
            # First make sure the upload directory exists
            media_dir = Path(current_app.config["UPLOAD_FOLDER"])
            try:
                media_dir.mkdir(exist_ok=True)
            except (PermissionError, OSError) as e:
                current_app.logger.error(f"Failed to create upload directory: {str(e)}")
                return None

            # Generate unique filename for local storage
            filename = self.commons_id
            if filename.startswith("File:"):
                filename = filename[5:]
            filename = secure_filename(filename)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            name, ext = os.path.splitext(filename)
            local_filename = f"{name}_{timestamp}{ext}"
            file_path = media_dir / local_filename

            # Download file from Wikimedia
            try:
                import aiohttp
                import asyncio

                async def download_file():
                    async with aiohttp.ClientSession() as session:
                        async with session.get(self.commons_url) as response:
                            if response.status != 200:
                                raise ValueError(
                                    f"Failed to download file: {response.status}"
                                )
                            with open(file_path, "wb") as f:
                                f.write(await response.read())

                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(download_file())
                finally:
                    loop.close()

            except Exception as e:
                current_app.logger.error(f"Failed to download file from Commons: {e}")
                if file_path.exists():
                    file_path.unlink()
                return None

            # Create Media entry
            media = Media(
                title=self.title,
                filename=local_filename,
                original_filename=self.commons_id,
                file_path=str(file_path),
                file_size=self.file_size,
                mime_type=self.mime_type,
                media_type=MediaType.IMAGE,
                source=MediaSource.WIKIMEDIA,
                source_url=self.commons_url,
                width=self.width,
                height=self.height,
                caption=self.description,
                attribution=f"Author: {self.author}\nLicense: {self.license}",
                license_url=self.license_url,
                commons_id=self.commons_id,
            )
            db.session.add(media)

            # Update candidate status
            self.status = ContentStatus.APPROVED
            self.review_notes = notes
            self.reviewed_by_id = user_id
            self.reviewed_at = datetime.now(timezone.utc)
            self.media_id = media.id

            db.session.commit()
            return media

        except Exception as e:
            current_app.logger.error(f"Error approving media candidate: {e}")
            db.session.rollback()
            if "file_path" in locals() and file_path.exists():
                file_path.unlink()  # Clean up file if it was created
            return None

    def reject(self, user_id: int, notes: Optional[str] = None) -> bool:
        """Reject candidate"""
        try:
            self.status = ContentStatus.REJECTED
            self.review_notes = notes
            self.reviewed_by_id = user_id
            self.reviewed_at = datetime.now(timezone.utc)

            db.session.commit()
            return True

        except Exception as e:
            current_app.logger.error(f"Error rejecting media candidate: {e}")
            db.session.rollback()
            return False


# noinspection PyArgumentList
class Media(db.Model, TimestampMixin, TranslatableMixin):
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

    # Licensing information
    license: Mapped[Optional[str]] = db.Column(
        db.String(100), nullable=True, comment="License type (e.g., CC BY-SA 4.0)"
    )
    license_url: Mapped[Optional[str]] = db.Column(
        db.String(512), nullable=True, comment="URL to license details"
    )
    attribution: Mapped[Optional[str]] = db.Column(
        db.Text, nullable=True, comment="Required attribution text"
    )
    source_url: Mapped[Optional[str]] = db.Column(
        db.String(512), nullable=True, comment="Original source URL"
    )
    commons_id: Mapped[Optional[str]] = db.Column(
        db.String(255), nullable=True, comment="Wikimedia Commons file identifier"
    )

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
        Index("idx_media_commons_id", "commons_id"),
        {"comment": "Media files with metadata, licensing, and relationships"},
    )

    @property
    def public_url(self) -> str:
        """Get the URL for accessing the media file"""
        if self.source == MediaSource.YOUTUBE:
            return self.external_url
        elif self.source in [MediaSource.LOCAL, MediaSource.WIKIMEDIA]:
            return f"/content/uploads/{os.path.basename(self.file_path)}"
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

    @property
    def attribution_html(self) -> Optional[str]:
        """Generate HTML attribution string"""
        if not self.attribution:
            return None

        attribution = self.attribution
        if self.license and self.license_url:
            attribution += (
                f' Licensed under <a href="{self.license_url}">{self.license}</a>'
            )
        if self.source_url:
            attribution = f'<a href="{self.source_url}">{attribution}</a>'

        return attribution

    @property
    def attribution_markdown(self) -> Optional[str]:
        """Generate Markdown attribution string"""
        if not self.attribution:
            return None

        attribution = self.attribution
        if self.license and self.license_url:
            attribution += f" Licensed under [{self.license}]({self.license_url})"
        if self.source_url:
            attribution = f"[{attribution}]({self.source_url})"

        return attribution

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

        try:
            # Create media directory if it doesn't exist
            media_dir = Path(current_app.config["UPLOAD_FOLDER"])
            try:
                media_dir.mkdir(exist_ok=True)
            except (PermissionError, OSError) as e:
                current_app.logger.error(f"Failed to create upload directory: {str(e)}")
                return None

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

        except Exception as e:
            current_app.logger.error(f"Error creating media from upload: {str(e)}")
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

    def set_wikimedia_metadata(self, commons_data: Dict[str, Any]) -> bool:
        """
        Update media metadata from Wikimedia Commons data
        """
        try:
            self.commons_id = commons_data.get("title")
            self.source_url = commons_data.get("url")
            self.license = commons_data.get("license")
            self.license_url = commons_data.get("license_url")
            self.attribution = commons_data.get("attribution")
            self.source = MediaSource.WIKIMEDIA

            if "width" in commons_data:
                self.width = commons_data["width"]
            if "height" in commons_data:
                self.height = commons_data["height"]

            db.session.commit()
            return True

        except Exception as e:
            current_app.logger.error(f"Error updating Wikimedia metadata: {e}")
            db.session.rollback()
            return False

    def get_attribution_text(self, format_: str = "html") -> Optional[str]:
        """
        Get properly formatted attribution text
        """
        if format_ == "html":
            return self.attribution_html
        elif format_ == "markdown":
            return self.attribution_markdown
        else:
            return self.attribution


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
    """
    Generated social media content with platform-specific constraints.
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
        Format the complete caption including content and hashtags.
        Returns the formatted caption ready for Instagram.
        """
        parts = [self.content]

        # Add hashtags if any
        if self.hashtags:
            hashtags_text = " ".join(f"#{tag}" for tag in self.hashtags)
            parts.append(hashtags_text)

        return "\n\n".join(filter(None, parts))

    def validate_instagram_format(self) -> bool:
        """
        Validate the Instagram-specific requirements for all media items in this post.
        Returns True if all media items meet the requirements, otherwise False.
        """
        for media in self.media_items:
            if not media.instagram_media_type:
                return False
        return True


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
