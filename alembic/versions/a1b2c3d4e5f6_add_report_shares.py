"""add report_shares

Revision ID: a1b2c3d4e5f6
Revises: 7d3e9f1a2b4c
Create Date: 2026-08-16 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '7d3e9f1a2b4c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('report_shares',
    sa.Column('token', sa.String(length=64), nullable=False),
    sa.Column('scope', sa.String(length=20), nullable=False),
    sa.Column('company_id', sa.UUID(), nullable=False),
    sa.Column('audit_id', sa.UUID(), nullable=True),
    sa.Column('benchmark_id', sa.UUID(), nullable=True),
    sa.Column('month', sa.String(length=7), nullable=True),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('revoked', sa.Boolean(), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_report_shares_token'), 'report_shares', ['token'], unique=True)
    op.create_index(op.f('ix_report_shares_company_id'), 'report_shares', ['company_id'], unique=False)
    op.create_index(op.f('ix_report_shares_id'), 'report_shares', ['id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_report_shares_id'), table_name='report_shares')
    op.drop_index(op.f('ix_report_shares_company_id'), table_name='report_shares')
    op.drop_index(op.f('ix_report_shares_token'), table_name='report_shares')
    op.drop_table('report_shares')
