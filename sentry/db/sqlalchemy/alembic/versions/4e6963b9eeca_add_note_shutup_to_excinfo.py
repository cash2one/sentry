"""add note, shutup to excinfo

Creator: Tiantian Gao
Revision ID: 4e6963b9eeca
Revises: 45306c23535e
Create Date: 2015-04-02 09:19:55.756796

"""

revision = '4e6963b9eeca'
down_revision = '45306c23535e'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('exc_info',
                  sa.Column('note', sa.Text(), nullable=True))
    op.add_column('exc_info',
                  sa.Column('shutup_end', sa.DateTime(), nullable=True))
    op.add_column('exc_info',
                  sa.Column('shutup_start', sa.DateTime(), nullable=True))


def downgrade():
    op.drop_column('exc_info', 'shutup_start')
    op.drop_column('exc_info', 'shutup_end')
    op.drop_column('exc_info', 'note')
