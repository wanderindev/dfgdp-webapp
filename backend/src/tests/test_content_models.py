from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import pytest
from sqlalchemy.exc import IntegrityError
from werkzeug.datastructures import FileStorage

from content.models import (
    Taxonomy,
    Category,
    Tag,
    ArticleSuggestion,
    Research,
    Article,
    SocialMediaAccount,
    SocialMediaPost,
    ArticleLevel,
    ContentStatus,
    Platform,
    Media,
    MediaType,
    MediaSource,
    InstagramMediaType,
    social_media_post_media,
)
from extensions import db


# noinspection PyArgumentList
def test_taxonomy_creation(db_session):
    """Test creating a taxonomy."""
    taxonomy = Taxonomy(
        name="World Religions",
        description="Major religions of the world",
    )
    db_session.add(taxonomy)
    db_session.commit()

    assert taxonomy.id is not None
    assert taxonomy.name == "World Religions"
    assert taxonomy.slug == "world-religions"
    assert taxonomy.created_at is not None
    assert taxonomy.updated_at is not None


# noinspection PyArgumentList
def test_category_creation(db_session):
    """Test creating a category with taxonomy relationship."""
    taxonomy = Taxonomy(
        name="World Religions",
        description="Major religions of the world",
    )
    db_session.add(taxonomy)
    db_session.commit()

    category = Category(
        taxonomy=taxonomy,
        name="Buddhism",
        description="Buddhist teachings and practices",
    )
    db_session.add(category)
    db_session.commit()

    assert category.id is not None
    assert category.taxonomy_id == taxonomy.id
    assert category.name == "Buddhism"
    assert category.slug == "buddhism"
    assert taxonomy.categories[0] == category


# noinspection PyArgumentList
def test_tag_approval_workflow(db_session, test_user):
    """Test tag creation and approval workflow."""
    tag = Tag(name="Philosophy", status=ContentStatus.PENDING)
    db_session.add(tag)
    db_session.commit()

    assert tag.status == ContentStatus.PENDING
    assert tag.approved_by_id is None
    assert tag.approved_at is None
    assert tag.slug == "philosophy"

    # Approve tag
    tag.status = ContentStatus.APPROVED
    tag.approved_by_id = test_user.id
    tag.approved_at = datetime.now(timezone.utc)
    db_session.commit()

    assert tag.status == ContentStatus.APPROVED
    assert tag.approved_by_id == test_user.id
    assert tag.approved_at is not None

    # Clean up the tag before the test_user fixture cleanup runs
    db_session.delete(tag)
    db_session.commit()


# noinspection PyArgumentList
def test_article_suggestion_creation(db_session):
    """Test creating an article suggestion."""
    taxonomy = Taxonomy(name="History", description="Historical events")
    db_session.add(taxonomy)
    category = Category(
        taxonomy=taxonomy,
        name="Ancient Greece",
        description="Ancient Greek history",
    )
    db_session.add(category)
    db_session.commit()

    suggestion = ArticleSuggestion(
        category=category,
        title="The Rise of Athens",
        main_topic="Athens' golden age and its impact",
        sub_topics=["Democracy", "Culture", "Military"],
        point_of_view="Academic analysis of cultural development",
        level=ArticleLevel.HIGH_SCHOOL,
    )
    db_session.add(suggestion)
    db_session.commit()

    assert suggestion.id is not None
    assert suggestion.category_id == category.id
    assert suggestion.status == ContentStatus.PENDING
    assert len(suggestion.sub_topics) == 3


# noinspection PyArgumentList
def test_research_creation(db_session):
    """Test creating research linked to a suggestion."""
    # Create necessary related objects
    taxonomy = Taxonomy(name="History", description="Historical events")
    db_session.add(taxonomy)
    category = Category(
        taxonomy=taxonomy,
        name="Ancient Greece",
        description="Ancient Greek history",
    )
    db_session.add(category)

    suggestion = ArticleSuggestion(
        category=category,
        title="The Rise of Athens",
        main_topic="Athens' golden age and its impact",
        sub_topics=["Democracy", "Culture", "Military"],
        point_of_view="Academic analysis",
        level=ArticleLevel.HIGH_SCHOOL,
    )
    db_session.add(suggestion)
    db_session.commit()

    research = Research(
        suggestion=suggestion,
        content="Detailed research about Athens...",
        status=ContentStatus.PENDING,
    )
    db_session.add(research)
    db_session.commit()

    assert research.id is not None
    assert research.suggestion_id == suggestion.id
    assert suggestion.research == research


