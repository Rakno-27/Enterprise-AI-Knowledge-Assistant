"""add_client_id_to_schema

Revision ID: cbe70e3db6b0
Revises: f7fcba2903da
Create Date: 2026-08-18 15:07:31.359157

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cbe70e3db6b0'
down_revision: Union[str, Sequence[str], None] = 'f7fcba2903da'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. conversations table
    with op.batch_alter_table('conversations', schema=None) as batch_op:
        batch_op.add_column(sa.Column('client_id', sa.String(), nullable=True))
        batch_op.create_index(batch_op.f('ix_conversations_client_id'), ['client_id'], unique=False)
        batch_op.create_foreign_key('fk_conversations_client_id', 'clients', ['client_id'], ['id'], ondelete='CASCADE')

    # 2. documents table
    with op.batch_alter_table('documents', schema=None) as batch_op:
        batch_op.add_column(sa.Column('client_id', sa.String(), nullable=True))
        batch_op.create_index(batch_op.f('ix_documents_client_id'), ['client_id'], unique=False)
        batch_op.create_foreign_key('fk_documents_client_id', 'clients', ['client_id'], ['id'], ondelete='CASCADE')

    # 3. users table
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('client_id', sa.String(), nullable=True))
        batch_op.create_index(batch_op.f('ix_users_client_id'), ['client_id'], unique=False)
        batch_op.create_foreign_key('fk_users_client_id', 'clients', ['client_id'], ['id'], ondelete='CASCADE')


def downgrade() -> None:
    # 1. users table
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_constraint('fk_users_client_id', type_='foreignkey')
        batch_op.drop_index(batch_op.f('ix_users_client_id'))
        batch_op.drop_column('client_id')

    # 2. documents table
    with op.batch_alter_table('documents', schema=None) as batch_op:
        batch_op.drop_constraint('fk_documents_client_id', type_='foreignkey')
        batch_op.drop_index(batch_op.f('ix_documents_client_id'))
        batch_op.drop_column('client_id')

    # 3. conversations table
    with op.batch_alter_table('conversations', schema=None) as batch_op:
        batch_op.drop_constraint('fk_conversations_client_id', type_='foreignkey')
        batch_op.drop_index(batch_op.f('ix_conversations_client_id'))
        batch_op.drop_column('client_id')
