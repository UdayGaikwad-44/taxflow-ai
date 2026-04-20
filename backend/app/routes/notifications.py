from datetime import date, timedelta
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.transaction import Transaction
from app.models.tds_entry import TDSEntry
from app.models.receipt import Receipt
from app.models.user import User
from app.utils.auth import get_current_user
from app.utils.db import get_db

router = APIRouter(prefix="/notifications")

# FY 2025-26 statutory deadlines
STATUTORY_DEADLINES = [
    {"title": "Advance Tax — Q1 (15%)", "date": date(2025, 6, 15), "category": "advance_tax", "priority": "high"},
    {"title": "Advance Tax — Q2 (45%)", "date": date(2025, 9, 15), "category": "advance_tax", "priority": "high"},
    {"title": "Advance Tax — Q3 (75%)", "date": date(2025, 12, 15), "category": "advance_tax", "priority": "high"},
    {"title": "Advance Tax — Q4 (100%)", "date": date(2026, 3, 15), "category": "advance_tax", "priority": "high"},
    {"title": "GST GSTR-1 Filing — Mar 2026", "date": date(2026, 4, 11), "category": "gst", "priority": "medium"},
    {"title": "ITR Filing Deadline — FY 2025-26", "date": date(2026, 7, 31), "category": "itr", "priority": "high"},
    {"title": "TDS Form 16 / 16A Issue Deadline", "date": date(2026, 6, 15), "category": "tds", "priority": "medium"},
    {"title": "Tax Audit Deadline (if applicable)", "date": date(2026, 9, 30), "category": "audit", "priority": "medium"},
]

WARN_DAYS = 30  # notify this many days in advance


def _f(v) -> float:
    if v is None:
        return 0.0
    return float(v) if isinstance(v, Decimal) else float(v)


@router.get("")
async def list_notifications(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns all relevant notifications for the user including:
    - Upcoming statutory tax deadlines
    - Data-driven alerts from their transaction history
    """
    today = date.today()
    notifications = []
    nid = 1

    # --- 1. Statutory deadlines ---
    for dl in STATUTORY_DEADLINES:
        days_left = (dl["date"] - today).days
        if days_left < 0:
            status = "overdue"
        elif days_left <= WARN_DAYS:
            status = "due_soon"
        else:
            status = "upcoming"

        if status in ("overdue", "due_soon"):
            notifications.append({
                "id": nid,
                "type": "deadline",
                "category": dl["category"],
                "priority": dl["priority"],
                "title": dl["title"],
                "message": f"Due on {dl['date'].strftime('%d %b %Y')}. "
                           + ("Overdue!" if status == "overdue" else f"{days_left} day(s) remaining."),
                "due_date": str(dl["date"]),
                "status": status,
                "days_remaining": max(0, days_left),
            })
            nid += 1

    # --- 2. Data-driven alerts from transactions ---
    txn_result = await db.execute(
        select(Transaction).where(Transaction.user_id == current_user.id)
    )
    txns = txn_result.scalars().all()

    rec_result = await db.execute(
        select(Receipt).where(Receipt.user_id == current_user.id)
    )
    receipts = rec_result.scalars().all()

    tds_result = await db.execute(
        select(TDSEntry).where(TDSEntry.user_id == current_user.id)
    )
    tds_entries = tds_result.scalars().all()

    total_income = sum(_f(t.amount_inr) for t in txns if t.direction == "in")
    total_80c = sum(abs(_f(t.amount_inr)) for t in txns if (t.section or "") == "80C")
    total_80c += sum(_f(r.amount) for r in receipts if r.section_80c)
    gst_receipts = [r for r in receipts if (_f(r.gst_amount) or 0) > 0]

    # 80C under-utilized
    if total_80c < 100_000:
        remaining = 150_000 - total_80c
        notifications.append({
            "id": nid,
            "type": "alert",
            "category": "deduction",
            "priority": "medium",
            "title": "80C Limit Under-utilized",
            "message": f"Invest ₹{remaining:,.0f} more in PPF / ELSS / LIC to claim full ₹1.5L 80C deduction.",
            "status": "action_needed",
        })
        nid += 1

    # No TDS entries recorded
    if not tds_entries and total_income > 0:
        notifications.append({
            "id": nid,
            "type": "alert",
            "category": "tds",
            "priority": "high",
            "title": "No TDS Records Found",
            "message": "You have income but no TDS entries. Add TDS from your Form 26AS to avoid tax mismatch.",
            "status": "action_needed",
        })
        nid += 1

    # Unclaimed GST ITC
    if gst_receipts:
        total_gst = sum(_f(r.gst_amount) for r in gst_receipts)
        notifications.append({
            "id": nid,
            "type": "alert",
            "category": "gst",
            "priority": "medium",
            "title": "Unclaimed GST ITC Available",
            "message": f"₹{total_gst:,.2f} in GST Input Tax Credit detected from your receipts. Claim before March 31.",
            "status": "action_needed",
        })
        nid += 1

    # No transactions uploaded yet
    if not txns:
        notifications.append({
            "id": nid,
            "type": "info",
            "category": "onboarding",
            "priority": "high",
            "title": "Upload Your Bank Statement",
            "message": "Go to Upload → upload your HDFC/SBI/ICICI CSV to get started with tax analysis.",
            "status": "action_needed",
        })
        nid += 1

    # Sort: overdue first, then due_soon, then action_needed, then upcoming
    priority_order = {"high": 0, "medium": 1, "low": 2}
    status_order = {"overdue": 0, "due_soon": 1, "action_needed": 2, "upcoming": 3}
    notifications.sort(key=lambda n: (status_order.get(n.get("status", "upcoming"), 3), priority_order.get(n.get("priority", "low"), 2)))

    return {
        "notifications": notifications,
        "total": len(notifications),
        "overdue": sum(1 for n in notifications if n.get("status") == "overdue"),
        "due_soon": sum(1 for n in notifications if n.get("status") == "due_soon"),
        "action_needed": sum(1 for n in notifications if n.get("status") == "action_needed"),
    }
