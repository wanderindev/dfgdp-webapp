from unittest.mock import patch

from click.testing import CliRunner
from flask.cli import ScriptInfo

from auth.commands import create_admin
from auth.utils import create_admin_user


def test_create_admin_user_success(db_session):
    """Test successful admin user creation."""
    success, message = create_admin_user(
        email="admin@example.com",
        full_name="Admin User",
        password="secure123",
    )

    assert success is True
    assert message == "Admin user created successfully"

    # Verify user was created with correct attributes
    from auth.models import User

    user = User.query.filter_by(email="admin@example.com").first()
    assert user is not None
    assert user.full_name == "Admin User"
    assert user.check_password("secure123")


def test_create_admin_user_duplicate(db_session, test_user):
    """Test creating admin user with existing email."""
    success, message = create_admin_user(
        email=test_user.email,  # Using existing test_user's email
        full_name="Another Name",
        password="password123",
    )

    assert success is False
    assert message == "User already exists"


def test_create_admin_user_error(db_session):
    """Test error handling in admin user creation."""
    with patch("auth.models.db.session.commit") as mock_commit:
        mock_commit.side_effect = Exception("Database error")

        success, message = create_admin_user(
            email="admin@example.com",
            full_name="Admin User",
            password="secure123",
        )

        assert success is False
        assert "Database error" in message


# noinspection PyTypeChecker
def test_create_admin_command_success(app, db_session):
    """Test successful CLI command execution."""
    runner = CliRunner()
    result = runner.invoke(
        create_admin,
        [
            "--email",
            "admin@example.com",
            "--full_name",
            "Admin User",
            "--password",
            "secure123",
        ],
        obj=ScriptInfo(create_app=lambda info: app),
    )

    assert result.exit_code == 0
    assert "Success: Admin user created successfully" in result.output


# noinspection PyTypeChecker
def test_create_admin_command_error(app, db_session):
    """Test CLI command with existing user."""
    runner = CliRunner()

    # First create a user
    first_result = runner.invoke(
        create_admin,
        [
            "--email",
            "admin@example.com",
            "--full_name",
            "Admin User",
            "--password",
            "secure123",
        ],
        obj=ScriptInfo(create_app=lambda info: app),
    )

    assert first_result.exit_code == 0  # First creation should succeed

    # Try to create the same user again
    second_result = runner.invoke(
        create_admin,
        [
            "--email",
            "admin@example.com",
            "--full_name",
            "Another Name",
            "--password",
            "password123",
        ],
        obj=ScriptInfo(create_app=lambda info: app),
    )

    assert second_result.exit_code == 0
    assert "Error: User already exists" in second_result.output


# noinspection PyTypeChecker
def test_create_admin_command_missing_args():
    """Test CLI command with missing required arguments."""
    runner = CliRunner()

    # Test missing email
    result = runner.invoke(
        create_admin,
        ["--full_name", "Admin User", "--password", "secure123"],
        obj=ScriptInfo(create_app=lambda info: info.app_import_path),
    )
    assert result.exit_code != 0
    assert "Missing option '--email'" in result.output

    # Test missing full_name
    result = runner.invoke(
        create_admin,
        ["--email", "admin@example.com", "--password", "secure123"],
        obj=ScriptInfo(create_app=lambda info: info.app_import_path),
    )
    assert result.exit_code != 0
    assert "Missing option '--full_name'" in result.output

    # Test missing password
    result = runner.invoke(
        create_admin,
        ["--email", "admin@example.com", "--full_name", "Admin User"],
        obj=ScriptInfo(create_app=lambda info: info.app_import_path),
    )
    assert result.exit_code != 0
    assert "Missing option '--password'" in result.output
