"""add hash_str to exc_info

Revision ID: 4e96fb132a11
Revises: 40ec54b70a32
Create Date: 2015-04-23 15:04:35.948935

"""

# revision identifiers, used by Alembic.
revision = '4e96fb132a11'
down_revision = '40ec54b70a32'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('exc_info', sa.Column('hash_str', sa.String(length=32),
                                        nullable=True))
    op.create_index('exc_info_hash_str', 'exc_info', ['hash_str'],
                    unique=False)


def downgrade():
    op.drop_index('exc_info_hash_str', table_name='exc_info')
    op.drop_column('exc_info', 'hash_str')
