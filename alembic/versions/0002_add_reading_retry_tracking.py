"""add reading retry tracking

Revision ID: 0002_add_reading_retry_tracking
Revises: 0001_initial_persistence
Create Date: 2026-09-08
"""

from alembic import op
import sqlalchemy as sa

revision = "0002_add_reading_retry_tracking"
down_revision = "0001_initial_persistence"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "readings",
        sa.Column(
            "retry_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column(
        "readings",
        sa.Column(
            "last_attempt_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("readings", "last_attempt_at")
    op.drop_column("readings", "retry_count")
