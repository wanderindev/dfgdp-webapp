import io
from pathlib import Path
from typing import Generator, Any

import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy.orm import Session
from werkzeug.datastructures import FileStorage

from app import create_app
from auth.models import User
from content.models import (
    Taxonomy,
    Category,
    ArticleSuggestion,
    Research,
    ArticleLevel,
    ContentStatus,
    Article,
    SocialMediaAccount,
)
from extensions import db


def pytest_configure(config: Any) -> None:
    config.addinivalue_line("markers", "asyncio: mark test as async/asyncio test")


@pytest.fixture(scope="session")
def app() -> Flask:
    """Create application for the tests."""
    app = create_app("testing")
    return app


# noinspection PyTestUnpassedFixture
@pytest.fixture(scope="function")
def db_session(app: Flask) -> Generator[Session, None, None]:
    """Create a fresh database session for each test."""
    with app.app_context():
        db.create_all()
        yield db.session
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app: Flask) -> FlaskClient:
    """Test client for our Flask application."""
    return app.test_client()


# noinspection PyArgumentList
@pytest.fixture
def test_user(db_session: Session) -> Generator[User, None, None]:
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
def app_context(app: Flask) -> Generator[None, None, None]:
    """Create app context for each test."""
    with app.app_context():
        yield


# noinspection PyArgumentList
@pytest.fixture
def test_taxonomy(db_session: Session) -> Taxonomy:
    """Create a test taxonomy."""
    taxonomy = Taxonomy(
        name="Test Taxonomy",
        description="Test taxonomy description",
    )
    db_session.add(taxonomy)
    db_session.commit()
    return taxonomy


# noinspection PyArgumentList
@pytest.fixture
def test_category(db_session: Session, test_taxonomy: Taxonomy) -> Category:
    """Create a test category."""
    category = Category(
        taxonomy_id=test_taxonomy.id,
        name="Test Category",
        description="Test category description",
    )
    db_session.add(category)
    db_session.commit()
    return category


# noinspection PyArgumentList
@pytest.fixture
def test_suggestion(db_session: Session, test_category: Category) -> ArticleSuggestion:
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
def test_research(db_session: Session, test_suggestion: ArticleSuggestion) -> Research:
    """Create a test research."""
    research = Research(
        suggestion=test_suggestion,
        content="Test research content",
        status=ContentStatus.APPROVED,
    )
    db_session.add(research)
    db_session.commit()
    return research


# noinspection PyArgumentList
@pytest.fixture
def test_social_media_account(db_session: Session) -> SocialMediaAccount:
    """Create a test social media account."""
    from content.models import SocialMediaAccount, Platform

    account = SocialMediaAccount(
        platform=Platform.INSTAGRAM,
        username="testaccount",
        account_id="123456",
        credentials={"access_token": "dummy_token"},
    )
    db_session.add(account)
    db_session.commit()
    return account


# noinspection PyArgumentList
@pytest.fixture
def test_article(
    db_session: Session, test_research: Research, test_category: Category
) -> Article:
    """Create a test article."""
    from content.models import Article, ArticleLevel

    article = Article(
        research=test_research,
        category=test_category,
        title="Test Article",
        content="Test content",
        excerpt="Test excerpt",
        level=ArticleLevel.HIGH_SCHOOL,
    )
    db_session.add(article)
    db_session.commit()
    return article


@pytest.fixture
def mock_file():
    """Create a mock file for testing."""
    file_content = b"test content"
    return FileStorage(
        stream=io.BytesIO(file_content),
        filename="test.jpg",
        content_type="image/jpeg",
    )


@pytest.fixture
def upload_folder(app):
    """Create and clean up a temporary upload folder."""
    folder = Path(app.config["UPLOAD_FOLDER"])
    folder.mkdir(exist_ok=True)
    yield folder
    # Cleanup
    for file in folder.glob("*"):
        file.unlink()
    if folder.exists():
        folder.rmdir()
