"""add strategies and conversations tables

Revision ID: 0255033a93e1
Revises: d90a5c7f148a
Create Date: 2026-08-29 09:33:11.687160

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '0255033a93e1'
down_revision: Union[str, Sequence[str], None] = 'd90a5c7f148a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('conversations',
    sa.Column('company_id', sa.UUID(), nullable=False),
    sa.Column('title', sa.Text(), nullable=True),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_conversations_company_id'), 'conversations', ['company_id'], unique=False)
    op.create_index(op.f('ix_conversations_id'), 'conversations', ['id'], unique=False)
    op.create_table('conversation_messages',
    sa.Column('conversation_id', sa.UUID(), nullable=False),
    sa.Column('author', sa.Text(), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_conversation_messages_conversation_id'), 'conversation_messages', ['conversation_id'], unique=False)
    op.create_index(op.f('ix_conversation_messages_id'), 'conversation_messages', ['id'], unique=False)
    op.create_table('strategies',
    sa.Column('company_id', sa.UUID(), nullable=False),
    sa.Column('audit_id', sa.UUID(), nullable=True),
    sa.Column('resultat', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['audit_id'], ['audits.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_strategies_audit_id'), 'strategies', ['audit_id'], unique=False)
    op.create_index(op.f('ix_strategies_company_id'), 'strategies', ['company_id'], unique=False)
    op.create_index(op.f('ix_strategies_id'), 'strategies', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_strategies_id'), table_name='strategies')
    op.drop_index(op.f('ix_strategies_company_id'), table_name='strategies')
    op.drop_index(op.f('ix_strategies_audit_id'), table_name='strategies')
    op.drop_table('strategies')
    op.drop_index(op.f('ix_conversation_messages_id'), table_name='conversation_messages')
    op.drop_index(op.f('ix_conversation_messages_conversation_id'), table_name='conversation_messages')
    op.drop_table('conversation_messages')
    op.drop_index(op.f('ix_conversations_id'), table_name='conversations')
    op.drop_index(op.f('ix_conversations_company_id'), table_name='conversations')
    op.drop_table('conversations')
