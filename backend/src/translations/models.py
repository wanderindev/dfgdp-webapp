from datetime import datetime
from typing import Optional, List

from sqlalchemy import text, Index
from sqlalchemy.orm import Mapped, relationship

from extensions import db
from mixins.mixins import TimestampMixin


class ApprovedLanguage(db.Model, TimestampMixin):
    """Languages approved for content translation"""

    __tablename__ = "approved_languages"

    id: Mapped[int] = db.Column(db.Integer, primary_key=True)
    code: Mapped[str] = db.Column(db.String(5), nullable=False, unique=True)
    name: Mapped[str] = db.Column(db.String(50), nullable=False, unique=True)
    is_active: Mapped[bool] = db.Column(
        db.Boolean, nullable=False, server_default=text("true")
    )
    is_default: Mapped[bool] = db.Column(
        db.Boolean, nullable=False, server_default=text("false")
    )

    translations: Mapped[List["Translation"]] = relationship(
        "Translation",
        backref="language",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    __table_args__ = (
        Index("idx_language_active", "is_active"),
        Index("idx_language_default", "is_default"),
        Index("idx_language_code", "code"),
        db.CheckConstraint(
            "CASE WHEN is_default THEN is_active ELSE true END",
            name="ck_default_must_be_active",
        ),
        {"comment": "Supported languages for content translation"},
    )

    def __repr__(self) -> str:
        return f"<Language {self.code}>"

    @classmethod
    def get_active_languages(cls) -> List["ApprovedLanguage"]:
        """Get all active languages."""
        return cls.query.filter_by(is_active=True).all()

    @classmethod
    def get_default_language(cls) -> Optional["ApprovedLanguage"]:
        """Get the default language (usually English)."""
        return cls.query.filter_by(is_default=True).first()


class Translation(db.Model, TimestampMixin):
    """Store translations for various content types"""

    __tablename__ = "translations"

    id: Mapped[int] = db.Column(db.Integer, primary_key=True)
    entity_type: Mapped[str] = db.Column(db.String(50), nullable=False)
    entity_id: Mapped[int] = db.Column(db.Integer, nullable=False)
    field: Mapped[str] = db.Column(db.String(50), nullable=False)
    language: Mapped[str] = db.Column(
        db.String(5),
        db.ForeignKey("approved_languages.code", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    content: Mapped[str] = db.Column(db.Text, nullable=False)

    # Track translation generation
    is_generated: Mapped[bool] = db.Column(
        db.Boolean, nullable=False, server_default=text("false")
    )
    generated_at: Mapped[Optional[datetime]] = db.Column(
        db.DateTime(timezone=True), nullable=True
    )
    generated_by_id: Mapped[Optional[int]] = db.Column(
        db.Integer, db.ForeignKey("ai_models.id", ondelete="SET NULL"), nullable=True
    )
    approved_by_id: Mapped[Optional[int]] = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    approved_at: Mapped[Optional[datetime]] = db.Column(
        db.DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        db.UniqueConstraint(
            "entity_type",
            "entity_id",
            "field",
            "language",
            name="uq_translation_entity_field_lang",
        ),
        Index("idx_translation_entity", "entity_type", "entity_id"),
        Index("idx_translation_generated", "is_generated"),
        {"comment": "Content translations with generation tracking"},
    )
