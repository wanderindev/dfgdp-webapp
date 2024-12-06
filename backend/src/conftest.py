import pytest
from app import create_app
from extensions import db


@pytest.fixture(scope="session")
def app():
    """Create application for the tests."""
    app = create_app("testing")
    return app


@pytest.fixture(scope="function")
def db_session(app):
    """Create a fresh database session for each test."""
    with app.app_context():
        db.create_all()
        yield db.session
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Test client for our Flask application."""
    return app.test_client()


@pytest.fixture
def test_user(db_session):
    """Create a test user."""
    from auth.models import User

    user = User(email="test@example.com", full_name="Test User")
    user.set_password("password123")
    db_session.add(user)
    db_session.commit()

    yield user

    db_session.delete(user)
    db_session.commit()


@pytest.fixture(autouse=True)
def app_context(app):
    """Create app context for each test."""
    with app.app_context():
        yield
