"""add whatsapp outbound message tracking"""

from alembic import op
import sqlalchemy as sa

revision = "0004_whatsapp_outbound"
down_revision = "0003_add_whatsapp_conversations"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "whatsapp_outbound_messages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("whatsapp_message_id", sa.String(length=200), nullable=False),
        sa.Column("to_number", sa.String(length=32), nullable=False),
        sa.Column("text_body", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="ACCEPTED"),
        sa.Column("provider_status", sa.String(length=30)),
        sa.Column("error_code", sa.Integer()),
        sa.Column("error_title", sa.String(length=500)),
        sa.Column("error_message", sa.Text()),
        sa.Column(
            "sent_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("status_updated_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("whatsapp_message_id"),
    )
    op.create_index(
        "ix_whatsapp_outbound_messages_whatsapp_message_id",
        "whatsapp_outbound_messages",
        ["whatsapp_message_id"],
        unique=True,
    )
    op.create_index(
        "ix_whatsapp_outbound_messages_to_number",
        "whatsapp_outbound_messages",
        ["to_number"],
    )
    op.create_index(
        "ix_whatsapp_outbound_messages_status",
        "whatsapp_outbound_messages",
        ["status"],
    )


def downgrade() -> None:
    op.drop_table("whatsapp_outbound_messages")
