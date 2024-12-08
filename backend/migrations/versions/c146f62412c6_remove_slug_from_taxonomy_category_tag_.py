"""Remove slug from taxonomy, category, tag, and article

Revision ID: c146f62412c6
Revises: 9d87cdff54de
Create Date: 2024-12-08 14:51:57.368582

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c146f62412c6'
down_revision = '9d87cdff54de'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('articles', schema=None) as batch_op:
        batch_op.drop_constraint('articles_slug_key', type_='unique')
        batch_op.drop_column('slug')

    with op.batch_alter_table('categories', schema=None) as batch_op:
        batch_op.drop_constraint('unique_category_slug_per_taxonomy', type_='unique')
        batch_op.create_unique_constraint('unique_category_name_per_taxonomy', ['taxonomy_id', 'name'])
        batch_op.drop_column('slug')

    with op.batch_alter_table('tags', schema=None) as batch_op:
        batch_op.drop_constraint('tags_slug_key', type_='unique')
        batch_op.drop_column('slug')

    with op.batch_alter_table('taxonomies', schema=None) as batch_op:
        batch_op.drop_constraint('taxonomies_slug_key', type_='unique')
        batch_op.drop_column('slug')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('taxonomies', schema=None) as batch_op:
        batch_op.add_column(sa.Column('slug', sa.VARCHAR(length=100), autoincrement=False, nullable=False))
        batch_op.create_unique_constraint('taxonomies_slug_key', ['slug'])

    with op.batch_alter_table('tags', schema=None) as batch_op:
        batch_op.add_column(sa.Column('slug', sa.VARCHAR(length=50), autoincrement=False, nullable=False))
        batch_op.create_unique_constraint('tags_slug_key', ['slug'])

    with op.batch_alter_table('categories', schema=None) as batch_op:
        batch_op.add_column(sa.Column('slug', sa.VARCHAR(length=100), autoincrement=False, nullable=False))
        batch_op.drop_constraint('unique_category_name_per_taxonomy', type_='unique')
        batch_op.create_unique_constraint('unique_category_slug_per_taxonomy', ['taxonomy_id', 'slug'])

    with op.batch_alter_table('articles', schema=None) as batch_op:
        batch_op.add_column(sa.Column('slug', sa.VARCHAR(length=255), autoincrement=False, nullable=False))
        batch_op.create_unique_constraint('articles_slug_key', ['slug'])

    # ### end Alembic commands ###