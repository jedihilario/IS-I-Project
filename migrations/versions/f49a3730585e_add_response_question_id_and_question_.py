"""add response question_id and question_tag

Revision ID: f49a3730585e
Revises: cf74ce8a7906
Create Date: 2026-11-25 00:11:59.153122

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'f49a3730585e'
down_revision: str | Sequence[str] | None = 'cf74ce8a7906'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    inspector = sa.inspect(op.get_bind())
    if not inspector.has_table('question_tag'):
        op.create_table(
            'question_tag',
            sa.Column('question_id', sa.Integer(), nullable=False),
            sa.Column('tag_id', sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(['question_id'], ['question.id']),
            sa.ForeignKeyConstraint(['tag_id'], ['tag.id']),
            sa.PrimaryKeyConstraint('question_id', 'tag_id'),
        )
    with op.batch_alter_table('response', schema=None) as batch_op:
        batch_op.add_column(sa.Column('question_id', sa.Integer(), nullable=False))
        batch_op.create_foreign_key(
            'fk_response_question_id',
            'question',
            ['question_id'],
            ['id'],
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('response', schema=None) as batch_op:
        batch_op.drop_constraint('fk_response_question_id', type_='foreignkey')
        batch_op.drop_column('question_id')
    op.drop_table('question_tag')
