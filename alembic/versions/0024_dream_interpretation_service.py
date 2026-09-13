"""add dream interpretation service

Revision ID: 0024_dream_interpretation
Revises: 0023_dream_symbol_catalog
"""
from alembic import op
import sqlalchemy as sa

revision = "0024_dream_interpretation"
down_revision = "0023_dream_symbol_catalog"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "dream_interpretations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("conversation_id", sa.Integer(), sa.ForeignKey("whatsapp_conversations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("payment_id", sa.Integer(), sa.ForeignKey("tarot_payments.id", ondelete="SET NULL")),
        sa.Column("language", sa.String(5), nullable=False, server_default="pt"),
        sa.Column("status", sa.String(40), nullable=False),
        sa.Column("dream_text", sa.Text(), nullable=False),
        sa.Column("linguistic_analogies", sa.JSON()),
        sa.Column("contextual_questions", sa.JSON()),
        sa.Column("answers", sa.JSON()),
        sa.Column("current_question_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("relevant_facts", sa.JSON()),
        sa.Column("matched_symbols", sa.JSON()),
        sa.Column("final_analysis", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
    )
    for column in ("user_id", "conversation_id", "payment_id", "status"):
        op.create_index(f"ix_dream_interpretations_{column}", "dream_interpretations", [column])


def downgrade() -> None:
    op.drop_table("dream_interpretations")
