"""runtime settings and reading ratings

Revision ID: 0020_feedback_runtime
Revises: 0019_x_reply_opportunities
Create Date: 2026-09-11
"""

from alembic import op
import sqlalchemy as sa


revision = "0020_feedback_runtime"
down_revision = "0019_x_reply_opportunities"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "runtime_settings",
        sa.Column("key", sa.String(length=80), primary_key=True),
        sa.Column("value", sa.String(length=200), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    runtime_settings = sa.table(
        "runtime_settings",
        sa.column("key", sa.String),
        sa.column("value", sa.String),
    )
    op.bulk_insert(
        runtime_settings,
        [
            {"key": "x_prospecting_enabled", "value": "false"},
            {"key": "daily_referral_prompt_date", "value": ""},
        ],
    )

    op.create_table(
        "reading_ratings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("reading_id", sa.Integer(), sa.ForeignKey("readings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("stars", sa.Integer(), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("stars >= 1 AND stars <= 5", name="ck_reading_ratings_stars"),
        sa.UniqueConstraint("reading_id", name="uq_reading_ratings_reading_id"),
    )
    op.create_index("ix_reading_ratings_reading_id", "reading_ratings", ["reading_id"])
    op.create_index("ix_reading_ratings_user_id", "reading_ratings", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_reading_ratings_user_id", table_name="reading_ratings")
    op.drop_index("ix_reading_ratings_reading_id", table_name="reading_ratings")
    op.drop_table("reading_ratings")
    op.drop_table("runtime_settings")
