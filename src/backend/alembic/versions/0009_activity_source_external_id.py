"""add activity source and external id

Revision ID: 0009_activity_source_external_id
Revises: 0008_github_app_installations
Create Date: 2026-09-01 00:00:00
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0009_activity_source_external_id"
down_revision = "0008_github_app_installations"
branch_labels = None
depends_on = None


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
    if not _column_exists("activities", "source"):
        op.add_column(
            "activities",
            sa.Column(
                "source",
                sa.String(length=60),
                nullable=False,
                server_default="WEBHOOK",
            ),
        )
    if not _index_exists("activities", "ix_activities_source"):
        op.create_index("ix_activities_source", "activities", ["source"])

    if not _column_exists("activities", "github_external_id"):
        op.add_column(
            "activities",
            sa.Column("github_external_id", sa.String(length=255), nullable=True),
        )
    if not _index_exists("activities", "ix_activities_github_external_id"):
        op.create_index(
            "ix_activities_github_external_id",
            "activities",
            ["github_external_id"],
            unique=True,
        )


def downgrade() -> None:
    op.drop_index("ix_activities_github_external_id", table_name="activities")
    op.drop_column("activities", "github_external_id")
    op.drop_index("ix_activities_source", table_name="activities")
    op.drop_column("activities", "source")
