"""add response_time to service_status

Revision ID: 2f3ecb102a78
Revises: 4e96fb132a11
Create Date: 2015-05-06 11:53:16.265678

"""

# revision identifiers, used by Alembic.
revision = '2f3ecb102a78'
down_revision = '4e96fb132a11'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('service_status',
                  sa.Column('response_time', sa.Float(), nullable=True))


def downgrade():
    op.drop_column('service_status', 'response_time')
