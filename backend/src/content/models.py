import enum
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, List

from flask import current_app
from slugify import slugify
from sqlalchemy import event, func
from sqlalchemy.exc import IntegrityError
from werkzeug.utils import secure_filename

from extensions import db
from mixins.mixins import AIGenerationMixin, TimestampMixin
from mixins.mixins import TranslatableMixin


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


class MediaType(enum.Enum):
    IMAGE = "image"
    VIDEO = "video"
    DOCUMENT = "document"
    PDF = "pdf"
    SPREADSHEET = "spreadsheet"
    OTHER = "other"


class MediaSource(enum.Enum):
    LOCAL = "local"
    YOUTUBE = "youtube"
    S3 = "s3"


class Taxonomy(db.Model, TimestampMixin, TranslatableMixin):
    """Main content hierarchy"""

    __tablename__ = "taxonomies"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    slug = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=False)

    categories = db.relationship("Category", backref="taxonomy", lazy=True)


class Category(db.Model, TimestampMixin, TranslatableMixin):
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


# noinspection PyArgumentList
class Tag(db.Model, TimestampMixin, TranslatableMixin):
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

    @staticmethod
    def create_tag(name: str) -> Optional["Tag"]:
        """Create a new tag in pending state."""
        try:
            tag = Tag(name=name, slug=slugify(name), status=ContentStatus.PENDING)
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


# noinspection PyArgumentList
class Media(db.Model, TimestampMixin):
    """Media files management"""

    __tablename__ = "media"

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(512), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)  # Size in bytes
    mime_type = db.Column(db.String(127), nullable=False)
    media_type = db.Column(db.Enum(MediaType), nullable=False)
    source = db.Column(db.Enum(MediaSource), nullable=False)

    # Optional metadata
    title = db.Column(db.String(255), nullable=True)
    caption = db.Column(db.Text, nullable=True)
    alt_text = db.Column(db.String(255), nullable=True)
    external_url = db.Column(db.String(512), nullable=True)  # For YouTube videos

    # Relationships
    feature_for_articles = db.relationship(
        "Article", backref="feature_image", foreign_keys="Article.feature_image_id"
    )
    feature_for_posts = db.relationship(
        "SocialMediaPost", backref="image", foreign_keys="SocialMediaPost.image_id"
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
            return f"[![{self.alt_text or self.title or 'Video thumbnail'}]({self.thumbnail_url})]({self.external_url})"
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


class Article(db.Model, TimestampMixin, AIGenerationMixin, TranslatableMixin):
    """Main article content"""

    __tablename__ = "articles"

    id = db.Column(db.Integer, primary_key=True)
    research_id = db.Column(db.Integer, db.ForeignKey("research.id"), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)
    feature_image_id = db.Column(db.Integer, db.ForeignKey("media.id"), nullable=True)

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

    def upload_feature_image(self, file) -> Optional[Media]:
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


class SocialMediaPost(db.Model, TimestampMixin, AIGenerationMixin, TranslatableMixin):
    """Generated social media content"""

    __tablename__ = "social_media_posts"

    id = db.Column(db.Integer, primary_key=True)
    article_id = db.Column(db.Integer, db.ForeignKey("articles.id"), nullable=False)
    account_id = db.Column(
        db.Integer, db.ForeignKey("social_media_accounts.id"), nullable=False
    )
    image_id = db.Column(db.Integer, db.ForeignKey("media.id"), nullable=True)

    content = db.Column(db.Text, nullable=False)
    hashtags = db.Column(db.ARRAY(db.String(100)), nullable=False, default=list)

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

    def upload_image(self, file) -> Optional[Media]:
        """Upload and set image for social media post"""
        media = Media.create_from_upload(
            file,
            title=f"Social media image for {self.article.title}",
            alt_text=f"Social media image for {self.article.title}",
        )
        if media:
            self.image_id = media.id
            try:
                db.session.commit()
                return media
            except Exception:
                db.session.rollback()
                media.delete()
        return None


@event.listens_for(Media, "after_delete")
def delete_media_file(_mapper, _connection, target):
    if target.source == MediaSource.LOCAL:
        try:
            file_path = Path(target.file_path)
            if file_path.exists():
                file_path.unlink()
        except Exception:
            current_app.logger.error(f"Failed to delete file: {target.file_path}")
