from datetime import datetime
from typing import Optional, List

from sqlalchemy.orm import Mapped

from extensions import db
from mixins.mixins import TimestampMixin


class ApprovedLanguage(db.Model, TimestampMixin):
    """Languages approved for content translation"""

    __tablename__ = "approved_languages"

    id: Mapped[int] = db.Column(db.Integer, primary_key=True)
    code: Mapped[str] = db.Column(db.String(5), nullable=False, unique=True)
    name: Mapped[str] = db.Column(db.String(50), nullable=False)
    is_active: Mapped[bool] = db.Column(db.Boolean, default=True)
    is_default: Mapped[bool] = db.Column(
        db.Boolean, default=False
    )  # Only one default language allowed

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
    language: Mapped[str] = db.Column(db.String(5), nullable=False)
    content: Mapped[str] = db.Column(db.Text, nullable=False)

    # Track translation generation
    is_generated: Mapped[bool] = db.Column(db.Boolean, default=False)
    generated_at: Mapped[Optional[datetime]] = db.Column(
        db.DateTime(timezone=True), nullable=True
    )
    generated_by_id: Mapped[Optional[int]] = db.Column(
        db.Integer, db.ForeignKey("ai_models.id"), nullable=True
    )
    approved_by_id: Mapped[Optional[int]] = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=True
    )
    approved_at: Mapped[Optional[datetime]] = db.Column(
        db.DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        db.UniqueConstraint(
            "entity_type", "entity_id", "field", "language", name="unique_translation"
        ),
        db.ForeignKeyConstraint(
            ["language"], ["approved_languages.code"], name="fk_translation_language"
        ),
    )
