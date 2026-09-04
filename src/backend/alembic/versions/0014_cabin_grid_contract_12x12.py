"""update cabin grid contract to 12x12

Revision ID: 0014_cabin_grid_contract_12x12
Revises: 0013_cabin_placement_foundation
Create Date: 2026-09-04 20:00:00
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0014_cabin_grid_contract_12x12"
down_revision = "0013_cabin_placement_foundation"
branch_labels = None
depends_on = None


def _table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return inspector.has_table(table_name)


def upgrade() -> None:
    if not _table_exists("cabins"):
        return

    op.execute(
        sa.text(
            """
            UPDATE cabins
            SET width = 12,
                depth = 12,
                tile_width = 60,
                tile_height = 30,
                tile_z_height = 46
            """
        )
    )


def downgrade() -> None:
    if not _table_exists("cabins"):
        return

    op.execute(
        sa.text(
            """
            UPDATE cabins
            SET width = 18,
                depth = 12,
                tile_width = 64,
                tile_height = 32,
                tile_z_height = 32
            """
        )
    )
