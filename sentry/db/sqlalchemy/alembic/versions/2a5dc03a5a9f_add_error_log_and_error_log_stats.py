"""Add error_log and error_log_stats

Revision ID: 2a5dc03a5a9f
Revises: 2f83c6521511
Create Date: 2015-02-12 13:31:29.086142

"""

# revision identifiers, used by Alembic.
revision = '2a5dc03a5a9f'
down_revision = '2f140d7d1410'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


def MediumBlob():
    return sa.LargeBinary().with_variant(mysql.MEDIUMBLOB(), 'mysql')


class MediumPickleType(sa.PickleType):
    impl = MediumBlob()


def upgrade():
    op.create_table('error_log_stats',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('uuid', sa.String(length=36), nullable=True),
    sa.Column('title', sa.String(length=255), nullable=True),
    sa.Column('log_level', sa.String(length=10), nullable=True),
    sa.Column('datetime', sa.DateTime(), nullable=True),
    sa.Column('count', sa.Integer(), nullable=True),
    sa.Column('on_process', sa.Boolean(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('id_x_uuid', 'error_log_stats', ['uuid', 'id'],
                    unique=False)
    op.create_index('title_x_loglevel_x_count_on_process', 'error_log_stats',
                    ['title', 'log_level', 'count', 'on_process'],
                    unique=False)
    op.create_table('error_logs',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('datetime', sa.DateTime(), nullable=True),
    sa.Column('hostname', sa.String(length=255), nullable=True),
    sa.Column('payload', MediumPickleType(), nullable=True),
    sa.Column('stats_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['stats_id'], ['error_log_stats.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('datetime_x_hostname', 'error_logs',
                    ['datetime', 'hostname'], unique=False)


def downgrade():
    op.drop_index('datetime_x_hostname', table_name='error_logs')
    op.drop_table('error_logs')
    op.drop_index('title_x_loglevel_x_count_on_process',
                  table_name='error_log_stats')
    op.drop_index('id_x_uuid', table_name='error_log_stats')
    op.drop_table('error_log_stats')
