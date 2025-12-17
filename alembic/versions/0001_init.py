"""init

Revision ID: 0001_init
Revises: 
Create Date: 2025-12-17

"""
from alembic import op
import sqlalchemy as sa

revision = "0001_init"
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        "accounts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=128), nullable=False, unique=True),
        sa.Column("asset", sa.String(length=16), nullable=False),
        sa.Column("type", sa.String(length=16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "transactions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("reference", sa.String(length=64), nullable=False, index=True),
        sa.Column("description", sa.String(length=256), nullable=True),
        sa.Column("asset", sa.String(length=16), nullable=False),
        sa.Column("idempotency_key", sa.String(length=128), nullable=False, unique=True, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "postings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("transaction_id", sa.Integer(), sa.ForeignKey("transactions.id"), nullable=False, index=True),
        sa.Column("account_id", sa.Integer(), sa.ForeignKey("accounts.id"), nullable=False, index=True),
        sa.Column("direction", sa.String(length=6), nullable=False),
        sa.Column("amount", sa.Numeric(18, 6), nullable=False),
    )
    op.create_table(
        "events_outbox",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_table(
        "reconciliation_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("summary_json", sa.Text(), nullable=True),
    )

def downgrade() -> None:
    op.drop_table("reconciliation_runs")
    op.drop_table("events_outbox")
    op.drop_table("postings")
    op.drop_table("transactions")
    op.drop_table("accounts")
