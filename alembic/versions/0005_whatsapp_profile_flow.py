"""add whatsapp onboarding and symbolic profile fields"""

from alembic import op
import sqlalchemy as sa

revision = "0005_whatsapp_profile_flow"
down_revision = "0004_whatsapp_outbound"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("user_profiles", sa.Column("birth_date", sa.Date(), nullable=True))
    op.add_column("user_profiles", sa.Column("birth_time", sa.Time(), nullable=True))
    op.add_column("user_profiles", sa.Column("zodiac_sign", sa.String(length=30), nullable=True))
    op.add_column("user_profiles", sa.Column("personal_number", sa.Integer(), nullable=True))
    op.add_column("user_profiles", sa.Column("personal_arcana_number", sa.Integer(), nullable=True))
    op.add_column("user_profiles", sa.Column("personal_arcana_name", sa.String(length=120), nullable=True))
    op.add_column("user_profiles", sa.Column("year_arcana_number", sa.Integer(), nullable=True))
    op.add_column("user_profiles", sa.Column("year_arcana_name", sa.String(length=120), nullable=True))
    op.add_column("user_profiles", sa.Column("year_arcana_reference_year", sa.Integer(), nullable=True))

    op.add_column(
        "whatsapp_conversations",
        sa.Column("whatsapp_number", sa.String(length=32), nullable=True),
    )
    op.execute(
        """
        UPDATE whatsapp_conversations AS wc
        SET whatsapp_number = u.whatsapp_number
        FROM users AS u
        WHERE wc.user_id = u.id
        """
    )
    op.alter_column("whatsapp_conversations", "whatsapp_number", nullable=False)
    op.create_index(
        "ix_whatsapp_conversations_whatsapp_number",
        "whatsapp_conversations",
        ["whatsapp_number"],
        unique=True,
    )
    op.alter_column("whatsapp_conversations", "user_id", nullable=True)


def downgrade() -> None:
    op.alter_column("whatsapp_conversations", "user_id", nullable=False)
    op.drop_index("ix_whatsapp_conversations_whatsapp_number", table_name="whatsapp_conversations")
    op.drop_column("whatsapp_conversations", "whatsapp_number")

    op.drop_column("user_profiles", "year_arcana_reference_year")
    op.drop_column("user_profiles", "year_arcana_name")
    op.drop_column("user_profiles", "year_arcana_number")
    op.drop_column("user_profiles", "personal_arcana_name")
    op.drop_column("user_profiles", "personal_arcana_number")
    op.drop_column("user_profiles", "personal_number")
    op.drop_column("user_profiles", "zodiac_sign")
    op.drop_column("user_profiles", "birth_time")
    op.drop_column("user_profiles", "birth_date")
