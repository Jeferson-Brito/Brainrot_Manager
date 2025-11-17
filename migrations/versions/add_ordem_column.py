"""Add ordem column to brainrot

Revision ID: add_ordem_column
Revises: 56d12c875d1b
Create Date: 2024-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_ordem_column'
down_revision = '56d12c875d1b'
branch_labels = None
depends_on = None


def upgrade():
    # Adicionar coluna ordem se não existir
    op.add_column('brainrot', sa.Column('ordem', sa.Integer(), nullable=True, server_default='0'))


def downgrade():
    # Remover coluna ordem
    op.drop_column('brainrot', 'ordem')

