"""Add config table

Revision ID: 4716189b2ec9
Revises: 2a5dc03a5a9f
Create Date: 2015-02-13 14:53:46.190431

"""

# revision identifiers, used by Alembic.
revision = '4716189b2ec9'
down_revision = '2a5dc03a5a9f'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table('configs',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('key', sa.String(length=255), nullable=True),
    sa.Column('value', sa.PickleType(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('created_at_x_updated_at', 'configs',
                    ['created_at', 'updated_at'], unique=False)
    op.create_index('id_x_key', 'configs', ['id', 'key'], unique=False)


def downgrade():
    op.drop_index('id_x_key', table_name='configs')
    op.drop_index('created_at_x_updated_at', table_name='configs')
    op.drop_table('configs')
