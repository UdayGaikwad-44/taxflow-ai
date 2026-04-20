from datetime import date, timedelta
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.transaction import Transaction
from app.models.receipt import Receipt
from app.models.user import User
from app.utils.auth import get_current_user
from app.utils.db import get_db

router = APIRouter(prefix="/matches")

MATCH_WINDOW_DAYS = 3  # receipts within +/- 3 days of a transaction


def _f(v) -> float:
    if v is None:
        return 0.0
    return float(v) if isinstance(v, Decimal) else float(v)


def _amounts_close(a: float, b: float, tolerance: float = 0.02) -> bool:
    """Returns True if amounts are within 2% of each other."""
    if a == 0 and b == 0:
        return True
    larger = max(abs(a), abs(b))
    return abs(a - b) / larger <= tolerance


@router.get("/auto")
async def auto_match(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Automatically matches receipts to transactions by:
    1. Amount proximity (within 2%)
    2. Date proximity (within ±3 days)
    Returns matched pairs and unmatched receipts.
    """
    # Load all transactions and receipts for the user
    txn_result = await db.execute(
        select(Transaction).where(Transaction.user_id == current_user.id)
    )
    txns = txn_result.scalars().all()

    rec_result = await db.execute(
        select(Receipt).where(Receipt.user_id == current_user.id)
    )
    receipts = rec_result.scalars().all()

    matched_pairs = []
    unmatched_receipts = []
    used_txn_ids = set()

    for receipt in receipts:
        receipt_date = receipt.date
        receipt_amount = _f(receipt.amount)
        if not receipt_date or receipt_amount == 0:
            unmatched_receipts.append(_receipt_mini(receipt))
            continue

        best_match = None
        best_score = float("inf")

        for txn in txns:
            if str(txn.id) in used_txn_ids:
                continue
            if txn.direction != "out":  # receipts are expenses (out)
                continue
            txn_amount = abs(_f(txn.amount_inr))
            if not _amounts_close(receipt_amount, txn_amount):
                continue
            date_diff = abs((txn.txn_date - receipt_date).days)
            if date_diff > MATCH_WINDOW_DAYS:
                continue
            score = date_diff + abs(receipt_amount - txn_amount)
            if score < best_score:
                best_score = score
                best_match = txn

        if best_match:
            used_txn_ids.add(str(best_match.id))
            matched_pairs.append({
                "receipt": _receipt_mini(receipt),
                "transaction": _txn_mini(best_match),
                "match_confidence": "high" if best_score < 1 else "medium",
                "amount_diff": round(abs(_f(receipt.amount) - abs(_f(best_match.amount_inr))), 2),
                "date_diff_days": abs((best_match.txn_date - receipt_date).days),
            })
        else:
            unmatched_receipts.append(_receipt_mini(receipt))

    return {
        "total_receipts": len(receipts),
        "matched": len(matched_pairs),
        "unmatched": len(unmatched_receipts),
        "matched_pairs": matched_pairs,
        "unmatched_receipts": unmatched_receipts,
        "tip": f"{len(unmatched_receipts)} receipt(s) could not be matched — check dates and amounts."
               if unmatched_receipts else "All receipts matched! ✅",
    }


@router.post("/{match_id}/confirm")
async def confirm_match(
    match_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Confirm a manual match (reserved for future persistent match storage)."""
    return {
        "ok": True,
        "match_id": match_id,
        "status": "confirmed",
        "message": "Match confirmed. Future version will persist this to match history.",
    }


def _receipt_mini(r: Receipt) -> dict:
    return {
        "id": str(r.id),
        "merchant": r.merchant,
        "amount": _f(r.amount),
        "date": str(r.date) if r.date else None,
        "category": r.category,
    }


def _txn_mini(t: Transaction) -> dict:
    return {
        "id": str(t.id),
        "date": str(t.txn_date),
        "narration": t.description,
        "amount": abs(_f(t.amount_inr)),
        "category": t.category,
    }
