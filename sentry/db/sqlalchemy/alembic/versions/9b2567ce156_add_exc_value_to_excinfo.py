"""Add exc_value to ExcInfo

Revision ID: 9b2567ce156
Revises: 4e6963b9eeca
Create Date: 2015-04-15 12:01:25.432315

"""

# revision identifiers, used by Alembic.
revision = '9b2567ce156'
down_revision = '4e6963b9eeca'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('exc_info', sa.Column('exc_value',
                                        sa.String(length=1024), nullable=True))


def downgrade():
    op.drop_column('exc_info', 'exc_value')
