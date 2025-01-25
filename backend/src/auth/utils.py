from typing import Tuple

from auth.models import User, db


# noinspection PyArgumentList
def create_admin_user(email: str, full_name: str, password: str) -> Tuple[bool, str]:
    """Create an admin user if it doesn't exist."""
    if db.session.query(User).filter_by(email=email).first():
        return False, "User already exists"

    try:
        user = User(email=email, full_name=full_name)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return True, "Admin user created successfully"
    except Exception as e:
        db.session.rollback()
        return False, str(e)
