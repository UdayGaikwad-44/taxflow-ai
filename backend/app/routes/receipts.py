from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.receipt import Receipt
from app.models.user import User
from app.utils.auth import get_current_user
from app.utils.db import get_db

router = APIRouter(prefix="/receipts")


def _float(v) -> float:
    if v is None:
        return 0.0
    return float(v) if isinstance(v, Decimal) else float(v)


def _receipt_out(r: Receipt) -> dict:
    return {
        "id": str(r.id),
        "merchant": r.merchant,
        "amount": _float(r.amount),
        "date": str(r.date) if r.date else None,
        "gstin": r.gstin,
        "gst_amount": _float(r.gst_amount),
        "category": r.category,
        "section_80c": r.section_80c,
        "section_80d": r.section_80d,
        "financial_year": r.financial_year,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }


# GET /api/receipts — list all receipts for the logged-in user
@router.get("")
async def list_receipts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    financial_year: Optional[str] = Query(None),
    limit: int = Query(200, le=500),
    offset: int = Query(0, ge=0),
):
    q = select(Receipt).where(Receipt.user_id == current_user.id)
    if financial_year:
        q = q.where(Receipt.financial_year == financial_year)
    q = q.order_by(Receipt.date.desc()).limit(limit).offset(offset)

    result = await db.execute(q)
    receipts = result.scalars().all()
    return {
        "ok": True,
        "items": [_receipt_out(r) for r in receipts],
        "count": len(receipts),
        "currency": "INR",
    }


# GET /api/receipts/{receipt_id} — single receipt details
@router.get("/{receipt_id}")
async def get_receipt(
    receipt_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Receipt).where(
            Receipt.id == receipt_id,
            Receipt.user_id == current_user.id,
        )
    )
    receipt = result.scalar_one_or_none()
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")
    return _receipt_out(receipt)


# DELETE /api/receipts/{receipt_id} — delete a receipt
@router.delete("/{receipt_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_receipt(
    receipt_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Receipt).where(
            Receipt.id == receipt_id,
            Receipt.user_id == current_user.id,
        )
    )
    receipt = result.scalar_one_or_none()
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")
    await db.delete(receipt)
    await db.commit()
