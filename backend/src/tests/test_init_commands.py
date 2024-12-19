from unittest.mock import patch

from click.testing import CliRunner
from flask.cli import ScriptInfo
from slugify import slugify
from sqlalchemy.exc import IntegrityError

from agents.models import AIModel, Agent, PromptTemplate
from content.models import (
    Taxonomy,
    Category,
    Tag,
    ContentStatus,
    SocialMediaAccount,
    Platform,
    HashtagGroup,
)
from init.commands import (
    init_agents,
    init_hashtags,
    init_languages,
    init_social_accounts,
    init_tags,
    init_taxonomies,
)
from init.initial_agents import INITIAL_AI_MODELS, INITIAL_AGENTS
from init.initial_categories import INITIAL_CATEGORIES
from init.initial_hashtags import INITIAL_HASHTAG_GROUPS
from init.initial_languages import INITIAL_LANGUAGES
from init.initial_social_media_accounts import INITIAL_SOCIAL_MEDIA_ACCOUNTS
from init.initial_tags import INITIAL_TAGS
from init.initial_taxonomies import INITIAL_TAXONOMIES
from translations.models import ApprovedLanguage


# noinspection PyTypeChecker
def test_init_agents_success(app, db_session):
    """Test successful initialization of AI models and agents."""
    runner = CliRunner()
    result = runner.invoke(init_agents, obj=ScriptInfo(create_app=lambda info: app))

    assert result.exit_code == 0
    assert "Successfully initialized agents and models." in result.output

    # Verify AI Models
    for model_data in INITIAL_AI_MODELS:
        model = AIModel.query.filter_by(name=model_data["name"]).first()
        assert model is not None
        assert model.provider == model_data["provider"]
        assert model.model_id == model_data["model_id"]
        assert model.is_active == model_data.get("is_active", True)

    # Verify Agents
    for agent_data in INITIAL_AGENTS:
        # Get the referenced model
        model = AIModel.query.filter_by(name=agent_data["model"]).first()
        agent = Agent.query.filter_by(name=agent_data["name"]).first()

        assert agent is not None
        assert agent.type == agent_data["type"]
        assert agent.model_id == model.id
        assert agent.temperature == agent_data["temperature"]
        assert agent.max_tokens == agent_data["max_tokens"]

        # Verify Prompt Templates
        for prompt_data in agent_data["prompts"]:
            template = PromptTemplate.query.filter_by(
                agent_id=agent.id, name=prompt_data["name"]
            ).first()
            assert template is not None
            assert template.description == prompt_data["description"]
            assert template.template == prompt_data["template"]


# noinspection PyTypeChecker
def test_init_agents_already_initialized(app, db_session):
    """Test running init_agents twice does not create duplicates."""
    runner = CliRunner()

    # First run
    first_result = runner.invoke(
        init_agents, obj=ScriptInfo(create_app=lambda info: app)
    )
    assert first_result.exit_code == 0

    # Second run
    second_result = runner.invoke(
        init_agents, obj=ScriptInfo(create_app=lambda info: app)
    )
    assert second_result.exit_code == 0

    # Verify number of models and agents
    assert AIModel.query.count() == len(INITIAL_AI_MODELS)
    assert Agent.query.count() == len(INITIAL_AGENTS)
    assert PromptTemplate.query.count() == sum(
        len(agent["prompts"]) for agent in INITIAL_AGENTS
    )


# noinspection PyTypeChecker
def test_init_agents_db_integrity_error(app, db_session):
    """Test database integrity error handling."""
    with patch(
        "init.commands.db.session.commit", side_effect=IntegrityError(None, None, None)
    ):
        runner = CliRunner()
        result = runner.invoke(init_agents, obj=ScriptInfo(create_app=lambda info: app))

        assert result.exit_code == 0
        assert "Error: Database integrity error" in result.output

        # Verify no models or agents were created if initialization fails
        assert AIModel.query.count() == 0
        assert Agent.query.count() == 0
        assert PromptTemplate.query.count() == 0


