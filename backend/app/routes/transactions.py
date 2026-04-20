from datetime import date as date_type
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.transaction import Transaction
from app.models.user import User
from app.utils.auth import get_current_user
from app.utils.db import get_db

router = APIRouter(prefix="/transactions")


class TransactionIn(BaseModel):
    date: date_type
    narration: str
    amount: float          # positive = income, negative = expense
    direction: str         # "in" | "out"
    category: Optional[str] = None
    deductible: bool = False
    section: Optional[str] = None
    financial_year: str = "FY2025-26"
    merchant: Optional[str] = None


def _txn_out(t: Transaction) -> dict:
    return {
        "id": str(t.id),
        "date": str(t.txn_date),
        "narration": t.description,
        "amount": float(t.amount_inr),
        "direction": t.direction,
        "category": t.category,
        "deductible": t.deductible,
        "section": t.section,
        "financial_year": t.financial_year,
        "merchant": t.merchant,
    }


# POST /api/transactions — create a single manual transaction
@router.post("", status_code=status.HTTP_201_CREATED)
async def create_transaction(
    payload: TransactionIn,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    direction = payload.direction
    if direction not in ("in", "out"):
        raise HTTPException(status_code=400, detail="direction must be 'in' or 'out'")

    txn = Transaction(
        user_id=current_user.id,
        txn_date=payload.date,
        description=payload.narration,
        amount_inr=payload.amount,
        direction=direction,
        category=payload.category or "Uncategorized",
        deductible=payload.deductible,
        section=payload.section,
        financial_year=payload.financial_year,
        merchant=payload.merchant,
    )
    db.add(txn)
    await db.commit()
    await db.refresh(txn)
    return _txn_out(txn)


# GET /api/transactions — list user's transactions with optional filters
@router.get("")
async def get_transactions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    financial_year: Optional[str] = Query(None),
    direction: Optional[str] = Query(None),
    limit: int = Query(200, le=500),
    offset: int = Query(0, ge=0),
):
    q = select(Transaction).where(Transaction.user_id == current_user.id)
    if financial_year:
        q = q.where(Transaction.financial_year == financial_year)
    if direction and direction in ("in", "out"):
        q = q.where(Transaction.direction == direction)
    q = q.order_by(Transaction.txn_date.desc()).limit(limit).offset(offset)

    result = await db.execute(q)
    transactions = result.scalars().all()
    return {
        "ok": True,
        "user_id": str(current_user.id),
        "items": [_txn_out(t) for t in transactions],
        "count": len(transactions),
        "currency": "INR",
    }


# DELETE /api/transactions/{txn_id} — delete a transaction
@router.delete("/{txn_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction(
    txn_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Transaction).where(
            Transaction.id == txn_id,
            Transaction.user_id == current_user.id,
        )
    )
    txn = result.scalar_one_or_none()
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")
    await db.delete(txn)
    await db.commit()
