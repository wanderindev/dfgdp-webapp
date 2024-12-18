from auth.models import User


# noinspection PyArgumentList
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


def test_user_activation_methods(test_user):
    """Test user activation/deactivation methods."""
    assert test_user.is_active is True  # Default state

    # Test deactivation
    test_user.deactivate()
    assert test_user.active is False
    assert test_user.is_active is False

    # Test reactivation
    test_user.reactivate()
    assert test_user.active is True
    assert test_user.is_active is True


def test_user_last_login(test_user):
    """Test updating last login timestamp."""
    assert test_user.last_login_at is None  # Default state

    test_user.update_last_login()
    assert test_user.last_login_at is not None
    assert test_user.last_login_at.tzinfo is not None  # Should be timezone-aware


# noinspection PyArgumentList
def test_user_default_values(db_session):
    """Test default values for user fields."""
    user = User(email="defaults@example.com", full_name="Default User")
    user.set_password("securepass")
    db_session.add(user)
    db_session.commit()

    assert user.active is True  # Should be active by default
    assert user.last_login_at is None  # Should be None by default
    assert user.created_at is not None  # Should have creation timestamp
    assert user.updated_at is not None  # Should have update timestamp