# noinspection PyArgumentList
def test_article_creation_and_relationships(db_session):
    """Test creating an article with all its relationships."""
    # Create necessary related objects
    taxonomy = Taxonomy(name="History", description="Historical events")
    db_session.add(taxonomy)

    category = Category(
        taxonomy=taxonomy, name="Ancient Greece", description="Ancient Greek history"
    )
    db_session.add(category)

    suggestion = ArticleSuggestion(
        category=category,
        title="The Rise of Athens",
        main_topic="Athens' golden age",
        sub_topics=["Democracy"],
        point_of_view="Academic",
        level=ArticleLevel.HIGH_SCHOOL,
    )
    db_session.add(suggestion)

    research = Research(
        suggestion=suggestion,
        content="Research about Athens...",
        status=ContentStatus.APPROVED,
    )
    db_session.add(research)

    tag1 = Tag(name="History", status=ContentStatus.APPROVED)
    tag2 = Tag(name="Greece", status=ContentStatus.APPROVED)
    db_session.add_all([tag1, tag2])
    db_session.commit()

    article = Article(
        research=research,
        category=category,
        title="The Rise of Athens",
        content="Article content about Athens...",
        excerpt="Brief excerpt about Athens",
        level=ArticleLevel.HIGH_SCHOOL,
        tags=[tag1, tag2],
    )
    db_session.add(article)
    db_session.commit()

    # Test basic attributes
    assert article.id is not None
    assert article.title == "The Rise of Athens"
    assert article.slug == "the-rise-of-athens"
    assert len(article.tags) == 2

    # Test word count property
    assert article.word_count == 4  # "Article content about Athens..."

    # Test relevance score property
    assert isinstance(article.relevance_score, float)
    assert article.relevance_score >= 0


# noinspection PyArgumentList
def test_article_relationships(db_session, test_research):
    """Test article relationships (related articles)."""
    # Create two articles using the test_research fixture
    article1 = Article(
        category=test_research.suggestion.category,
        research=test_research,
        title="Article 1",
        content="Content 1",
        level=ArticleLevel.HIGH_SCHOOL,
    )
    article2 = Article(
        category=test_research.suggestion.category,
        research=test_research,
        title="Article 2",
        content="Content 2",
        level=ArticleLevel.HIGH_SCHOOL,
    )
    db_session.add_all([article1, article2])
    db_session.commit()

    # Set up relationship
    article1.related_articles.append(article2)
    db_session.commit()

    assert article2 in article1.related_articles
    assert article1 in article2.referenced_by


# noinspection PyArgumentList
def test_social_media_post_creation(db_session, test_research):
    """Test creating a social media post."""
    # Create social media account
    account = SocialMediaAccount(
        platform=Platform.INSTAGRAM,
        username="testaccount",
        account_id="123456",
        credentials={"access_token": "dummy_token"},
    )
    db_session.add(account)

    # Create article using test_research fixture
    article = Article(
        category=test_research.suggestion.category,
        research=test_research,
        title="Test Article",
        content="Test content",
        level=ArticleLevel.HIGH_SCHOOL,
    )
    db_session.add(article)
    db_session.commit()

    post = SocialMediaPost(
        article=article,
        account=account,
        content="Check out our new article about Ancient Greece!",
        hashtags=["#history", "#education"],
        scheduled_for=datetime.now(timezone.utc) + timedelta(days=1),
    )
    db_session.add(post)
    db_session.commit()

    assert post.id is not None
    assert post.platform == Platform.INSTAGRAM  # Test the property
    assert post.scheduled_for > datetime.now(timezone.utc)
    assert len(post.hashtags) == 2
    assert post.status == ContentStatus.PENDING


