"""add WhatsApp conversation language

Revision ID: 0010_whatsapp_language
Revises: 0009_mystic_intuitions
"""

from alembic import op
import sqlalchemy as sa


revision = "0010_whatsapp_language"
down_revision = "0009_mystic_intuitions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "whatsapp_conversations",
        sa.Column("language", sa.String(length=5), nullable=False, server_default="en"),
    )
    op.alter_column("whatsapp_conversations", "language", server_default=None)


def downgrade() -> None:
    op.drop_column("whatsapp_conversations", "language")
