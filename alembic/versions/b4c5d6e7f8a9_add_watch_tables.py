"""add watch tables

Revision ID: b4c5d6e7f8a9
Revises: 9c1e2a3b4d5e
Create Date: 2026-08-16 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'b4c5d6e7f8a9'
down_revision: Union[str, Sequence[str], None] = '9c1e2a3b4d5e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('watches',
    sa.Column('company_id', sa.UUID(), nullable=False),
    sa.Column('competitor_ids', sa.JSON(), nullable=True),
    sa.Column('frequency', sa.String(length=20), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_watches_company_id'), 'watches', ['company_id'], unique=False)
    op.create_index(op.f('ix_watches_id'), 'watches', ['id'], unique=False)

    op.create_table('watch_snapshots',
    sa.Column('watch_id', sa.UUID(), nullable=False),
    sa.Column('audit_id', sa.UUID(), nullable=True),
    sa.Column('period', sa.Date(), nullable=False),
    sa.Column('metrics', sa.JSON(), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['watch_id'], ['watches.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['audit_id'], ['audits.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_watch_snapshots_watch_id'), 'watch_snapshots', ['watch_id'], unique=False)
    op.create_index(op.f('ix_watch_snapshots_id'), 'watch_snapshots', ['id'], unique=False)

    op.create_table('watch_alerts',
    sa.Column('watch_id', sa.UUID(), nullable=False),
    sa.Column('alert_type', sa.String(length=50), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('detail', sa.Text(), nullable=True),
    sa.Column('severity', sa.String(length=20), nullable=False),
    sa.Column('read', sa.Boolean(), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['watch_id'], ['watches.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_watch_alerts_watch_id'), 'watch_alerts', ['watch_id'], unique=False)
    op.create_index(op.f('ix_watch_alerts_id'), 'watch_alerts', ['id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_watch_alerts_id'), table_name='watch_alerts')
    op.drop_index(op.f('ix_watch_alerts_watch_id'), table_name='watch_alerts')
    op.drop_table('watch_alerts')
    op.drop_index(op.f('ix_watch_snapshots_id'), table_name='watch_snapshots')
    op.drop_index(op.f('ix_watch_snapshots_watch_id'), table_name='watch_snapshots')
    op.drop_table('watch_snapshots')
    op.drop_index(op.f('ix_watches_id'), table_name='watches')
    op.drop_index(op.f('ix_watches_company_id'), table_name='watches')
    op.drop_table('watches')
