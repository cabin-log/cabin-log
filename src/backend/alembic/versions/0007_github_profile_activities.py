"""add github profiles and activities

Revision ID: 0007_github_profile_activities
Revises: 0006_api_keys_usage_and_expiry
Create Date: 2026-08-19 00:00:00
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0007_github_profile_activities"
down_revision = "0006_api_keys_usage_and_expiry"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "github_profiles",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("github_user_id", sa.BigInteger(), nullable=False),
        sa.Column("login", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column("avatar_url", sa.Text(), nullable=True),
        sa.Column("profile_url", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("github_user_id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index(
        "ix_github_profiles_github_user_id",
        "github_profiles",
        ["github_user_id"],
        unique=True,
    )

    op.create_table(
        "github_repositories",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("github_repo_id", sa.BigInteger(), nullable=False),
        sa.Column("owner_login", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("private", sa.Boolean(), nullable=False),
        sa.Column("html_url", sa.Text(), nullable=True),
        sa.Column("default_branch", sa.String(length=255), nullable=True),
        sa.Column("primary_language", sa.String(length=100), nullable=True),
        sa.Column("pushed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("github_repo_id"),
    )
    op.create_index(
        "ix_github_repositories_full_name",
        "github_repositories",
        ["full_name"],
    )
    op.create_index(
        "ix_github_repositories_github_repo_id",
        "github_repositories",
        ["github_repo_id"],
        unique=True,
    )

    op.create_table(
        "github_repository_languages",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("repository_id", sa.Integer(), nullable=False),
        sa.Column("language", sa.String(length=100), nullable=False),
        sa.Column("bytes", sa.BigInteger(), nullable=False),
        sa.ForeignKeyConstraint(["repository_id"], ["github_repositories.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_github_repository_languages_language",
        "github_repository_languages",
        ["language"],
    )

    op.create_table(
        "activities",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("type", sa.String(length=60), nullable=False),
        sa.Column("repository_github_id", sa.BigInteger(), nullable=True),
        sa.Column("repository_full_name", sa.String(length=255), nullable=True),
        sa.Column("github_delivery_id", sa.String(length=128), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("github_delivery_id"),
    )
    op.create_index("ix_activities_github_delivery_id", "activities", ["github_delivery_id"])
    op.create_index("ix_activities_repository_github_id", "activities", ["repository_github_id"])
    op.create_index("ix_activities_type", "activities", ["type"])


def downgrade() -> None:
    op.drop_index("ix_activities_type", table_name="activities")
    op.drop_index("ix_activities_repository_github_id", table_name="activities")
    op.drop_index("ix_activities_github_delivery_id", table_name="activities")
    op.drop_table("activities")
    op.drop_index(
        "ix_github_repository_languages_language",
        table_name="github_repository_languages",
    )
    op.drop_table("github_repository_languages")
    op.drop_index("ix_github_repositories_github_repo_id", table_name="github_repositories")
    op.drop_index("ix_github_repositories_full_name", table_name="github_repositories")
    op.drop_table("github_repositories")
    op.drop_index("ix_github_profiles_github_user_id", table_name="github_profiles")
    op.drop_table("github_profiles")
