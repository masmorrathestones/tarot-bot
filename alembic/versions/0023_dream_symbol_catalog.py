"""add multilingual dream symbol catalogue

Revision ID: 0023_dream_symbol_catalog
Revises: 0022_past_life_tarot
Create Date: 2026-09-13
"""

from alembic import op
import sqlalchemy as sa

from app.dreams.catalog import INITIAL_DREAM_SYMBOLS

revision = "0023_dream_symbol_catalog"
down_revision = "0022_past_life_tarot"
branch_labels = None
depends_on = None


def upgrade() -> None:
    table = op.create_table(
        "dream_symbols",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("canonical_key", sa.String(120), nullable=False),
        sa.Column("name_pt", sa.String(160), nullable=False),
        sa.Column("name_en", sa.String(160), nullable=False),
        sa.Column("name_es", sa.String(160), nullable=False),
        sa.Column("meaning_pt", sa.Text(), nullable=False),
        sa.Column("meaning_en", sa.Text(), nullable=False),
        sa.Column("meaning_es", sa.Text(), nullable=False),
        sa.Column("interpretation_type", sa.String(24), nullable=False),
        sa.Column("tradition", sa.String(40), nullable=False),
        sa.Column("source_book", sa.String(180), nullable=False),
        sa.Column("source_reference", sa.String(80), nullable=False),
        sa.Column("context_note_pt", sa.Text()),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "interpretation_type IN ('MYSTICAL', 'PSYCHOANALYTIC')",
            name="ck_dream_symbols_interpretation_type",
        ),
        sa.UniqueConstraint(
            "canonical_key", "interpretation_type", "source_book", "source_reference",
            name="uq_dream_symbols_key_type_source",
        ),
    )
    for column in ("canonical_key", "name_pt", "name_en", "name_es", "interpretation_type"):
        op.create_index(f"ix_dream_symbols_{column}", "dream_symbols", [column])
    op.bulk_insert(table, list(INITIAL_DREAM_SYMBOLS))


def downgrade() -> None:
    op.drop_table("dream_symbols")
