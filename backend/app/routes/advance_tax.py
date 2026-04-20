from datetime import date, timedelta
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.transaction import Transaction
from app.models.tds_entry import TDSEntry
from app.models.user import User
from app.utils.auth import get_current_user
from app.utils.db import get_db
from app.utils.tax_calc import calculate_tax

router = APIRouter(prefix="/advance-tax")

CURRENT_FY = "FY2025-26"

# FY 2025-26 advance tax due dates and cumulative percentages
INSTALMENTS = [
    {"label": "1st Instalment", "due_date": date(2025, 6, 15), "cumulative_pct": 0.15, "quarter": "Q1"},
    {"label": "2nd Instalment", "due_date": date(2025, 9, 15), "cumulative_pct": 0.45, "quarter": "Q2"},
    {"label": "3rd Instalment", "due_date": date(2025, 12, 15), "cumulative_pct": 0.75, "quarter": "Q3"},
    {"label": "4th Instalment", "due_date": date(2026, 3, 15), "cumulative_pct": 1.00, "quarter": "Q4"},
]


def _f(v) -> float:
    if v is None:
        return 0.0
    return float(v) if isinstance(v, Decimal) else float(v)


@router.get("/schedule")
async def get_advance_tax_schedule(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    financial_year: Optional[str] = Query(CURRENT_FY),
):
    """
    Calculates advance tax instalments for the current user based on their
    actual income from uploaded transactions, minus deductions.
    Uses FY 2025-26 slab rates + 4% cess.
    """
    # Fetch user's transactions
    q = select(Transaction).where(Transaction.user_id == current_user.id)
    if financial_year:
        q = q.where(Transaction.financial_year == financial_year)
    result = await db.execute(q)
    txns = result.scalars().all()

    # Fetch TDS entries (already deducted at source)
    tds_result = await db.execute(
        select(TDSEntry).where(TDSEntry.user_id == current_user.id)
    )
    tds_entries = tds_result.scalars().all()

    total_income = sum(_f(t.amount_inr) for t in txns if t.direction == "in")
    total_expenses = sum(abs(_f(t.amount_inr)) for t in txns if t.direction == "out" and t.deductible)
    deduction_80c = float(min(sum(abs(_f(t.amount_inr)) for t in txns if (t.section or "") == "80C"), 150_000))
    deduction_80d = float(min(sum(abs(_f(t.amount_inr)) for t in txns if (t.section or "") == "80D"), 25_000))
    taxable_income = max(0.0, total_income - total_expenses - deduction_80c - deduction_80d)

    total_tax_liability = calculate_tax(taxable_income)
    total_tds = sum(_f(e.tds_amount_inr) for e in tds_entries)
    net_tax_payable = max(0.0, total_tax_liability - total_tds)

    today = date.today()
    schedule = []
    prev_cumulative = 0.0

    for inst in INSTALMENTS:
        cumulative_amount = round(net_tax_payable * inst["cumulative_pct"], 2)
        instalment_amount = round(cumulative_amount - prev_cumulative, 2)
        prev_cumulative = cumulative_amount

        is_overdue = today > inst["due_date"]
        is_upcoming = not is_overdue and (inst["due_date"] - today).days <= 30

        schedule.append({
            "label": inst["label"],
            "quarter": inst["quarter"],
            "due_date": str(inst["due_date"]),
            "cumulative_pct": int(inst["cumulative_pct"] * 100),
            "cumulative_amount": cumulative_amount,
            "instalment_amount": instalment_amount,
            "status": "overdue" if is_overdue else ("due_soon" if is_upcoming else "upcoming"),
            "days_remaining": max(0, (inst["due_date"] - today).days),
        })

    # Determine threshold: advance tax required only if liability > ₹10,000
    advance_tax_required = net_tax_payable > 10_000

    return {
        "financial_year": financial_year,
        "advance_tax_required": advance_tax_required,
        "total_income": round(total_income, 2),
        "taxable_income": round(taxable_income, 2),
        "total_tax_liability": round(total_tax_liability, 2),
        "tds_already_deducted": round(total_tds, 2),
        "net_tax_payable": round(net_tax_payable, 2),
        "schedule": schedule,
        "note": "No advance tax required — net liability ≤ ₹10,000." if not advance_tax_required
                else "Pay advance tax by each due date to avoid interest u/s 234B & 234C.",
        "currency": "INR",
    }


@router.get("/due-soon")
async def advance_tax_due_soon(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Returns only upcoming/overdue advance tax instalments in the next 45 days."""
    today = date.today()
    due_soon = [
        inst for inst in INSTALMENTS
        if 0 <= (inst["due_date"] - today).days <= 45 or today > inst["due_date"]
    ]
    return {
        "upcoming_instalments": [
            {
                "label": i["label"],
                "due_date": str(i["due_date"]),
                "quarter": i["quarter"],
                "status": "overdue" if today > i["due_date"] else "due_soon",
                "days_remaining": max(0, (i["due_date"] - today).days),
            }
            for i in due_soon
        ]
    }
