"""Add service_history, service_status

Revision ID: 40ec54b70a32
Revises: 9b2567ce156
Create Date: 2015-04-16 19:55:37.723841

"""

# revision identifiers, used by Alembic.
revision = '40ec54b70a32'
down_revision = '9b2567ce156'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table('service_history',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('binary', sa.String(length=32), nullable=True),
    sa.Column('hostname', sa.String(length=50), nullable=True),
    sa.Column('start_at', sa.DateTime(),
              nullable=True),
    sa.Column('end_at', sa.DateTime(),
              nullable=True),
    sa.Column('duration', sa.Integer(), nullable=True),
    sa.Column('note', sa.Text(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('sh_binary_hostname_idx', 'service_history',
                    ['binary', 'hostname'], unique=False)
    op.create_index('sh_hostname_idx', 'service_history',
                    ['hostname'], unique=False)
    op.create_table('service_status',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('binary', sa.String(length=32), nullable=True),
    sa.Column('hostname', sa.String(length=50), nullable=True),
    sa.Column('updated_at', sa.DateTime(),
              nullable=True),
    sa.Column('state', sa.String(length=10), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ss_binary_hostname_idx', 'service_status',
                    ['binary', 'hostname'], unique=False)
    op.create_index('ss_hostname_idx', 'service_status',
                    ['hostname'], unique=False)
    op.create_index('ss_state_idx', 'service_status',
                    ['state'], unique=False)


def downgrade():
    op.drop_index('ss_state_idx', table_name='service_status')
    op.drop_index('ss_hostname_idx', table_name='service_status')
    op.drop_index('ss_binary_hostname_idx', table_name='service_status')
    op.drop_table('service_status')
    op.drop_index('sh_hostname_idx', table_name='service_history')
    op.drop_index('sh_binary_hostname_idx', table_name='service_history')
    op.drop_table('service_history')
