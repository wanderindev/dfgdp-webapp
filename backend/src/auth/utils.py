from .models import User, db


def create_admin_user(email, full_name, password):
    """Create an admin user if it doesn't exist."""
    if User.query.filter_by(email=email).first():
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