"""Add hidden mystic intuition modifiers for readings.

Revision ID: 0009_mystic_intuitions
Revises: 0008_whatsapp_tarot_flows
"""

from alembic import op
import sqlalchemy as sa


revision = "0009_mystic_intuitions"
down_revision = "0008_whatsapp_tarot_flows"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "reading_mystic_intuitions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "reading_id",
            sa.Integer(),
            sa.ForeignKey("readings.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "reading_id",
            name="uq_reading_mystic_intuitions_reading_id",
        ),
    )
    op.create_index(
        "ix_reading_mystic_intuitions_reading_id",
        "reading_mystic_intuitions",
        ["reading_id"],
        unique=True,
    )


def downgrade():
    op.drop_index(
        "ix_reading_mystic_intuitions_reading_id",
        table_name="reading_mystic_intuitions",
    )
    op.drop_table("reading_mystic_intuitions")
