"""Initial migration — create all TaxFlow AI tables.

Revision ID: 0001_initial
Revises:
Create Date: 2026-04-08

Tables created:
  users, transactions, receipts, tds_entries, advance_tax,
  deductions_80, gst_credits, matches, notifications, tax_reports
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── users ──────────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("full_name", sa.String(200), nullable=True),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("hashed_password", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("user_type", sa.String(20), nullable=True),
        sa.Column("itr_form", sa.String(30), nullable=True),
        sa.Column("google_sub", sa.String(255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_google_sub", "users", ["google_sub"], unique=True)

    # ── transactions ───────────────────────────────────────────────────────────
    op.create_table(
        "transactions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("txn_date", sa.Date(), nullable=False),
        sa.Column("description", sa.String(500), nullable=False),
        sa.Column("amount_inr", sa.Numeric(12, 2), nullable=False),
        sa.Column("direction", sa.String(10), nullable=False),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("deductible", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("section", sa.String(30), nullable=True),
        sa.Column("financial_year", sa.String(9), nullable=True),
        sa.Column("merchant", sa.String(200), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_transactions_user_id", "transactions", ["user_id"])
    op.create_index("ix_transactions_txn_date", "transactions", ["txn_date"])
    op.create_index("ix_transactions_financial_year", "transactions", ["financial_year"])

    # ── receipts ───────────────────────────────────────────────────────────────
    op.create_table(
        "receipts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("financial_year", sa.String(20), nullable=True),
        sa.Column("merchant", sa.String(200), nullable=True),
        sa.Column("amount", sa.Numeric(12, 2), nullable=True),
        sa.Column("date", sa.Date(), nullable=True),
        sa.Column("gstin", sa.String(20), nullable=True),
        sa.Column("gst_amount", sa.Numeric(12, 2), nullable=True),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("section_80c", sa.Boolean(), server_default="false"),
        sa.Column("section_80d", sa.Boolean(), server_default="false"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_receipts_user_id", "receipts", ["user_id"])

    # ── tds_entries ────────────────────────────────────────────────────────────
    op.create_table(
        "tds_entries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("deductor_name", sa.String(200), nullable=True),
        sa.Column("tan", sa.String(30), nullable=True),
        sa.Column("section", sa.String(20), nullable=True),
        sa.Column("quarter", sa.String(5), nullable=True),
        sa.Column("financial_year", sa.String(9), nullable=False),
        sa.Column("credited_date", sa.Date(), nullable=True),
        sa.Column("amount_credited_inr", sa.Numeric(14, 2), nullable=True),
        sa.Column("tds_amount_inr", sa.Numeric(14, 2), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_tds_entries_user_id", "tds_entries", ["user_id"])

    # ── advance_tax ────────────────────────────────────────────────────────────
    op.create_table(
        "advance_tax",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("financial_year", sa.String(9), nullable=False),
        sa.Column("instalment_label", sa.String(30), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("paid_date", sa.Date(), nullable=True),
        sa.Column("amount_inr", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("challan_ref", sa.String(80), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_advance_tax_user_id", "advance_tax", ["user_id"])
    op.create_index("ix_advance_tax_financial_year", "advance_tax", ["financial_year"])

    # ── deductions_80 ──────────────────────────────────────────────────────────
    op.create_table(
        "deductions_80",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("section", sa.String(10), nullable=False),
        sa.Column("description", sa.String(300), nullable=True),
        sa.Column("amount_inr", sa.Numeric(14, 2), nullable=False),
        sa.Column("financial_year", sa.String(9), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_deductions_80_user_id", "deductions_80", ["user_id"])

    # ── gst_credits ────────────────────────────────────────────────────────────
    op.create_table(
        "gst_credits",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("receipt_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("gstin", sa.String(20), nullable=True),
        sa.Column("itc_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("gst_rate", sa.String(10), nullable=True),
        sa.Column("period", sa.String(10), nullable=True),
        sa.Column("claimed", sa.Boolean(), server_default="false"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_gst_credits_user_id", "gst_credits", ["user_id"])

    # ── matches ────────────────────────────────────────────────────────────────
    op.create_table(
        "matches",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("transaction_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("receipt_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_matches_user_id", "matches", ["user_id"])

    # ── notifications ──────────────────────────────────────────────────────────
    op.create_table(
        "notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("category", sa.String(50), nullable=True),
        sa.Column("is_read", sa.Boolean(), server_default="false"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])

    # ── tax_reports ────────────────────────────────────────────────────────────
    op.create_table(
        "tax_reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("financial_year", sa.String(9), nullable=False),
        sa.Column("total_income", sa.Numeric(16, 2), nullable=True),
        sa.Column("total_deductions", sa.Numeric(16, 2), nullable=True),
        sa.Column("taxable_income", sa.Numeric(16, 2), nullable=True),
        sa.Column("tax_liability", sa.Numeric(16, 2), nullable=True),
        sa.Column("recommendation", sa.String(20), nullable=True),
        sa.Column("report_json", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_tax_reports_user_id", "tax_reports", ["user_id"])


def downgrade() -> None:
    op.drop_table("tax_reports")
    op.drop_table("notifications")
    op.drop_table("matches")
    op.drop_table("gst_credits")
    op.drop_table("deductions_80")
    op.drop_table("advance_tax")
    op.drop_table("tds_entries")
    op.drop_table("receipts")
    op.drop_table("transactions")
    op.drop_table("users")
