"""add natal chart profile fields"""

from alembic import op
import sqlalchemy as sa

revision = "0006_natal_chart"
down_revision = "0005_whatsapp_profile_flow"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("user_profiles", sa.Column("birth_place", sa.String(length=250), nullable=True))
    op.add_column("user_profiles", sa.Column("birth_latitude", sa.Float(), nullable=True))
    op.add_column("user_profiles", sa.Column("birth_longitude", sa.Float(), nullable=True))
    op.add_column("user_profiles", sa.Column("birth_timezone", sa.String(length=80), nullable=True))
    op.add_column("user_profiles", sa.Column("natal_chart", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("user_profiles", "natal_chart")
    op.drop_column("user_profiles", "birth_timezone")
    op.drop_column("user_profiles", "birth_longitude")
    op.drop_column("user_profiles", "birth_latitude")
    op.drop_column("user_profiles", "birth_place")
