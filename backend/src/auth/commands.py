import click
from flask.cli import AppGroup

# Create a command group
auth_cli = AppGroup("auth")


@auth_cli.command("create-admin")
@click.option("--email", required=True, help="Email of the user")
@click.option("--full_name", required=True, help="Full name of the user")
@click.option("--password", required=True, help="Password of the user")
def create_admin(email, full_name, password):
    """Create an admin user."""
    from auth.utils import create_admin_user

    success, message = create_admin_user(email, full_name, password)
    if success:
        click.echo(f"Success: {message}")
    else:
        click.echo(f"Error: {message}")
