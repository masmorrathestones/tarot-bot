"""add administrator flag to users

Revision ID: 0013_user_admin
Revises: 0012_profile_analysis
"""

from alembic import op
import sqlalchemy as sa


revision = "0013_user_admin"
down_revision = "0012_profile_analysis"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "is_admin",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.alter_column("users", "is_admin", server_default=None)


def downgrade() -> None:
    op.drop_column("users", "is_admin")
