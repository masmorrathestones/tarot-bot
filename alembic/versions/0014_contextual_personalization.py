"""add contextual personalization

Revision ID: 0014_contextual_personalization
Revises: 0013_user_admin
"""

from alembic import op
import sqlalchemy as sa

revision = "0014_contextual_personalization"
down_revision = "0013_user_admin"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_relevant_information",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("text", sa.String(length=240), nullable=False),
        sa.Column("selected_for_next_reading", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_user_relevant_information_user_id", "user_relevant_information", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_user_relevant_information_user_id", table_name="user_relevant_information")
    op.drop_table("user_relevant_information")
