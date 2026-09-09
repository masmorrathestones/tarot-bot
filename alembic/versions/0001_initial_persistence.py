"""create users profiles readings and drawn cards"""

from alembic import op
import sqlalchemy as sa

revision = "0001_initial_persistence"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("whatsapp_number", sa.String(32), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True),
            server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("whatsapp_number"),
    )
    op.create_index(
        "ix_users_whatsapp_number", "users",
        ["whatsapp_number"], unique=True
    )

    op.create_table(
        "user_profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id", sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False
        ),
        sa.Column("sun_sign", sa.String(30)),
        sa.Column("moon_sign", sa.String(30)),
        sa.Column("rising_sign", sa.String(30)),
        sa.Column("mbti", sa.String(10)),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True),
            server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index(
        "ix_user_profiles_user_id", "user_profiles",
        ["user_id"], unique=True
    )

    op.create_table(
        "readings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id", sa.Integer(),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False
        ),
        sa.Column("deck_code", sa.String(60), nullable=False),
        sa.Column("spread_code", sa.String(80), nullable=False),
        sa.Column("question", sa.String(500), nullable=False),
        sa.Column("context", sa.String(1000)),
        sa.Column("allow_reversed", sa.Boolean(), nullable=False),
        sa.Column("profile_snapshot", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("ai_model", sa.String(120)),
        sa.Column("prompt_version", sa.String(40), nullable=False),
        sa.Column("knowledge_version", sa.String(40), nullable=False),
        sa.Column("narrative", sa.Text()),
        sa.Column("card_analysis", sa.Text()),
        sa.Column("synthesis", sa.Text()),
        sa.Column("error_message", sa.Text()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            server_default=sa.func.now(), nullable=False
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_readings_user_id", "readings", ["user_id"])
    op.create_index("ix_readings_status", "readings", ["status"])

    op.create_table(
        "drawn_cards",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "reading_id", sa.Integer(),
            sa.ForeignKey("readings.id", ondelete="CASCADE"),
            nullable=False
        ),
        sa.Column("card_code", sa.String(80), nullable=False),
        sa.Column("card_name", sa.String(120), nullable=False),
        sa.Column("position_index", sa.Integer(), nullable=False),
        sa.Column("position_code", sa.String(80), nullable=False),
        sa.Column("position_name", sa.String(120), nullable=False),
        sa.Column("position_description", sa.String(500), nullable=False),
        sa.Column("orientation", sa.String(20), nullable=False),
        sa.UniqueConstraint(
            "reading_id", "position_index",
            name="uq_drawn_cards_reading_position"
        ),
    )
    op.create_index(
        "ix_drawn_cards_reading_id", "drawn_cards", ["reading_id"]
    )


def downgrade() -> None:
    op.drop_table("drawn_cards")
    op.drop_table("readings")
    op.drop_table("user_profiles")
    op.drop_table("users")
