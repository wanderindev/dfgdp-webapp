from datetime import datetime, timezone
from typing import Optional

from flask_login import UserMixin
from sqlalchemy.orm import Mapped
from werkzeug.security import generate_password_hash, check_password_hash

from extensions import db


class User(UserMixin, db.Model):
    """User model for authentication."""

    __tablename__: str = "users"

    id: Mapped[int] = db.Column(db.Integer, primary_key=True)
    email: Mapped[str] = db.Column(
        db.String(120), unique=True, nullable=False, index=True
    )
    full_name: Mapped[str] = db.Column(db.String(100), nullable=False)
    password_hash: Mapped[str] = db.Column(db.String(200), nullable=False)
    active: Mapped[bool] = db.Column(db.Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    last_login_at: Mapped[Optional[datetime]] = db.Column(db.DateTime)

    def set_password(self, password: str) -> None:
        """Set the user's password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Check if the provided password matches the hash."""
        return check_password_hash(self.password_hash, password)

    def __repr__(self) -> str:
        return f"<User {self.email}>"
