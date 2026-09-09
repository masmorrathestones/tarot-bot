"""add whatsapp conversation state and inbound event tracking"""

from alembic import op
import sqlalchemy as sa

revision = "0003_add_whatsapp_conversations"
down_revision = "0002_add_reading_retry_tracking"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "whatsapp_conversations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "state",
            sa.String(length=40),
            nullable=False,
            server_default="AWAITING_QUESTION",
        ),
        sa.Column("pending_question", sa.String(length=500)),
        sa.Column("pending_context", sa.String(length=1000)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index(
        "ix_whatsapp_conversations_user_id",
        "whatsapp_conversations",
        ["user_id"],
        unique=True,
    )
    op.create_index(
        "ix_whatsapp_conversations_state",
        "whatsapp_conversations",
        ["state"],
    )

    op.create_table(
        "whatsapp_message_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "whatsapp_message_id",
            sa.String(length=200),
            nullable=False,
        ),
        sa.Column("from_number", sa.String(length=32), nullable=False),
        sa.Column("display_name", sa.String(length=120)),
        sa.Column("message_type", sa.String(length=30), nullable=False),
        sa.Column("text_body", sa.Text()),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default="RECEIVED",
        ),
        sa.Column("error_message", sa.Text()),
        sa.Column(
            "received_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("processed_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("whatsapp_message_id"),
    )
    op.create_index(
        "ix_whatsapp_message_events_whatsapp_message_id",
        "whatsapp_message_events",
        ["whatsapp_message_id"],
        unique=True,
    )
    op.create_index(
        "ix_whatsapp_message_events_status",
        "whatsapp_message_events",
        ["status"],
    )


def downgrade() -> None:
    op.drop_table("whatsapp_message_events")
    op.drop_table("whatsapp_conversations")
