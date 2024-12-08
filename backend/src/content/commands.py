import click
from flask.cli import AppGroup
from sqlalchemy.exc import IntegrityError

from extensions import db
from .initial_categories import INITIAL_CATEGORIES
from .initial_taxonomies import INITIAL_TAXONOMIES
from .models import Taxonomy, Category

# Create the CLI group
content_cli = AppGroup("content")


# noinspection PyArgumentList
@content_cli.command("init-taxonomies")
def init_taxonomies() -> None:
    """Initialize taxonomies and categories with default configurations."""
    try:
        # First, create taxonomies
        for taxonomy_data in INITIAL_TAXONOMIES:
            if not Taxonomy.query.filter_by(name=taxonomy_data["name"]).first():
                taxonomy = Taxonomy(**taxonomy_data)
                db.session.add(taxonomy)
                click.echo(
                    f"Created taxonomy: {taxonomy_data['name']} (slug: {taxonomy.slug})"
                )
        db.session.commit()

        # Then create categories
        for category_data in INITIAL_CATEGORIES:
            # Make a copy of the data to avoid modifying the original
            category_dict = category_data.copy()

            # Get the referenced taxonomy
            taxonomy = Taxonomy.query.filter_by(name=category_dict["taxonomy"]).first()
            if not taxonomy:
                click.echo(f"Error: Taxonomy {category_dict['taxonomy']} not found")
                continue

            # Remove taxonomy name from data and add taxonomy_id
            category_dict.pop("taxonomy")
            category_dict["taxonomy_id"] = taxonomy.id

            # Check if category already exists
            if not Category.query.filter_by(
                taxonomy_id=taxonomy.id, name=category_dict["name"]
            ).first():
                category = Category(**category_dict)
                db.session.add(category)
                click.echo(
                    f"Created category: {category_dict['name']} (slug: {category.slug})"
                )

        db.session.commit()
        click.echo("Successfully initialized taxonomies and categories.")

    except IntegrityError as e:
        db.session.rollback()
        click.echo(f"Error: Database integrity error - {str(e)}")
    except Exception as e:
        db.session.rollback()
        click.echo(f"Error: {str(e)}")


@content_cli.command("list")
def list_content_hierarchy() -> None:
    """List all taxonomies and their categories."""
    taxonomies = Taxonomy.query.all()

    if not taxonomies:
        click.echo("No taxonomies found.")
        return

    for taxonomy in taxonomies:
        click.echo(f"\nTaxonomy: {taxonomy.name}")
        click.echo(f"Description: {taxonomy.description}")
        click.echo("\nCategories:")

        for category in taxonomy.categories:
            click.echo(f"  - {category.name}: {category.description}")
