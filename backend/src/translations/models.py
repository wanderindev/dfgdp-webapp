from typing import Optional, List

from extensions import db
from mixins.mixins import TimestampMixin


class ApprovedLanguage(db.Model, TimestampMixin):
    """Languages approved for content translation"""

    __tablename__ = "approved_languages"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(5), nullable=False, unique=True)
    name = db.Column(db.String(50), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    is_default = db.Column(
        db.Boolean, default=False
    )  # Only one default language allowed

    def __repr__(self):
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

    id = db.Column(db.Integer, primary_key=True)
    entity_type = db.Column(db.String(50), nullable=False)
    entity_id = db.Column(db.Integer, nullable=False)
    field = db.Column(db.String(50), nullable=False)
    language = db.Column(db.String(5), nullable=False)
    content = db.Column(db.Text, nullable=False)

    # Track translation generation
    is_generated = db.Column(db.Boolean, default=False)
    generated_at = db.Column(db.DateTime(timezone=True), nullable=True)
    generated_by_id = db.Column(
        db.Integer, db.ForeignKey("ai_models.id"), nullable=True
    )
    approved_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    approved_at = db.Column(db.DateTime(timezone=True), nullable=True)

    __table_args__ = (
        db.UniqueConstraint(
            "entity_type", "entity_id", "field", "language", name="unique_translation"
        ),
        db.ForeignKeyConstraint(
            ["language"], ["approved_languages.code"], name="fk_translation_language"
        ),
    )
