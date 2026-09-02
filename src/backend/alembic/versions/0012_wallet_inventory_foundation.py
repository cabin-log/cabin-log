"""add wallet and inventory foundation

Revision ID: 0012_wallet_inventory_foundation
Revises: 0011_user_game_settings
Create Date: 2026-09-02 00:00:00
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0012_wallet_inventory_foundation"
down_revision = "0011_user_game_settings"
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
    if not _table_exists("user_wallets"):
        op.create_table(
            "user_wallets",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("coins", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("user_id"),
        )

    if not _table_exists("user_inventory_items"):
        op.create_table(
            "user_inventory_items",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("item_type", sa.String(length=60), nullable=False),
            sa.Column("item_key", sa.String(length=255), nullable=False),
            sa.Column("quantity", sa.Integer(), nullable=False),
            sa.Column("metadata", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "user_id",
                "item_type",
                "item_key",
                name="uq_user_inventory_items_user_type_key",
            ),
        )
    if not _index_exists("user_inventory_items", "ix_user_inventory_items_item_type"):
        op.create_index(
            "ix_user_inventory_items_item_type",
            "user_inventory_items",
            ["item_type"],
        )
    if not _index_exists("user_inventory_items", "ix_user_inventory_items_item_key"):
        op.create_index(
            "ix_user_inventory_items_item_key",
            "user_inventory_items",
            ["item_key"],
        )


def downgrade() -> None:
    op.drop_index("ix_user_inventory_items_item_key", table_name="user_inventory_items")
    op.drop_index("ix_user_inventory_items_item_type", table_name="user_inventory_items")
    op.drop_table("user_inventory_items")
    op.drop_table("user_wallets")
