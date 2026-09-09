"""Add persisted WhatsApp Tarot ritual flow state.

Revision ID: 0008_whatsapp_tarot_flows
Revises: 0007_english_profile_values
"""

from alembic import op
import sqlalchemy as sa


revision = "0008_whatsapp_tarot_flows"
down_revision = "0007_english_profile_values"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "whatsapp_tarot_flows",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "conversation_id",
            sa.Integer(),
            sa.ForeignKey("whatsapp_conversations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "conversation_id",
            name="uq_whatsapp_tarot_flows_conversation_id",
        ),
    )
    op.create_index(
        "ix_whatsapp_tarot_flows_conversation_id",
        "whatsapp_tarot_flows",
        ["conversation_id"],
        unique=True,
    )


def downgrade():
    op.drop_index(
        "ix_whatsapp_tarot_flows_conversation_id",
        table_name="whatsapp_tarot_flows",
    )
    op.drop_table("whatsapp_tarot_flows")
