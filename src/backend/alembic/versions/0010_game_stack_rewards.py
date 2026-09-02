"""add game stack rewards

Revision ID: 0010_game_stack_rewards
Revises: 0009_activity_source_external_id
Create Date: 2026-09-02 00:00:00
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0010_game_stack_rewards"
down_revision = "0009_activity_source_external_id"
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
    if not _table_exists("user_stack_profiles"):
        op.create_table(
            "user_stack_profiles",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("language", sa.String(length=100), nullable=False),
            sa.Column("total_bytes", sa.BigInteger(), nullable=False),
            sa.Column("ratio", sa.Float(), nullable=False),
            sa.Column("repository_count", sa.Integer(), nullable=False),
            sa.Column("recent_activity_count", sa.Integer(), nullable=False),
            sa.Column("active_days_30d", sa.Integer(), nullable=False),
            sa.Column("score", sa.Float(), nullable=False),
            sa.Column("tier", sa.Integer(), nullable=False),
            sa.Column("mastery_level", sa.Integer(), nullable=False),
            sa.Column("calculated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("user_id", "language", name="uq_user_stack_profiles_user_language"),
        )
    if not _index_exists("user_stack_profiles", "ix_user_stack_profiles_language"):
        op.create_index("ix_user_stack_profiles_language", "user_stack_profiles", ["language"])

    if not _table_exists("reward_grants"):
        op.create_table(
            "reward_grants",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("grant_key", sa.String(length=255), nullable=False),
            sa.Column("source", sa.String(length=60), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("user_id", "grant_key", name="uq_reward_grants_user_key"),
        )
    if not _index_exists("reward_grants", "ix_reward_grants_grant_key"):
        op.create_index("ix_reward_grants_grant_key", "reward_grants", ["grant_key"])
    if not _index_exists("reward_grants", "ix_reward_grants_source"):
        op.create_index("ix_reward_grants_source", "reward_grants", ["source"])

    if not _table_exists("reward_packages"):
        op.create_table(
            "reward_packages",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("grant_id", sa.Integer(), nullable=True),
            sa.Column("source", sa.String(length=60), nullable=False),
            sa.Column("status", sa.String(length=60), nullable=False),
            sa.Column("title", sa.String(length=255), nullable=False),
            sa.Column("description", sa.String(length=500), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("claimed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("metadata", sa.JSON(), nullable=True),
            sa.ForeignKeyConstraint(["grant_id"], ["reward_grants.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("grant_id"),
        )
    if not _index_exists("reward_packages", "ix_reward_packages_source"):
        op.create_index("ix_reward_packages_source", "reward_packages", ["source"])
    if not _index_exists("reward_packages", "ix_reward_packages_status"):
        op.create_index("ix_reward_packages_status", "reward_packages", ["status"])

    if not _table_exists("reward_package_items"):
        op.create_table(
            "reward_package_items",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("package_id", sa.Integer(), nullable=False),
            sa.Column("item_type", sa.String(length=60), nullable=False),
            sa.Column("item_key", sa.String(length=255), nullable=False),
            sa.Column("quantity", sa.Integer(), nullable=False),
            sa.Column("metadata", sa.JSON(), nullable=True),
            sa.ForeignKeyConstraint(["package_id"], ["reward_packages.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
    if not _index_exists("reward_package_items", "ix_reward_package_items_item_type"):
        op.create_index(
            "ix_reward_package_items_item_type",
            "reward_package_items",
            ["item_type"],
        )

    if not _table_exists("user_stack_rewards"):
        op.create_table(
            "user_stack_rewards",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("reward_key", sa.String(length=255), nullable=False),
            sa.Column("reward_type", sa.String(length=60), nullable=False),
            sa.Column("source_language", sa.String(length=100), nullable=False),
            sa.Column("stage", sa.Integer(), nullable=False),
            sa.Column("stack_reward_level", sa.Integer(), nullable=False),
            sa.Column("exp", sa.Integer(), nullable=False),
            sa.Column("is_featured", sa.Boolean(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("user_id", "reward_key", name="uq_user_stack_rewards_user_key"),
        )
    if not _index_exists("user_stack_rewards", "ix_user_stack_rewards_reward_key"):
        op.create_index("ix_user_stack_rewards_reward_key", "user_stack_rewards", ["reward_key"])
    if not _index_exists("user_stack_rewards", "ix_user_stack_rewards_reward_type"):
        op.create_index("ix_user_stack_rewards_reward_type", "user_stack_rewards", ["reward_type"])
    if not _index_exists("user_stack_rewards", "ix_user_stack_rewards_source_language"):
        op.create_index(
            "ix_user_stack_rewards_source_language",
            "user_stack_rewards",
            ["source_language"],
        )


def downgrade() -> None:
    op.drop_index("ix_user_stack_rewards_source_language", table_name="user_stack_rewards")
    op.drop_index("ix_user_stack_rewards_reward_type", table_name="user_stack_rewards")
    op.drop_index("ix_user_stack_rewards_reward_key", table_name="user_stack_rewards")
    op.drop_table("user_stack_rewards")
    op.drop_index("ix_reward_package_items_item_type", table_name="reward_package_items")
    op.drop_table("reward_package_items")
    op.drop_index("ix_reward_packages_status", table_name="reward_packages")
    op.drop_index("ix_reward_packages_source", table_name="reward_packages")
    op.drop_table("reward_packages")
    op.drop_index("ix_reward_grants_source", table_name="reward_grants")
    op.drop_index("ix_reward_grants_grant_key", table_name="reward_grants")
    op.drop_table("reward_grants")
    op.drop_index("ix_user_stack_profiles_language", table_name="user_stack_profiles")
    op.drop_table("user_stack_profiles")
