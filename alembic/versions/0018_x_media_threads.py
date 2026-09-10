"""add X media and thread scheduling fields

Revision ID: 0018_x_media_threads
Revises: 0017_x_git_campaigns
Create Date: 2026-09-10
"""

from alembic import op
import sqlalchemy as sa


revision = "0018_x_media_threads"
down_revision = "0017_x_git_campaigns"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "scheduled_x_posts",
        sa.Column("media_path", sa.String(length=500), nullable=True),
    )
    op.add_column(
        "scheduled_x_posts",
        sa.Column("parent_source_key", sa.String(length=160), nullable=True),
    )
    op.create_index(
        "ix_scheduled_x_posts_parent_source_key",
        "scheduled_x_posts",
        ["parent_source_key"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_scheduled_x_posts_parent_source_key",
        table_name="scheduled_x_posts",
    )
    op.drop_column("scheduled_x_posts", "parent_source_key")
    op.drop_column("scheduled_x_posts", "media_path")