# noinspection PyTypeChecker
def test_init_taxonomies_success(app, db_session):
    """Test successful initialization of taxonomies and categories."""
    runner = CliRunner()
    result = runner.invoke(init_taxonomies, obj=ScriptInfo(create_app=lambda info: app))

    assert result.exit_code == 0
    assert "Successfully initialized taxonomies and categories." in result.output

    # Verify Taxonomies
    for taxonomy_data in INITIAL_TAXONOMIES:
        taxonomy = Taxonomy.query.filter_by(name=taxonomy_data["name"]).first()
        assert taxonomy is not None
        assert taxonomy.description == taxonomy_data["description"]
        assert taxonomy.slug == slugify(taxonomy_data["name"])

    # Verify Categories
    for category_data in INITIAL_CATEGORIES:
        # Get the referenced taxonomy
        taxonomy = Taxonomy.query.filter_by(name=category_data["taxonomy"]).first()
        assert taxonomy is not None

        # Check category creation
        category = Category.query.filter_by(
            taxonomy_id=taxonomy.id, name=category_data["name"]
        ).first()
        assert category is not None
        assert category.description == category_data["description"]
        assert category.slug == slugify(category_data["name"])


# noinspection PyTypeChecker
def test_init_taxonomies_already_initialized(app, db_session):
    """Test running init_taxonomies twice does not create duplicates."""
    runner = CliRunner()

    # First run
    first_result = runner.invoke(
        init_taxonomies, obj=ScriptInfo(create_app=lambda info: app)
    )
    assert first_result.exit_code == 0

    # Second run
    second_result = runner.invoke(
        init_taxonomies, obj=ScriptInfo(create_app=lambda info: app)
    )
    assert second_result.exit_code == 0

    # Verify number of taxonomies and categories
    assert Taxonomy.query.count() == len(INITIAL_TAXONOMIES)
    assert Category.query.count() == len(INITIAL_CATEGORIES)


# noinspection PyTypeChecker
def test_init_taxonomies_invalid_category_reference(app, db_session):
    """Test handling of category with nonexistent taxonomy."""
    # Temporarily modify INITIAL_CATEGORIES to include a nonexistent taxonomy
    invalid_categories = INITIAL_CATEGORIES + [
        {
            "taxonomy": "Nonexistent Taxonomy",
            "name": "Invalid Category",
            "description": "This category should not be created",
        }
    ]

    with patch("init.commands.INITIAL_CATEGORIES", invalid_categories):
        runner = CliRunner()
        result = runner.invoke(
            init_taxonomies, obj=ScriptInfo(create_app=lambda info: app)
        )

        assert result.exit_code == 0
        assert "Error: Taxonomy Nonexistent Taxonomy not found" in result.output

        # Verify that only valid categories were created
        assert Category.query.count() == len(INITIAL_CATEGORIES)


# noinspection PyTypeChecker
def test_init_taxonomies_db_integrity_error(app, db_session):
    """Test handling of database integrity errors during initialization."""
    with patch(
        "init.commands.db.session.commit", side_effect=IntegrityError(None, None, None)
    ):
        runner = CliRunner()
        result = runner.invoke(
            init_taxonomies, obj=ScriptInfo(create_app=lambda info: app)
        )

        assert result.exit_code == 0
        assert "Error: Database integrity error" in result.output

        # Verify no taxonomies or categories were created
        assert Taxonomy.query.count() == 0
        assert Category.query.count() == 0


# noinspection PyTypeChecker
def test_init_tags_success(app, db_session):
    """Test successful initialization of tags."""
    runner = CliRunner()
    result = runner.invoke(init_tags, obj=ScriptInfo(create_app=lambda info: app))

    assert result.exit_code == 0
    assert "Successfully initialized tags." in result.output

    # Verify Tags
    for tag_data in INITIAL_TAGS:
        tag = Tag.query.filter_by(name=tag_data["name"]).first()
        assert tag is not None
        assert tag.status == ContentStatus[tag_data["status"]]
        assert tag.slug == tag_data["name"].lower().replace(" ", "-")


