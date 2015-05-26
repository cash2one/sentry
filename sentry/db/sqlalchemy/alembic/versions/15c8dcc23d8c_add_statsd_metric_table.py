"""add statsd_metric table

Revision ID: 15c8dcc23d8c
Revises: 1cbeb2b93488
Create Date: 2015-05-25 17:13:41.533609

"""

# revision identifiers, used by Alembic.
revision = '15c8dcc23d8c'
down_revision = '1cbeb2b93488'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa

import sentry


def upgrade():
    op.create_table(
        'statsd_metric',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('namespace', sa.String(length=255), nullable=True),
        sa.Column('dimen_name', sa.String(length=255), nullable=True),
        sa.Column('dimen_value', sa.String(length=255), nullable=True),
        sa.Column('metric_name', sa.String(length=255), nullable=True),
        sa.Column('metric_value', sa.Float(), nullable=True),
        sa.Column('updated_at', sentry.db.sqlalchemy.models.LocalDateTime(),
                  nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('sm_namespace_dimen_name_idx', 'statsd_metric',
                    ['namespace', 'dimen_name'], unique=False)
    op.drop_index(u'request_id', table_name=u'events')


def downgrade():
    op.create_index(u'request_id', u'events', [u'request_id'], unique=False)
    op.drop_index('sm_namespace_dimen_name_idx', table_name='statsd_metric')
    op.drop_table('statsd_metric')
