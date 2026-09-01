"""add github app installations

Revision ID: 0008_github_app_installations
Revises: 0007_github_profile_activities
Create Date: 2026-09-01 00:00:00
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0008_github_app_installations"
down_revision = "0007_github_profile_activities"
branch_labels = None
depends_on = None


def _table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    return sa.inspect(bind).has_table(table_name)


def _column_exists(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table(table_name):
        return False
    return any(column["name"] == column_name for column in inspector.get_columns(table_name))


def _index_exists(table_name: str, index_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table(table_name):
        return False
    return any(index["name"] == index_name for index in inspector.get_indexes(table_name))


def upgrade() -> None:
    if not _table_exists("github_installations"):
        op.create_table(
            "github_installations",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=True),
            sa.Column("github_installation_id", sa.BigInteger(), nullable=False),
            sa.Column("account_id", sa.BigInteger(), nullable=True),
            sa.Column("account_login", sa.String(length=255), nullable=True),
            sa.Column("account_type", sa.String(length=60), nullable=True),
            sa.Column("target_type", sa.String(length=60), nullable=True),
            sa.Column("repository_selection", sa.String(length=60), nullable=True),
            sa.Column("suspended_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("github_installation_id"),
        )
    if not _index_exists("github_installations", "ix_github_installations_account_id"):
        op.create_index(
            "ix_github_installations_account_id",
            "github_installations",
            ["account_id"],
        )
    if not _index_exists(
        "github_installations",
        "ix_github_installations_github_installation_id",
    ):
        op.create_index(
            "ix_github_installations_github_installation_id",
            "github_installations",
            ["github_installation_id"],
            unique=True,
        )
    if not _index_exists("github_installations", "ix_github_installations_user_id"):
        op.create_index(
            "ix_github_installations_user_id",
            "github_installations",
            ["user_id"],
        )
    if not _column_exists("github_repositories", "github_installation_id"):
        op.add_column(
            "github_repositories",
            sa.Column("github_installation_id", sa.BigInteger(), nullable=True),
        )
    if not _index_exists(
        "github_repositories",
        "ix_github_repositories_github_installation_id",
    ):
        op.create_index(
            "ix_github_repositories_github_installation_id",
            "github_repositories",
            ["github_installation_id"],
        )
    if not _column_exists("activities", "github_installation_id"):
        op.add_column(
            "activities",
            sa.Column("github_installation_id", sa.BigInteger(), nullable=True),
        )
    if not _index_exists("activities", "ix_activities_github_installation_id"):
        op.create_index(
            "ix_activities_github_installation_id",
            "activities",
            ["github_installation_id"],
        )


def downgrade() -> None:
    op.drop_index("ix_activities_github_installation_id", table_name="activities")
    op.drop_column("activities", "github_installation_id")
    op.drop_index(
        "ix_github_repositories_github_installation_id",
        table_name="github_repositories",
    )
    op.drop_column("github_repositories", "github_installation_id")
    op.drop_index("ix_github_installations_user_id", table_name="github_installations")
    op.drop_index(
        "ix_github_installations_github_installation_id",
        table_name="github_installations",
    )
    op.drop_index("ix_github_installations_account_id", table_name="github_installations")
    op.drop_table("github_installations")
