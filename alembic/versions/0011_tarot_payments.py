"""add Tarot payments

Revision ID: 0011_tarot_payments
Revises: 0010_whatsapp_language
"""

from alembic import op
import sqlalchemy as sa


revision = "0011_tarot_payments"
down_revision = "0010_whatsapp_language"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tarot_payments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("conversation_id", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(length=20), nullable=False, server_default="stripe"),
        sa.Column("provider_session_id", sa.String(length=255), nullable=False),
        sa.Column("checkout_url", sa.Text(), nullable=False),
        sa.Column("amount_cents", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="usd"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="PENDING"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["conversation_id"], ["whatsapp_conversations.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("provider_session_id"),
    )
    op.create_index("ix_tarot_payments_user_id", "tarot_payments", ["user_id"])
    op.create_index("ix_tarot_payments_conversation_id", "tarot_payments", ["conversation_id"])
    op.create_index("ix_tarot_payments_provider_session_id", "tarot_payments", ["provider_session_id"], unique=True)
    op.create_index("ix_tarot_payments_status", "tarot_payments", ["status"])


def downgrade() -> None:
    op.drop_index("ix_tarot_payments_status", table_name="tarot_payments")
    op.drop_index("ix_tarot_payments_provider_session_id", table_name="tarot_payments")
    op.drop_index("ix_tarot_payments_conversation_id", table_name="tarot_payments")
    op.drop_index("ix_tarot_payments_user_id", table_name="tarot_payments")
    op.drop_table("tarot_payments")
