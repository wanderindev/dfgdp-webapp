from auth.models import User


def test_user_creation(db_session):
    """Test creating a new user."""
    user = User(email="new@example.com", full_name="New User")
    user.set_password("securepass")
    db_session.add(user)
    db_session.commit()

    assert user.email == "new@example.com"
    assert user.full_name == "New User"
    assert user.check_password("securepass")
    assert not user.check_password("wrongpass")
    assert user.is_active


def test_user_representation(test_user):
    """Test string representation of user."""
    assert str(test_user) == f"<User {test_user.email}>"


def test_password_hashing(test_user):
    """Test password hashing."""
    assert test_user.password_hash != "password123"
    assert test_user.check_password("password123")
    assert not test_user.check_password("wrongpassword")
