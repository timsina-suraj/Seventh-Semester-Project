"""prescription items: medicine_id fk + quantity

Revision ID: 44008e621ef2
Revises: 7436577d53f6
Create Date: 2026-07-29 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '44008e621ef2'
down_revision: Union[str, None] = '7436577d53f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # batch mode: SQLite can't ALTER TABLE ADD CONSTRAINT directly — batch
    # mode handles the recreate-and-copy dance for it, and is a no-op
    # wrapper (plain ALTER TABLE) on backends that do support it directly.
    with op.batch_alter_table('prescription_items', schema=None) as batch_op:
        batch_op.add_column(sa.Column('medicine_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('quantity', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_prescription_items_medicine_id', 'medicines', ['medicine_id'], ['id'])


def downgrade() -> None:
    with op.batch_alter_table('prescription_items', schema=None) as batch_op:
        batch_op.drop_constraint('fk_prescription_items_medicine_id', type_='foreignkey')
        batch_op.drop_column('quantity')
        batch_op.drop_column('medicine_id')
