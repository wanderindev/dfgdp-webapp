"""Add media model

Revision ID: 9d87cdff54de
Revises: 82dd7e1f1e1e
Create Date: 2024-12-08 14:21:32.575502

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9d87cdff54de'
down_revision = '82dd7e1f1e1e'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('media',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('filename', sa.String(length=255), nullable=False),
    sa.Column('original_filename', sa.String(length=255), nullable=False),
    sa.Column('file_path', sa.String(length=512), nullable=False),
    sa.Column('file_size', sa.Integer(), nullable=False),
    sa.Column('mime_type', sa.String(length=127), nullable=False),
    sa.Column('media_type', sa.Enum('IMAGE', 'VIDEO', 'DOCUMENT', 'PDF', 'SPREADSHEET', 'OTHER', name='mediatype'), nullable=False),
    sa.Column('source', sa.Enum('LOCAL', 'YOUTUBE', 'S3', name='mediasource'), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=True),
    sa.Column('caption', sa.Text(), nullable=True),
    sa.Column('alt_text', sa.String(length=255), nullable=True),
    sa.Column('external_url', sa.String(length=512), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('articles', schema=None) as batch_op:
        batch_op.add_column(sa.Column('feature_image_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(None, 'media', ['feature_image_id'], ['id'])

    with op.batch_alter_table('social_media_posts', schema=None) as batch_op:
        batch_op.add_column(sa.Column('image_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(None, 'media', ['image_id'], ['id'])
        batch_op.drop_column('image_url')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('social_media_posts', schema=None) as batch_op:
        batch_op.add_column(sa.Column('image_url', sa.VARCHAR(length=255), autoincrement=False, nullable=True))
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_column('image_id')

    with op.batch_alter_table('articles', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_column('feature_image_id')

    op.drop_table('media')
    # ### end Alembic commands ###