# noinspection PyUnboundLocalVariable,PyTypeChecker
def test_create_from_upload_success(app, db_session, mock_file, upload_folder):
    """Test successful file upload."""
    try:
        media = Media.create_from_upload(
            mock_file,
            title="Test Image",
            caption="Test Caption",
            alt_text="Test Alt",
        )

        assert media is not None
        assert media.title == "Test Image"
        assert media.caption == "Test Caption"
        assert media.alt_text == "Test Alt"
        assert media.media_type == MediaType.IMAGE
        assert media.source == MediaSource.LOCAL
        assert media.mime_type == "image/jpeg"
        assert Path(media.file_path).exists()
    finally:
        # Clean up any created files
        if media and media.file_path:
            try:
                Path(media.file_path).unlink(missing_ok=True)
            except:
                pass


def test_create_from_upload_no_file(db_session):
    """Test upload with no file."""
    assert Media.create_from_upload(None) is None


def test_create_from_upload_error(app, db_session, mock_file):
    """Test upload with database error."""
    with patch("content.models.db.session.commit", side_effect=Exception("DB Error")):
        media = Media.create_from_upload(mock_file)
        assert media is None
        # Verify file was cleaned up
        assert not any(Path(app.config["UPLOAD_FOLDER"]).glob("*"))


def test_create_from_youtube_success(db_session):
    """Test creating YouTube media entry."""
    url = "https://www.youtube.com/watch?v=test123"
    media = Media.create_from_youtube(
        url,
        title="Test Video",
        caption="Test Caption",
    )

    assert media is not None
    assert media.external_url == url
    assert media.title == "Test Video"
    assert media.caption == "Test Caption"
    assert media.media_type == MediaType.VIDEO
    assert media.source == MediaSource.YOUTUBE
    assert media.mime_type == "video/youtube"
    assert media.file_size == 0


def test_create_from_youtube_invalid_url(db_session):
    """Test creating YouTube media with invalid URL."""
    assert Media.create_from_youtube("https://example.com/video") is None


def test_create_from_youtube_error(db_session):
    """Test YouTube media creation with database error."""
    with patch("content.models.db.session.commit", side_effect=Exception("DB Error")):
        media = Media.create_from_youtube("https://www.youtube.com/watch?v=test123")
        assert media is None


def test_update_metadata_success(db_session, mock_file):
    """Test updating media metadata."""
    media = Media.create_from_upload(mock_file)

    assert media.update_metadata(
        title="New Title",
        caption="New Caption",
        alt_text="New Alt",
    )

    assert media.title == "New Title"
    assert media.caption == "New Caption"
    assert media.alt_text == "New Alt"


def test_update_metadata_error(db_session, mock_file):
    """Test metadata update with database error."""
    media = Media.create_from_upload(mock_file)

    with patch("content.models.db.session.commit", side_effect=Exception("DB Error")):
        assert not media.update_metadata(title="New Title")


# noinspection PyTypeChecker
def test_delete_local_file(app, db_session, mock_file):
    """Test deleting local media."""
    media = Media.create_from_upload(mock_file)
    file_path = Path(media.file_path)

    assert media.delete()
    assert not file_path.exists()
    assert db_session.get(Media, media.id) is None


def test_delete_youtube_media(db_session):
    """Test deleting YouTube media."""
    media = Media.create_from_youtube("https://www.youtube.com/watch?v=test123")
    assert media.delete()
    assert db_session.get(Media, media.id) is None


def test_delete_error(db_session, mock_file):
    """Test delete with database error."""
    media = Media.create_from_upload(mock_file)
    media_id = media.id

    with patch("content.models.db.session.commit", side_effect=Exception("DB Error")):
        assert not media.delete()
        # Verify that media still exists in database after failed deletion
        assert db_session.get(Media, media_id) is not None


def test_public_url(db_session, mock_file):
    """Test public URL generation."""
    # Local file
    local_media = Media.create_from_upload(mock_file)
    assert local_media.public_url == f"/media/{local_media.filename}"

    # YouTube
    youtube_media = Media.create_from_youtube("https://www.youtube.com/watch?v=test123")
    assert youtube_media.public_url == youtube_media.external_url


