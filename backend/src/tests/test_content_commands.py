from unittest.mock import patch

from click.testing import CliRunner
from flask.cli import ScriptInfo

from content.commands import init_taxonomies, list_content_hierarchy

# Test data
TEST_TAXONOMIES = [
    {
        "name": "Test Taxonomy",
        "description": "Test taxonomy description",
    }
]

TEST_CATEGORIES = [
    {
        "taxonomy": "Test Taxonomy",
        "name": "Test Category",
        "description": "Test category description",
    }
]


# noinspection PyTypeChecker
def test_init_taxonomies_success(app, db_session):
    """Test successful initialization of taxonomies and categories."""
    with patch("content.commands.INITIAL_TAXONOMIES", TEST_TAXONOMIES), patch(
        "content.commands.INITIAL_CATEGORIES", TEST_CATEGORIES
    ):
        runner = CliRunner()
        result = runner.invoke(
            init_taxonomies, obj=ScriptInfo(create_app=lambda info: app)
        )

        assert result.exit_code == 0
        assert "Created taxonomy: Test Taxonomy" in result.output
        assert "Created category: Test Category" in result.output
        assert "Successfully initialized taxonomies and categories" in result.output

        # Verify database state
        from content.models import Taxonomy, Category

        taxonomy = Taxonomy.query.filter_by(name="Test Taxonomy").first()
        assert taxonomy is not None
        assert taxonomy.description == "Test taxonomy description"

        category = Category.query.filter_by(name="Test Category").first()
        assert category is not None
        assert category.description == "Test category description"
        assert category.taxonomy_id == taxonomy.id


# noinspection PyTypeChecker
def test_init_taxonomies_duplicate(app, db_session):
    """Test initialization with existing taxonomies."""
    # First initialization
    with patch("content.commands.INITIAL_TAXONOMIES", TEST_TAXONOMIES), patch(
        "content.commands.INITIAL_CATEGORIES", TEST_CATEGORIES
    ):
        runner = CliRunner()
        runner.invoke(init_taxonomies, obj=ScriptInfo(create_app=lambda info: app))

    # Second initialization
    with patch("content.commands.INITIAL_TAXONOMIES", TEST_TAXONOMIES), patch(
        "content.commands.INITIAL_CATEGORIES", TEST_CATEGORIES
    ):
        result = runner.invoke(
            init_taxonomies, obj=ScriptInfo(create_app=lambda info: app)
        )

        assert result.exit_code == 0
        assert "Created taxonomy" not in result.output  # Should not create duplicate
        assert "Created category" not in result.output  # Should not create duplicate


# noinspection PyTypeChecker
def test_init_taxonomies_invalid_reference(app, db_session):
    """Test initialization with invalid taxonomy reference."""
    invalid_categories = [
        {
            "taxonomy": "Nonexistent Taxonomy",
            "name": "Test Category",
            "description": "Test category description",
        }
    ]

    with patch("content.commands.INITIAL_TAXONOMIES", TEST_TAXONOMIES), patch(
        "content.commands.INITIAL_CATEGORIES", invalid_categories
    ):
        runner = CliRunner()
        result = runner.invoke(
            init_taxonomies, obj=ScriptInfo(create_app=lambda info: app)
        )

        assert "Error: Taxonomy Nonexistent Taxonomy not found" in result.output


# noinspection PyTypeChecker
def test_init_taxonomies_db_error(app, db_session):
    """Test handling of database errors."""
    with patch("content.commands.INITIAL_TAXONOMIES", TEST_TAXONOMIES), patch(
        "content.commands.INITIAL_CATEGORIES", TEST_CATEGORIES
    ), patch(
        "content.commands.db.session.commit", side_effect=Exception("Database error")
    ):
        runner = CliRunner()
        result = runner.invoke(
            init_taxonomies, obj=ScriptInfo(create_app=lambda info: app)
        )

        assert "Error: Database error" in result.output


# noinspection PyTypeChecker
def test_list_content_empty(app, db_session):
    """Test listing content hierarchy with no data."""
    runner = CliRunner()
    result = runner.invoke(
        list_content_hierarchy, obj=ScriptInfo(create_app=lambda info: app)
    )

    assert result.exit_code == 0
    assert "No taxonomies found." in result.output


# noinspection PyTypeChecker
def test_list_content_hierarchy(app, db_session):
    """Test listing content hierarchy with data."""
    test_taxonomies = [
        {
            "name": "Test Taxonomy",
            "description": "Test taxonomy description",
        }
    ]

    test_categories = [
        {
            "taxonomy": "Test Taxonomy",  # Reference to taxonomy
            "name": "Test Category",
            "description": "Test category description",
        }
    ]

    # First create some test data
    with patch("content.commands.INITIAL_TAXONOMIES", test_taxonomies), patch(
        "content.commands.INITIAL_CATEGORIES", test_categories
    ):
        runner = CliRunner()
        runner.invoke(init_taxonomies, obj=ScriptInfo(create_app=lambda info: app))

        # Verify taxonomy and category were created
        from content.models import Taxonomy, Category

        taxonomy = db_session.query(Taxonomy).filter_by(name="Test Taxonomy").first()
        assert taxonomy is not None

        category = (
            db_session.query(Category)
            .filter_by(taxonomy_id=taxonomy.id, name="Test Category")
            .first()
        )
        assert category is not None

        # Then test the list command
        result = runner.invoke(
            list_content_hierarchy, obj=ScriptInfo(create_app=lambda info: app)
        )

        assert result.exit_code == 0
        assert "Taxonomy: Test Taxonomy" in result.output
        assert "Description: Test taxonomy description" in result.output
        assert "  - Test Category: Test category description" in result.output
