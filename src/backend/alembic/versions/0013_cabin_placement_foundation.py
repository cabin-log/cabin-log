"""add cabin placement foundation

Revision ID: 0013_cabin_placement_foundation
Revises: 0012_wallet_inventory_foundation
Create Date: 2026-09-02 00:00:00
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0013_cabin_placement_foundation"
down_revision = "0012_wallet_inventory_foundation"
branch_labels = None
depends_on = None


def _table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return inspector.has_table(table_name)


def _index_exists(table_name: str, index_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table(table_name):
        return False
    return any(index["name"] == index_name for index in inspector.get_indexes(table_name))


def upgrade() -> None:
    if not _table_exists("cabins"):
        op.create_table(
            "cabins",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("width", sa.Integer(), nullable=False),
            sa.Column("depth", sa.Integer(), nullable=False),
            sa.Column("tile_width", sa.Integer(), nullable=False),
            sa.Column("tile_height", sa.Integer(), nullable=False),
            sa.Column("tile_z_height", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("user_id"),
        )

    if not _table_exists("cabin_placements"):
        op.create_table(
            "cabin_placements",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("cabin_id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("object_type", sa.String(length=60), nullable=False),
            sa.Column("object_key", sa.String(length=255), nullable=False),
            sa.Column("x", sa.Integer(), nullable=False),
            sa.Column("y", sa.Integer(), nullable=False),
            sa.Column("z", sa.Integer(), nullable=False),
            sa.Column("rotation", sa.Integer(), nullable=False),
            sa.Column("width", sa.Integer(), nullable=False),
            sa.Column("depth", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["cabin_id"], ["cabins.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )

    for index_name, columns in (
        ("ix_cabin_placements_cabin_id", ["cabin_id"]),
        ("ix_cabin_placements_object_type", ["object_type"]),
        ("ix_cabin_placements_object_key", ["object_key"]),
    ):
        if not _index_exists("cabin_placements", index_name):
            op.create_index(index_name, "cabin_placements", columns)


def downgrade() -> None:
    op.drop_index("ix_cabin_placements_object_key", table_name="cabin_placements")
    op.drop_index("ix_cabin_placements_object_type", table_name="cabin_placements")
    op.drop_index("ix_cabin_placements_cabin_id", table_name="cabin_placements")
    op.drop_table("cabin_placements")
    op.drop_table("cabins")
