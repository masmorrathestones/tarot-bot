"""add git campaign source key to scheduled X posts

Revision ID: 0017_x_git_campaigns
Revises: 0016_x_post_scheduler
"""

from alembic import op
import sqlalchemy as sa


revision = "0017_x_git_campaigns"
down_revision = "0016_x_post_scheduler"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "scheduled_x_posts",
        sa.Column("source_key", sa.String(length=160), nullable=True),
    )
    op.create_unique_constraint(
        "uq_scheduled_x_posts_source_key",
        "scheduled_x_posts",
        ["source_key"],
    )
    op.create_index(
        "ix_scheduled_x_posts_source_key",
        "scheduled_x_posts",
        ["source_key"],
    )


def downgrade() -> None:
    op.drop_index("ix_scheduled_x_posts_source_key", table_name="scheduled_x_posts")
    op.drop_constraint(
        "uq_scheduled_x_posts_source_key",
        "scheduled_x_posts",
        type_="unique",
    )
    op.drop_column("scheduled_x_posts", "source_key")