# noinspection PyTypeChecker,DuplicatedCode
def test_init_tags_already_initialized(app, db_session):
    """Test running init_tags twice does not create duplicates."""
    runner = CliRunner()

    # First run
    first_result = runner.invoke(init_tags, obj=ScriptInfo(create_app=lambda info: app))
    assert first_result.exit_code == 0

    # Second run
    second_result = runner.invoke(
        init_tags, obj=ScriptInfo(create_app=lambda info: app)
    )
    assert second_result.exit_code == 0

    # Verify number of tags
    assert Tag.query.count() == len(INITIAL_TAGS)


# noinspection PyTypeChecker
def test_init_tags_db_integrity_error(app, db_session):
    """Test handling of database integrity errors during tag initialization."""
    with patch(
        "init.commands.db.session.commit", side_effect=IntegrityError(None, None, None)
    ):
        runner = CliRunner()
        result = runner.invoke(init_tags, obj=ScriptInfo(create_app=lambda info: app))

        assert result.exit_code == 0
        assert "Error: Database integrity error" in result.output

        # Verify no tags were created
        assert Tag.query.count() == 0


# noinspection PyTypeChecker
def test_init_social_accounts_success(app, db_session):
    """Test successful initialization of social media accounts."""
    runner = CliRunner()
    result = runner.invoke(
        init_social_accounts, obj=ScriptInfo(create_app=lambda info: app)
    )

    assert result.exit_code == 0
    assert "Successfully initialized social media accounts." in result.output

    # Verify Social Media Accounts
    for account_data in INITIAL_SOCIAL_MEDIA_ACCOUNTS:
        account = SocialMediaAccount.query.filter_by(
            platform=account_data["platform"], username=account_data["username"]
        ).first()
        assert account is not None
        assert account.account_id == account_data["account_id"]
        assert account.is_active == account_data.get("is_active", True)
        assert account.credentials == account_data["credentials"]


# noinspection PyTypeChecker,DuplicatedCode
def test_init_social_accounts_already_initialized(app, db_session):
    """Test running init_social_accounts twice does not create duplicates."""
    runner = CliRunner()

    # First run
    first_result = runner.invoke(
        init_social_accounts, obj=ScriptInfo(create_app=lambda info: app)
    )
    assert first_result.exit_code == 0

    # Second run
    second_result = runner.invoke(
        init_social_accounts, obj=ScriptInfo(create_app=lambda info: app)
    )
    assert second_result.exit_code == 0

    # Verify number of social media accounts
    assert SocialMediaAccount.query.count() == len(INITIAL_SOCIAL_MEDIA_ACCOUNTS)


# noinspection PyTypeChecker
def test_init_social_accounts_db_integrity_error(app, db_session):
    """Test handling of database integrity errors during social media account initialization."""
    with patch(
        "init.commands.db.session.commit", side_effect=IntegrityError(None, None, None)
    ):
        runner = CliRunner()
        result = runner.invoke(
            init_social_accounts, obj=ScriptInfo(create_app=lambda info: app)
        )

        assert result.exit_code == 0
        assert "Error: Database integrity error" in result.output

        # Verify no social media accounts were created
        assert SocialMediaAccount.query.count() == 0


# noinspection PyTypeChecker
def test_init_social_accounts_with_duplicate_platform_username(app, db_session):
    """Test handling of attempts to create duplicate social media accounts."""
    # Create a copy of initial accounts with a duplicate entry
    duplicate_accounts = INITIAL_SOCIAL_MEDIA_ACCOUNTS + [
        {
            "platform": Platform.INSTAGRAM,
            "username": "panama_in_context",  # Same as first account
            "account_id": "99999",
            "credentials": {"access_token": "duplicate_token"},
            "is_active": True,
        }
    ]

    with patch("init.commands.INITIAL_SOCIAL_MEDIA_ACCOUNTS", duplicate_accounts):
        runner = CliRunner()
        result = runner.invoke(
            init_social_accounts, obj=ScriptInfo(create_app=lambda info: app)
        )

        # Verify that only unique accounts are created
        assert result.exit_code == 0
        assert "Successfully initialized social media accounts." in result.output
        assert SocialMediaAccount.query.count() == len(INITIAL_SOCIAL_MEDIA_ACCOUNTS)


