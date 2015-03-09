"""Add exc_info tables

Revision ID: 45306c23535e
Revises: 4716189b2ec9
Create Date: 2015-03-09 10:09:11.825644

"""

# revision identifiers, used by Alembic.
revision = '45306c23535e'
down_revision = '4716189b2ec9'
branch_labels = None
depends_on = None

import sentry
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


def upgrade():
    op.create_table(
        'exc_info',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('last_time', sa.DateTime(), nullable=True),
        sa.Column('binary', sa.String(length=36), nullable=True),
        sa.Column('count', sa.Integer(), nullable=True),
        sa.Column('on_process', sa.Boolean(), nullable=True),
        sa.Column('uuid', sa.String(length=36), nullable=True),
        sa.Column('exc_class', sa.String(length=255), nullable=True),
        sa.Column('file_path', sa.String(length=1024), nullable=True),
        sa.Column('func_name', sa.String(length=255), nullable=True),
        sa.Column('lineno', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(
        'exc_info_binary_idx', 'exc_info', ['binary'],
        unique=False
    )
    op.create_index(
        'exc_info_count_idx', 'exc_info', ['count'],
        unique=False
    )
    op.create_index(
        'exc_info_idx', 'exc_info',
        ['exc_class', 'file_path', 'func_name', 'lineno'],
        unique=False
    )
    op.create_index('exc_info_uuid_idx', 'exc_info', ['uuid'], unique=False)
    op.create_table(
        'exc_info_detail',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('hostname', sa.String(length=255), nullable=True),
        sa.Column('exc_value', sa.String(length=1024), nullable=True),
        sa.Column('payload', sentry.db.sqlalchemy.models.MediumPickleType(),
                  nullable=True),
        sa.Column('exc_info_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['exc_info_id'], ['exc_info.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('exc_info_created_at_hostname', 'exc_info_detail',
                    ['created_at', 'hostname'], unique=False)
    op.drop_table(u'error_logs')
    op.drop_table(u'error_log_stats')


def downgrade():
    op.create_table(
        u'error_log_stats',
        sa.Column(u'id', mysql.INTEGER(display_width=11), nullable=False),
        sa.Column(u'uuid', mysql.VARCHAR(length=36), nullable=True),
        sa.Column(u'title', mysql.VARCHAR(length=255), nullable=True),
        sa.Column(u'log_level', mysql.VARCHAR(length=10), nullable=True),
        sa.Column(u'datetime', sa.DATETIME(), nullable=True),
        sa.Column(u'count', mysql.INTEGER(display_width=11),
                  autoincrement=False,
                  nullable=True),
        sa.Column(u'on_process', mysql.TINYINT(display_width=1),
                  autoincrement=False, nullable=True),
        sa.PrimaryKeyConstraint(u'id'),
        mysql_default_charset=u'utf8',
        mysql_engine=u'InnoDB'
    )
    op.create_table(
        u'error_logs',
        sa.Column(u'id', mysql.INTEGER(display_width=11), nullable=False),
        sa.Column(u'datetime', sa.DATETIME(), nullable=True),
        sa.Column(u'hostname', mysql.VARCHAR(length=255), nullable=True),
        sa.Column(u'payload', mysql.MEDIUMBLOB(), nullable=True),
        sa.Column(u'stats_id', mysql.INTEGER(display_width=11),
                  autoincrement=False, nullable=True),
        sa.ForeignKeyConstraint([u'stats_id'], [u'error_log_stats.id'],
                                name=u'error_logs_ibfk_1'),
        sa.PrimaryKeyConstraint(u'id'),
        mysql_default_charset=u'utf8',
        mysql_engine=u'InnoDB'
    )
    op.drop_index('exc_info_created_at_hostname', table_name='exc_info_detail')
    op.drop_table('exc_info_detail')
    op.drop_index('exc_info_uuid_idx', table_name='exc_info')
    op.drop_index('exc_info_idx', table_name='exc_info')
    op.drop_index('exc_info_count_idx', table_name='exc_info')
    op.drop_index('exc_info_binary_idx', table_name='exc_info')
    op.drop_table('exc_info')
