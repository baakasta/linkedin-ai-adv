"""add benchmark tables

Revision ID: 2f7c9d4e8a1b
Revises: 6daeea1afe9a
Create Date: 2026-08-11 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '2f7c9d4e8a1b'
down_revision: Union[str, Sequence[str], None] = '6daeea1afe9a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('benchmarks',
    sa.Column('company_id', sa.UUID(), nullable=False),
    sa.Column('audit_ids', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('resultat', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_benchmarks_company_id'), 'benchmarks', ['company_id'], unique=False)
    op.create_index(op.f('ix_benchmarks_id'), 'benchmarks', ['id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_benchmarks_id'), table_name='benchmarks')
    op.drop_index(op.f('ix_benchmarks_company_id'), table_name='benchmarks')
    op.drop_table('benchmarks')
