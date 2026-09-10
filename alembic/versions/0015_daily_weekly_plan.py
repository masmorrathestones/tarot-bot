"""add daily tarot and weekly astrology plan

Revision ID: 0015_daily_weekly_plan
Revises: 0014_contextual_personalization
"""

from alembic import op
import sqlalchemy as sa


revision = "0015_daily_weekly_plan"
down_revision = "0014_contextual_personalization"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 0013 removed the database default after backfilling is_admin. The ORM does
    # not map that column, so new user INSERTs omit it; keep a safe false default.
    op.alter_column("users", "is_admin", server_default=sa.false())

    op.add_column("user_profiles", sa.Column("current_place", sa.String(length=250), nullable=True))
    op.add_column("user_profiles", sa.Column("current_latitude", sa.Float(), nullable=True))
    op.add_column("user_profiles", sa.Column("current_longitude", sa.Float(), nullable=True))
    op.add_column("user_profiles", sa.Column("current_timezone", sa.String(length=80), nullable=True))
    op.add_column("user_profiles", sa.Column("current_location_updated_at", sa.DateTime(timezone=True), nullable=True))

    op.create_table(
        "daily_weekly_plans",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="DRAFT"),
        sa.Column("billing_type", sa.String(length=20), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=True),
        sa.Column("amount_cents", sa.Integer(), nullable=True),
        sa.Column("daily_time", sa.Time(), nullable=True),
        sa.Column("weekly_weekday", sa.Integer(), nullable=True),
        sa.Column("weekly_time", sa.Time(), nullable=True),
        sa.Column("schedule_timezone", sa.String(length=80), nullable=True),
        sa.Column("checkout_token", sa.String(length=80), nullable=True),
        sa.Column("stripe_checkout_session_id", sa.String(length=255), nullable=True),
        sa.Column("stripe_customer_id", sa.String(length=255), nullable=True),
        sa.Column("stripe_subscription_id", sa.String(length=255), nullable=True),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancel_at_period_end", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("next_daily_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_weekly_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_daily_sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_weekly_sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", name="uq_daily_weekly_plans_user_id"),
        sa.UniqueConstraint("checkout_token", name="uq_daily_weekly_plans_checkout_token"),
        sa.UniqueConstraint("stripe_checkout_session_id", name="uq_daily_weekly_plans_checkout_session_id"),
        sa.UniqueConstraint("stripe_subscription_id", name="uq_daily_weekly_plans_subscription_id"),
    )
    op.create_index("ix_daily_weekly_plans_user_id", "daily_weekly_plans", ["user_id"])
    op.create_index("ix_daily_weekly_plans_status", "daily_weekly_plans", ["status"])
    op.create_index("ix_daily_weekly_plans_next_daily_at", "daily_weekly_plans", ["next_daily_at"])
    op.create_index("ix_daily_weekly_plans_next_weekly_at", "daily_weekly_plans", ["next_weekly_at"])
    op.create_index("ix_daily_weekly_plans_checkout_token", "daily_weekly_plans", ["checkout_token"])
    op.create_index("ix_daily_weekly_plans_stripe_customer_id", "daily_weekly_plans", ["stripe_customer_id"])
    op.create_index("ix_daily_weekly_plans_stripe_subscription_id", "daily_weekly_plans", ["stripe_subscription_id"])

    op.create_table(
        "plan_deliveries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("plan_id", sa.Integer(), sa.ForeignKey("daily_weekly_plans.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("delivery_type", sa.String(length=20), nullable=False),
        sa.Column("scheduled_for", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="PROCESSING"),
        sa.Column("card_code", sa.String(length=80), nullable=True),
        sa.Column("orientation", sa.String(length=20), nullable=True),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("plan_id", "delivery_type", "scheduled_for", name="uq_plan_delivery_slot"),
    )
    op.create_index("ix_plan_deliveries_plan_id", "plan_deliveries", ["plan_id"])
    op.create_index("ix_plan_deliveries_user_id", "plan_deliveries", ["user_id"])
    op.create_index("ix_plan_deliveries_delivery_type", "plan_deliveries", ["delivery_type"])
    op.create_index("ix_plan_deliveries_status", "plan_deliveries", ["status"])


def downgrade() -> None:
    op.drop_table("plan_deliveries")
    op.drop_table("daily_weekly_plans")
    op.drop_column("user_profiles", "current_location_updated_at")
    op.drop_column("user_profiles", "current_timezone")
    op.drop_column("user_profiles", "current_longitude")
    op.drop_column("user_profiles", "current_latitude")
    op.drop_column("user_profiles", "current_place")
    op.alter_column("users", "is_admin", server_default=None)
