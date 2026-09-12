"""add past life Tarot flow

Revision ID: 0022_past_life_tarot
Revises: 0021_scheduled_analysis
Create Date: 2026-09-11
"""

from alembic import op
import sqlalchemy as sa

revision = "0022_past_life_tarot"
down_revision = "0021_scheduled_analysis"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("tarot_payments", sa.Column("purpose", sa.String(40), nullable=False, server_default="tarot_reading"))
    op.create_table(
        "past_life_readings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("conversation_id", sa.Integer(), sa.ForeignKey("whatsapp_conversations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(40), nullable=False),
        sa.Column("meditation_started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("meditation_completed_at", sa.DateTime(timezone=True)),
        sa.Column("meditation_word", sa.String(120)),
        sa.Column("word_arcana_number", sa.Integer()),
        sa.Column("word_arcana_name", sa.String(120)),
        sa.Column("profile_snapshot", sa.JSON(), nullable=False),
        sa.Column("personality_cards", sa.JSON()),
        sa.Column("personality_analysis", sa.Text()),
        sa.Column("theme_candidates", sa.JSON()),
        sa.Column("selected_theme", sa.String(300)),
        sa.Column("intuitive_question", sa.Text()),
        sa.Column("intuitive_answer", sa.Boolean()),
        sa.Column("second_cards", sa.JSON()),
        sa.Column("final_analysis", sa.Text()),
        sa.Column("helped_answer", sa.Boolean()),
        sa.Column("helped_answer_text", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_past_life_readings_user_id", "past_life_readings", ["user_id"])
    op.create_index("ix_past_life_readings_conversation_id", "past_life_readings", ["conversation_id"])
    op.create_index("ix_past_life_readings_status", "past_life_readings", ["status"])


def downgrade() -> None:
    op.drop_table("past_life_readings")
    op.drop_column("tarot_payments", "purpose")