def test_markdown_code(db_session, mock_file):
    """Test Markdown code generation."""
    # Image
    image = Media.create_from_upload(
        mock_file,
        title="Test Image",
        caption="Test Caption",
        alt_text="Test Alt",
    )
    assert "![Test Alt](/media/" in image.markdown_code
    assert "*Test Caption*" in image.markdown_code

    # YouTube
    video = Media.create_from_youtube(
        "https://www.youtube.com/watch?v=test123",
        title="Test Video",
    )
    assert "[Test Video]" in video.markdown_code
    assert "https://www.youtube.com/watch?v=test123" in video.markdown_code


def test_media_type_detection():
    """Test media type detection from MIME types."""
    assert Media._get_media_type("image/jpeg") == MediaType.IMAGE
    assert Media._get_media_type("video/mp4") == MediaType.VIDEO
    assert Media._get_media_type("application/pdf") == MediaType.PDF
    assert Media._get_media_type("application/msword") == MediaType.DOCUMENT
    assert Media._get_media_type("application/vnd.ms-excel") == MediaType.SPREADSHEET
    assert Media._get_media_type("text/plain") == MediaType.OTHER


def test_event_listener_delete_error(app, db_session, mock_file):
    """Test media file deletion event listener error handling."""
    media = Media.create_from_upload(mock_file)

    with patch("pathlib.Path.unlink", side_effect=Exception("IO Error")), patch(
        "content.models.current_app.logger.error"
    ) as mock_logger:
        db.session.delete(media)
        db.session.commit()

        # Updated assertion to match actual error message format
        mock_logger.assert_called_with(
            f"Failed to delete file {media.file_path}: IO Error"
        )


# noinspection PyTypeChecker
def test_article_tag_methods(db_session, test_article):
    """Test article tagging methods."""
    # Test tag_article method
    tags = test_article.tag_article(["test", "example"])
    assert len(tags) == 2
    assert all(tag.name in ["test", "example"] for tag in tags)

    # Test with duplicate tags
    more_tags = test_article.tag_article(["test", "new"])
    assert len(more_tags) == 1  # Only "new" should be added
    assert more_tags[0].name == "new"

    # Test with integrity error
    with patch(
        "content.models.db.session.commit", side_effect=IntegrityError(None, None, None)
    ):
        tags = test_article.tag_article(["error"])
        assert len(tags) == 0


# noinspection PyArgumentList
def test_media_candidate_operations(db_session, test_user, test_research):
    """Test MediaCandidate operations."""
    from content.models import MediaCandidate, MediaSuggestion

    # Create test media suggestion using test_research
    suggestion = MediaSuggestion(
        research_id=test_research.id,
        commons_categories=["Test Category"],
        search_queries=["Test Query"],
        illustration_topics=["Test Topic"],
        reasoning="Test reasoning",
    )
    db_session.add(suggestion)
    db_session.commit()

    # Create candidate with complete Wikimedia metadata
    candidate = MediaCandidate(
        suggestion_id=suggestion.id,
        commons_id="File:Test_File.jpg",  # Added "File:" prefix
        commons_url="https://commons.wikimedia.org/wiki/File:Test_File.jpg",
        title="Test File",
        description="Test Description",
        author="Test Author",  # Added author
        license="CC BY-SA 4.0",
        license_url="https://creativecommons.org/licenses/by-sa/4.0/",  # Added license URL
        width=1920,
        height=1080,
        mime_type="image/jpeg",
        file_size=1000000,
    )
    db_session.add(candidate)
    db_session.commit()

    # Test aspect_ratio property
    assert candidate.aspect_ratio == pytest.approx(1920 / 1080)

    # Test approve method
    media = candidate.approve(test_user.id, notes="Test approval")
    assert media is not None
    assert candidate.status == ContentStatus.APPROVED
    assert candidate.reviewed_by_id == test_user.id
    assert candidate.reviewed_at is not None

    # Test the created media object
    assert (
        media.filename == "Test_File.jpg"
    )  # Should use commons_id without "File:" prefix
    assert media.source == MediaSource.WIKIMEDIA
    assert media.media_type == MediaType.IMAGE
    assert media.attribution is not None
    assert "Test Author" in media.attribution
    assert "CC BY-SA 4.0" in media.attribution

    # Test reject method
    another_candidate = MediaCandidate(
        suggestion_id=suggestion.id,
        commons_id="File:Test_File_2.jpg",
        commons_url="https://commons.wikimedia.org/wiki/File:Test_File_2.jpg",
        title="Test File 2",
        author="Test Author 2",
        license="CC BY-SA 4.0",
        license_url="https://creativecommons.org/licenses/by-sa/4.0/",
        width=1920,
        height=1080,
        mime_type="image/jpeg",
        file_size=1000000,
    )
    db_session.add(another_candidate)
    db_session.commit()

    assert another_candidate.reject(test_user.id, notes="Test rejection")
    assert another_candidate.status == ContentStatus.REJECTED
    assert another_candidate.reviewed_by_id == test_user.id
    assert another_candidate.reviewed_at is not None