# noinspection PyTypeChecker
def test_init_hashtags_success(app, db_session):
    """Test successful initialization of hashtag groups."""
    runner = CliRunner()
    result = runner.invoke(init_hashtags, obj=ScriptInfo(create_app=lambda info: app))

    assert result.exit_code == 0
    assert "Successfully initialized hashtag groups." in result.output

    # Verify Hashtag Groups
    for group_data in INITIAL_HASHTAG_GROUPS:
        group = HashtagGroup.query.filter_by(name=group_data["name"]).first()
        assert group is not None
        assert group.description == group_data["description"]
        assert group.is_core == group_data["is_core"]
        assert set(group.hashtags) == set(group_data["hashtags"])


# noinspection PyTypeChecker,DuplicatedCode
def test_init_hashtags_already_initialized(app, db_session):
    """Test running init_hashtags twice does not create duplicates."""
    runner = CliRunner()

    # First run
    first_result = runner.invoke(
        init_hashtags, obj=ScriptInfo(create_app=lambda info: app)
    )
    assert first_result.exit_code == 0

    # Second run
    second_result = runner.invoke(
        init_hashtags, obj=ScriptInfo(create_app=lambda info: app)
    )
    assert second_result.exit_code == 0

    # Verify number of hashtag groups
    assert HashtagGroup.query.count() == len(INITIAL_HASHTAG_GROUPS)


# noinspection PyTypeChecker
def test_init_hashtags_db_integrity_error(app, db_session):
    """Test handling of database integrity errors during hashtag group initialization."""
    with patch(
        "init.commands.db.session.commit", side_effect=IntegrityError(None, None, None)
    ):
        runner = CliRunner()
        result = runner.invoke(
            init_hashtags, obj=ScriptInfo(create_app=lambda info: app)
        )

        assert result.exit_code == 0
        assert "Error: Database integrity error" in result.output

        # Verify no hashtag groups were created
        assert HashtagGroup.query.count() == 0


# noinspection PyTypeChecker
def test_init_hashtags_with_duplicate_group(app, db_session):
    """Test handling of attempts to create duplicate hashtag groups."""
    # Create a copy of initial hashtag groups with a duplicate entry
    duplicate_groups = INITIAL_HASHTAG_GROUPS + [
        {
            "name": "Core Brand",  # Same name as an existing group
            "description": "Duplicate Core Hashtags",
            "is_core": True,
            "hashtags": ["DuplicateBrand", "DuplicateTag"],
        }
    ]

    with patch("init.commands.INITIAL_HASHTAG_GROUPS", duplicate_groups):
        runner = CliRunner()
        result = runner.invoke(
            init_hashtags, obj=ScriptInfo(create_app=lambda info: app)
        )

        # Verify that only unique hashtag groups are created
        assert result.exit_code == 0
        assert "Successfully initialized hashtag groups." in result.output
        assert HashtagGroup.query.count() == len(INITIAL_HASHTAG_GROUPS)


# noinspection PyTypeChecker
def test_init_hashtags_group_details(app, db_session):
    """Test detailed verification of hashtag group properties."""
    runner = CliRunner()
    result = runner.invoke(init_hashtags, obj=ScriptInfo(create_app=lambda info: app))

    assert result.exit_code == 0

    # Verify specific properties of known groups
    core_group = HashtagGroup.query.filter_by(is_core=True).first()
    assert core_group is not None
    assert core_group.is_core == True

    # Verify that both core and non-core groups are created
    core_groups = HashtagGroup.query.filter_by(is_core=True).all()
    non_core_groups = HashtagGroup.query.filter_by(is_core=False).all()

    assert len(core_groups) > 0, "At least one core hashtag group should exist"
    assert len(non_core_groups) > 0, "At least one non-core hashtag group should exist"


