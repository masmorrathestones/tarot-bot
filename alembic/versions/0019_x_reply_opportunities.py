"""add X reply opportunities

Revision ID: 0019_x_reply_opportunities
Revises: 0018_x_media_threads
Create Date: 2026-09-11
"""

from alembic import op
import sqlalchemy as sa


revision = "0019_x_reply_opportunities"
down_revision = "0018_x_media_threads"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "x_reply_opportunities",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tweet_id", sa.String(length=64), nullable=False),
        sa.Column("tweet_text", sa.Text(), nullable=False),
        sa.Column("author_id", sa.String(length=64), nullable=True),
        sa.Column("author_username", sa.String(length=100), nullable=True),
        sa.Column("language", sa.String(length=10), nullable=True),
        sa.Column("matched_query", sa.Text(), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("suggested_reply", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("x_reply_id", sa.String(length=64), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("discovered_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("replied_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tweet_id"),
        sa.UniqueConstraint("x_reply_id"),
    )
    op.create_index("ix_x_reply_opportunities_tweet_id", "x_reply_opportunities", ["tweet_id"], unique=True)
    op.create_index("ix_x_reply_opportunities_language", "x_reply_opportunities", ["language"], unique=False)
    op.create_index("ix_x_reply_opportunities_score", "x_reply_opportunities", ["score"], unique=False)
    op.create_index("ix_x_reply_opportunities_status", "x_reply_opportunities", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_x_reply_opportunities_status", table_name="x_reply_opportunities")
    op.drop_index("ix_x_reply_opportunities_score", table_name="x_reply_opportunities")
    op.drop_index("ix_x_reply_opportunities_language", table_name="x_reply_opportunities")
    op.drop_index("ix_x_reply_opportunities_tweet_id", table_name="x_reply_opportunities")
    op.drop_table("x_reply_opportunities")