# noinspection PyArgumentList
def test_hashtag_group_operations(db_session):
    """Test HashtagGroup operations."""
    from content.models import HashtagGroup

    # Create core hashtag group
    core_group = HashtagGroup(
        name="Core Brand",
        hashtags=["brand", "company"],
        description="Core brand hashtags",
        is_core=True,
    )
    db_session.add(core_group)

    # Create regular hashtag group
    regular_group = HashtagGroup(
        name="Product Launch",
        hashtags=["new", "launch"],
        description="Product launch hashtags",
        is_core=False,
    )
    db_session.add(regular_group)
    db_session.commit()

    assert core_group.is_core is True
    assert regular_group.is_core is False
    assert len(core_group.hashtags) == 2
    assert len(regular_group.hashtags) == 2


# noinspection PyTypeChecker
def test_media_file_operations_edge_cases(app, db_session, mock_file):
    """Test edge cases in media file operations."""
    # Test with non-existent upload folder
    with patch.object(Path, "mkdir", side_effect=PermissionError):
        media = Media.create_from_upload(mock_file)
        assert media is None

    # Test with file write error
    with patch.object(FileStorage, "save", side_effect=IOError):
        media = Media.create_from_upload(mock_file)
        assert media is None

    # Test deletion of non-existent file
    media = Media.create_from_upload(mock_file)
    Path(media.file_path).unlink()  # Delete file manually
    assert media.delete()  # Should still return True even if file doesn't exist


# noinspection PyArgumentList
def test_social_media_post_properties(
    db_session, test_article, test_social_media_account
):
    """Test the validate_instagram_format method with multiple media items."""
    # Create test Media objects
    media1 = Media(
        filename="media1.jpg",
        original_filename="media1.jpg",
        file_path="/media/media1.jpg",
        file_size=1000000,
        mime_type="image/jpeg",
        media_type=MediaType.IMAGE,
        source=MediaSource.LOCAL,
        instagram_media_type=InstagramMediaType.SQUARE,
    )
    media2 = Media(
        filename="media2.jpg",
        original_filename="media2.jpg",
        file_path="/media/media2.jpg",
        file_size=1000000,
        mime_type="image/jpeg",
        media_type=MediaType.IMAGE,
        source=MediaSource.LOCAL,
        instagram_media_type=InstagramMediaType.PORTRAIT,
    )
    media3 = Media(
        filename="media3.jpg",
        original_filename="media3.jpg",
        file_path="/media/media3.jpg",
        file_size=1000000,
        mime_type="image/jpeg",
        media_type=MediaType.IMAGE,
        source=MediaSource.LOCAL,
        instagram_media_type=None,
    )  # Missing type
    db_session.add_all([media1, media2, media3])
    db_session.commit()

    # Create SocialMediaPost
    post = SocialMediaPost(
        article=test_article,
        account=test_social_media_account,
        content="Test post content",
        hashtags=["#test"],
    )
    db_session.add(post)
    db_session.commit()

    # Add media items with positions
    db_session.execute(
        social_media_post_media.insert(),
        [
            {"post_id": post.id, "media_id": media1.id, "position": 0},
            {"post_id": post.id, "media_id": media2.id, "position": 1},
        ],
    )
    db_session.commit()

    # Validate Instagram format
    assert post.validate_instagram_format()  # Should return True

    # Add invalid media and test again
    db_session.execute(
        social_media_post_media.insert(),
        [{"post_id": post.id, "media_id": media3.id, "position": 2}],
    )
    db_session.commit()

    assert not post.validate_instagram_format()  # Should return False
