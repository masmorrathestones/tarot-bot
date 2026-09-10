"""add scheduled X posts

Revision ID: 0016_x_post_scheduler
Revises: 0015_daily_weekly_plan
"""

from alembic import op
import sqlalchemy as sa


revision = "0016_x_post_scheduler"
down_revision = "0015_daily_weekly_plan"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "scheduled_x_posts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("language", sa.String(length=5), nullable=True),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="PENDING"),
        sa.Column("x_post_id", sa.String(length=64), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("last_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("x_post_id", name="uq_scheduled_x_posts_x_post_id"),
    )
    op.create_index("ix_scheduled_x_posts_scheduled_at", "scheduled_x_posts", ["scheduled_at"])
    op.create_index("ix_scheduled_x_posts_status", "scheduled_x_posts", ["status"])
    op.create_index("ix_scheduled_x_posts_x_post_id", "scheduled_x_posts", ["x_post_id"], unique=True)


def downgrade() -> None:
    op.drop_table("scheduled_x_posts")
