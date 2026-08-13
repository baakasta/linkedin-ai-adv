"""add calendar tables

Revision ID: 7d3e9f1a2b4c
Revises: 2f7c9d4e8a1b
Create Date: 2026-08-12 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '7d3e9f1a2b4c'
down_revision: Union[str, Sequence[str], None] = '2f7c9d4e8a1b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('calendars',
    sa.Column('company_id', sa.UUID(), nullable=False),
    sa.Column('frequence', sa.Integer(), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('company_id')
    )
    op.create_index(op.f('ix_calendars_company_id'), 'calendars', ['company_id'], unique=True)
    op.create_index(op.f('ix_calendars_id'), 'calendars', ['id'], unique=False)

    op.create_table('calendar_slots',
    sa.Column('calendar_id', sa.UUID(), nullable=False),
    sa.Column('date', sa.Date(), nullable=False),
    sa.Column('type_contenu', sa.String(length=100), nullable=False),
    sa.Column('sujet', sa.String(length=500), nullable=True),
    sa.Column('objectif', sa.String(length=500), nullable=True),
    sa.Column('cta', sa.String(length=500), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('generation_id', sa.UUID(), nullable=True),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['calendar_id'], ['calendars.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['generation_id'], ['generations.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_calendar_slots_calendar_id'), 'calendar_slots', ['calendar_id'], unique=False)
    op.create_index(op.f('ix_calendar_slots_date'), 'calendar_slots', ['date'], unique=False)
    op.create_index(op.f('ix_calendar_slots_id'), 'calendar_slots', ['id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_calendar_slots_id'), table_name='calendar_slots')
    op.drop_index(op.f('ix_calendar_slots_date'), table_name='calendar_slots')
    op.drop_index(op.f('ix_calendar_slots_calendar_id'), table_name='calendar_slots')
    op.drop_table('calendar_slots')
    op.drop_index(op.f('ix_calendars_id'), table_name='calendars')
    op.drop_index(op.f('ix_calendars_company_id'), table_name='calendars')
    op.drop_table('calendars')
