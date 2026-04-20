from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.transaction import Transaction
from app.models.receipt import Receipt
from app.models.user import User
from app.utils.auth import get_current_user
from app.utils.db import get_db


router = APIRouter(prefix="/deductions")

CURRENT_FY = "FY2025-26"
LIMIT_80C = 150_000
LIMIT_80D = 25_000
LIMIT_80D_SENIOR = 50_000


def _f(v) -> float:
    if v is None:
        return 0.0
    return float(v) if isinstance(v, Decimal) else float(v)


@router.get("/summary")
async def deductions_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    financial_year: Optional[str] = Query(CURRENT_FY),
):
    """
    Returns a comprehensive deduction summary for 80C, 80D, and other sections
    pulled from both transactions and receipts.
    """
    # --- Transactions ---
    q_txn = select(Transaction).where(
        Transaction.user_id == current_user.id,
        Transaction.deductible == True,
    )
    if financial_year:
        q_txn = q_txn.where(Transaction.financial_year == financial_year)
    txn_result = await db.execute(q_txn)
    txns = txn_result.scalars().all()

    # --- Receipts ---
    q_rec = select(Receipt).where(Receipt.user_id == current_user.id)
    if financial_year:
        q_rec = q_rec.where(Receipt.financial_year == financial_year)
    rec_result = await db.execute(q_rec)
    receipts = rec_result.scalars().all()

    # Aggregate from transactions
    by_section: dict[str, float] = {}
    for t in txns:
        key = t.section or "Other"
        by_section[key] = by_section.get(key, 0.0) + abs(_f(t.amount_inr))

    # Add receipt-based 80C/80D
    receipt_80c = sum(_f(r.amount) for r in receipts if r.section_80c)
    receipt_80d = sum(_f(r.amount) for r in receipts if r.section_80d)
    by_section["80C"] = by_section.get("80C", 0.0) + receipt_80c
    by_section["80D"] = by_section.get("80D", 0.0) + receipt_80d

    raw_80c = by_section.get("80C", 0.0)
    raw_80d = by_section.get("80D", 0.0)
    effective_80c = min(raw_80c, LIMIT_80C)
    effective_80d = min(raw_80d, LIMIT_80D)
    remaining_80c = max(0, LIMIT_80C - raw_80c)
    remaining_80d = max(0, LIMIT_80D - raw_80d)

    by_section_detail = [
        {
            "section": k,
            "raw_amount": round(v, 2),
            "effective_amount": round(min(v, LIMIT_80C) if k == "80C" else min(v, LIMIT_80D) if k == "80D" else v, 2),
            "limit": LIMIT_80C if k == "80C" else LIMIT_80D if k == "80D" else None,
        }
        for k, v in sorted(by_section.items(), key=lambda x: x[0])
    ]

    total_effective = effective_80c + effective_80d + sum(
        v for k, v in by_section.items() if k not in ("80C", "80D")
    )

    return {
        "financial_year": financial_year,
        "by_section": by_section_detail,
        "summary": {
            "80C": {
                "raw": round(raw_80c, 2),
                "effective": round(effective_80c, 2),
                "limit": LIMIT_80C,
                "remaining": round(remaining_80c, 2),
                "utilization_pct": round(min(raw_80c / LIMIT_80C, 1.0) * 100, 1),
            },
            "80D": {
                "raw": round(raw_80d, 2),
                "effective": round(effective_80d, 2),
                "limit": LIMIT_80D,
                "remaining": round(remaining_80d, 2),
                "utilization_pct": round(min(raw_80d / LIMIT_80D, 1.0) * 100, 1),
            },
        },
        "total_effective_deductions": round(total_effective, 2),
        "tips": [
            f"You can invest ₹{remaining_80c:,.0f} more in 80C instruments (PPF, ELSS, LIC) to maximize the ₹1.5L limit."
            if remaining_80c > 0
            else "80C limit fully utilized! ✅",
            f"You can invest ₹{remaining_80d:,.0f} more in health insurance to maximize the 80D limit."
            if remaining_80d > 0
            else "80D limit fully utilized! ✅",
        ],
        "currency": "INR",
    }


# Legacy endpoint (/deductions/80) kept for backward compatibility
@router.get("/80")
async def list_80_deductions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    q = select(Transaction).where(
        Transaction.user_id == current_user.id,
        Transaction.deductible == True,
    ).where(Transaction.section.in_(["80C", "80D"]))
    result = await db.execute(q)
    txns = result.scalars().all()
    return {
        "ok": True,
        "items": [
            {"id": str(t.id), "date": str(t.txn_date), "narration": t.description,
             "amount": float(_f(t.amount_inr)), "section": t.section}
            for t in txns
        ],
        "currency": "INR",
    }
