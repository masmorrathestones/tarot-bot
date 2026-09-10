"""add profile analysis and payment currency choice token

Revision ID: 0012_profile_analysis
Revises: 0011_tarot_payments
"""

from alembic import op
import sqlalchemy as sa


revision = "0012_profile_analysis"
down_revision = "0011_tarot_payments"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("user_profiles", sa.Column("profile_analysis", sa.Text(), nullable=True))
    op.add_column("user_profiles", sa.Column("profile_analysis_summary", sa.Text(), nullable=True))
    op.add_column("user_profiles", sa.Column("profile_analysis_reference_year", sa.Integer(), nullable=True))
    op.add_column(
        "user_profiles",
        sa.Column("profile_analysis_created_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "tarot_payments",
        sa.Column("checkout_choice_token", sa.String(length=64), nullable=True),
    )
    op.create_index(
        "ix_tarot_payments_checkout_choice_token",
        "tarot_payments",
        ["checkout_choice_token"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_tarot_payments_checkout_choice_token", table_name="tarot_payments")
    op.drop_column("tarot_payments", "checkout_choice_token")
    op.drop_column("user_profiles", "profile_analysis_created_at")
    op.drop_column("user_profiles", "profile_analysis_reference_year")
    op.drop_column("user_profiles", "profile_analysis_summary")
    op.drop_column("user_profiles", "profile_analysis")
