"""persist scheduled Tarot analysis delivery time

Revision ID: 0021_scheduled_analysis
Revises: 0020_feedback_runtime
Create Date: 2026-09-11
"""

from alembic import op
import sqlalchemy as sa


revision = "0021_scheduled_analysis"
down_revision = "0020_feedback_runtime"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "readings",
        sa.Column("scheduled_analysis_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_readings_scheduled_analysis_at",
        "readings",
        ["scheduled_analysis_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_readings_scheduled_analysis_at", table_name="readings")
    op.drop_column("readings", "scheduled_analysis_at")
