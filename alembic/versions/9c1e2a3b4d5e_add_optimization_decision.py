"""add optimization decision columns

Revision ID: 9c1e2a3b4d5e
Revises: a1b2c3d4e5f6
Create Date: 2026-08-16 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '9c1e2a3b4d5e'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('optimizations', sa.Column('contexte_entreprise', sa.JSON(), nullable=True))
    op.add_column('optimizations', sa.Column('decision', sa.String(length=20), nullable=True))
    op.add_column('optimizations', sa.Column('contenu_final', sa.Text(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('optimizations', 'contenu_final')
    op.drop_column('optimizations', 'decision')
    op.drop_column('optimizations', 'contexte_entreprise')
