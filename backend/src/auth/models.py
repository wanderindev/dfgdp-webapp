from datetime import datetime, timezone
from typing import Optional

from flask_login import UserMixin
from sqlalchemy import text, Index
from sqlalchemy.orm import Mapped
from werkzeug.security import generate_password_hash, check_password_hash

from extensions import db
from mixins.mixins import TimestampMixin


class User(UserMixin, db.Model, TimestampMixin):
    """User model for authentication."""

    __tablename__ = "users"

    id: Mapped[int] = db.Column(db.Integer, primary_key=True)
    email: Mapped[str] = db.Column(
        db.String(120), unique=True, nullable=False, index=True
    )
    full_name: Mapped[str] = db.Column(db.String(100), nullable=False)
    password_hash: Mapped[str] = db.Column(db.String(200), nullable=False)
    active: Mapped[bool] = db.Column(
        db.Boolean, server_default=text("true"), nullable=False
    )
    last_login_at: Mapped[Optional[datetime]] = db.Column(
        db.DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        Index("idx_user_active", "active"),
        Index("idx_user_last_login", "last_login_at"),
        {"comment": "Stores user authentication and profile information"},
    )

    def set_password(self, password: str) -> None:
        """Set the user's password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Check if the provided password matches the hash."""
        return check_password_hash(self.password_hash, password)

    def deactivate(self) -> None:
        """Deactivate the user account."""
        self.active = False

    def reactivate(self) -> None:
        """Reactivate the user account."""
        self.active = True

    def update_last_login(self) -> None:
        """Update the last login timestamp."""
        self.last_login_at = datetime.now(timezone.utc)

    @property
    def is_active(self) -> bool:
        """Required by Flask-Login."""
        return self.active

    def __repr__(self) -> str:
        return f"<User {self.email}>"