# noinspection PyTypeChecker
def test_init_languages_success(app, db_session):
    """Test successful initialization of approved languages."""
    runner = CliRunner()
    result = runner.invoke(init_languages, obj=ScriptInfo(create_app=lambda info: app))

    assert result.exit_code == 0
    assert "Successfully initialized languages." in result.output

    # Verify Languages
    for lang_data in INITIAL_LANGUAGES:
        language = ApprovedLanguage.query.filter_by(code=lang_data["code"]).first()
        assert language is not None
        assert language.name == lang_data["name"]
        assert language.is_active == lang_data["is_active"]
        assert language.is_default == lang_data.get("is_default", False)


# noinspection PyTypeChecker,DuplicatedCode
def test_init_languages_already_initialized(app, db_session):
    """Test running init_languages twice does not create duplicates."""
    runner = CliRunner()

    # First run
    first_result = runner.invoke(
        init_languages, obj=ScriptInfo(create_app=lambda info: app)
    )
    assert first_result.exit_code == 0

    # Second run
    second_result = runner.invoke(
        init_languages, obj=ScriptInfo(create_app=lambda info: app)
    )
    assert second_result.exit_code == 0

    # Verify number of languages
    assert ApprovedLanguage.query.count() == len(INITIAL_LANGUAGES)


# noinspection PyTypeChecker
def test_init_languages_db_integrity_error(app, db_session):
    """Test handling of database integrity errors during language initialization."""
    with patch(
        "init.commands.db.session.commit", side_effect=IntegrityError(None, None, None)
    ):
        runner = CliRunner()
        result = runner.invoke(
            init_languages, obj=ScriptInfo(create_app=lambda info: app)
        )

        assert result.exit_code == 0
        assert "Error: Database integrity error" in result.output

        # Verify no languages were created
        assert ApprovedLanguage.query.count() == 0


# noinspection PyTypeChecker
def test_init_languages_default_language_validation(app, db_session):
    """Test that only one default language is set."""
    runner = CliRunner()
    result = runner.invoke(init_languages, obj=ScriptInfo(create_app=lambda info: app))

    assert result.exit_code == 0

    # Count default languages
    default_languages = ApprovedLanguage.query.filter_by(is_default=True).all()
    assert len(default_languages) == 1, "Only one default language should exist"

    # Verify the default language is English
    default_language = default_languages[0]
    assert default_language.code == "en", "Default language should be English"
    assert default_language.is_active is True, "Default language must be active"


# noinspection PyTypeChecker
def test_init_languages_active_language_validation(app, db_session):
    """Test that active languages are set correctly."""
    runner = CliRunner()
    result = runner.invoke(init_languages, obj=ScriptInfo(create_app=lambda info: app))

    assert result.exit_code == 0

    # Verify active languages
    active_languages = ApprovedLanguage.query.filter_by(is_active=True).all()
    active_codes = {lang.code for lang in active_languages}

    # Check that all initial languages are active
    expected_active_codes = {lang["code"] for lang in INITIAL_LANGUAGES}
    assert (
        active_codes == expected_active_codes
    ), "All initial languages should be active"


# noinspection PyTypeChecker
def test_init_languages_with_duplicate_languages(app, db_session):
    """Test handling of attempts to create duplicate languages."""
    # Create a copy of initial languages with a duplicate entry
    duplicate_languages = INITIAL_LANGUAGES + [
        {
            "code": "en",  # Duplicate of existing English language
            "name": "Duplicate English",
            "is_active": True,
            "is_default": False,
        }
    ]

    with patch("init.commands.INITIAL_LANGUAGES", duplicate_languages):
        runner = CliRunner()
        result = runner.invoke(
            init_languages, obj=ScriptInfo(create_app=lambda info: app)
        )

        # Verify that only unique languages are created
        assert result.exit_code == 0
        assert "Successfully initialized languages." in result.output
        assert ApprovedLanguage.query.count() == len(INITIAL_LANGUAGES)
