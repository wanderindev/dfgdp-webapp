import pytest

from app import create_app
from content.models import (
    Taxonomy,
    Category,
    ArticleSuggestion,
    Research,
    ArticleLevel,
    ContentStatus,
)
from extensions import db


@pytest.fixture(scope="session")
def app():
    """Create application for the tests."""
    app = create_app("testing")
    return app


# noinspection PyTestUnpassedFixture
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


# noinspection PyArgumentList
@pytest.fixture
def test_user(db_session):
    """Create a test user."""
    from auth.models import User
    from content.models import Tag

    user = User(email="test@example.com", full_name="Test User")
    user.set_password("password123")
    db_session.add(user)
    db_session.commit()

    yield user

    # Clean up any tags that reference this user
    Tag.query.filter_by(approved_by_id=user.id).update({Tag.approved_by_id: None})
    db_session.commit()

    # Now we can safely delete the user
    db_session.delete(user)
    db_session.commit()


@pytest.fixture(autouse=True)
def app_context(app):
    """Create app context for each test."""
    with app.app_context():
        yield


# noinspection PyArgumentList
@pytest.fixture
def test_taxonomy(db_session):
    """Create a test taxonomy."""
    taxonomy = Taxonomy(
        name="Test Taxonomy",
        slug="test-taxonomy",
        description="Test taxonomy description",
    )
    db_session.add(taxonomy)
    db_session.commit()
    return taxonomy


# noinspection PyArgumentList
@pytest.fixture
def test_category(db_session, test_taxonomy):
    """Create a test category."""
    category = Category(
        taxonomy_id=test_taxonomy.id,
        name="Test Category",
        slug="test-category",
        description="Test category description",
    )
    db_session.add(category)
    db_session.commit()
    return category


# noinspection PyArgumentList
@pytest.fixture
def test_suggestion(db_session, test_category):
    """Create a test article suggestion."""
    suggestion = ArticleSuggestion(
        category=test_category,
        title="Test Suggestion",
        main_topic="Test Topic",
        sub_topics=["Topic 1"],
        point_of_view="Test POV",
        level=ArticleLevel.HIGH_SCHOOL,
    )
    db_session.add(suggestion)
    db_session.commit()
    return suggestion


# noinspection PyArgumentList
@pytest.fixture
def test_research(db_session, test_suggestion):
    """Create a test research."""
    research = Research(
        suggestion=test_suggestion,
        content="Test research content",
        status=ContentStatus.APPROVED,
    )
    db_session.add(research)
    db_session.commit()
    return research
