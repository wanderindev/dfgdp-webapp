from datetime import datetime, timedelta, timezone

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
)


# noinspection PyArgumentList
def test_taxonomy_creation(db_session):
    """Test creating a taxonomy."""
    taxonomy = Taxonomy(
        name="World Religions",
        slug="world-religions",
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
        slug="world-religions",
        description="Major religions of the world",
    )
    db_session.add(taxonomy)
    db_session.commit()

    category = Category(
        taxonomy=taxonomy,
        name="Buddhism",
        slug="buddhism",
        description="Buddhist teachings and practices",
    )
    db_session.add(category)
    db_session.commit()

    assert category.id is not None
    assert category.taxonomy_id == taxonomy.id
    assert category.name == "Buddhism"
    assert taxonomy.categories[0] == category


# noinspection PyArgumentList
def test_tag_approval_workflow(db_session, test_user):
    """Test tag creation and approval workflow."""
    tag = Tag(name="Philosophy", slug="philosophy", status=ContentStatus.PENDING)
    db_session.add(tag)
    db_session.commit()

    assert tag.status == ContentStatus.PENDING
    assert tag.approved_by_id is None
    assert tag.approved_at is None

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
    taxonomy = Taxonomy(name="History", slug="history", description="Historical events")
    db_session.add(taxonomy)
    category = Category(
        taxonomy=taxonomy,
        name="Ancient Greece",
        slug="ancient-greece",
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
    taxonomy = Taxonomy(name="History", slug="history", description="Historical events")
    db_session.add(taxonomy)
    category = Category(
        taxonomy=taxonomy,
        name="Ancient Greece",
        slug="ancient-greece",
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
    taxonomy = Taxonomy(name="History", slug="history", description="Historical events")
    db_session.add(taxonomy)
    category = Category(
        taxonomy=taxonomy,
        name="Ancient Greece",
        slug="ancient-greece",
        description="Ancient Greek history",
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

    tag1 = Tag(name="History", slug="history", status=ContentStatus.APPROVED)
    tag2 = Tag(name="Greece", slug="greece", status=ContentStatus.APPROVED)
    db_session.add_all([tag1, tag2])
    db_session.commit()

    article = Article(
        research=research,
        category=category,
        title="The Rise of Athens",
        slug="rise-of-athens",
        content="Article content about Athens...",
        excerpt="Brief excerpt about Athens",
        ai_summary="AI summary for content manager",
        level=ArticleLevel.HIGH_SCHOOL,
        tags=[tag1, tag2],
    )
    db_session.add(article)
    db_session.commit()

    # Test basic attributes
    assert article.id is not None
    assert article.title == "The Rise of Athens"
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
        slug="article-1",
        content="Content 1",
        level=ArticleLevel.HIGH_SCHOOL,
    )
    article2 = Article(
        category=test_research.suggestion.category,
        research=test_research,
        title="Article 2",
        slug="article-2",
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
        slug="test-article",
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
