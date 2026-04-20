from decimal import Decimal
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tds_entry import TDSEntry
from app.models.user import User
from app.utils.auth import get_current_user
from app.utils.db import get_db

router = APIRouter(prefix="/tds")


class TDSEntryIn(BaseModel):
    deductor_name: str
    deductor_tan: str
    amount: float
    section: Literal["194J", "194C", "192"]
    quarter: Literal["Q1", "Q2", "Q3", "Q4"]
    financial_year: str = "FY2025-26"


def _amt(v) -> float:
    if v is None:
        return 0.0
    if isinstance(v, Decimal):
        return float(v)
    return float(v)


def _entry_out(e: TDSEntry) -> dict:
    return {
        "id": str(e.id),
        "deductor_name": e.deductor_name,
        "deductor_tan": e.tan,
        "amount": float(_amt(e.tds_amount_inr)),
        "section": e.section,
        "quarter": e.quarter,
        "financial_year": e.financial_year,
        "created_at": e.created_at.isoformat() if e.created_at else None,
    }


# POST /api/tds/entry — create a TDS entry
@router.post("/entry", status_code=status.HTTP_201_CREATED)
async def create_tds_entry(
    payload: TDSEntryIn,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    entry = TDSEntry(
        user_id=current_user.id,
        deductor_name=payload.deductor_name,
        tan=payload.deductor_tan,
        section=payload.section,
        quarter=payload.quarter,
        financial_year=payload.financial_year,
        credited_date=None,
        amount_credited_inr=0,
        tds_amount_inr=payload.amount,
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return _entry_out(entry)


# GET /api/tds/summary — summary of all TDS entries for current user
@router.get("/summary")
async def tds_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(TDSEntry).where(TDSEntry.user_id == current_user.id))
    entries = result.scalars().all()

    total = sum(_amt(e.tds_amount_inr) for e in entries)

    by_section = {"194J": 0.0, "194C": 0.0, "192": 0.0}
    by_quarter = {"Q1": 0.0, "Q2": 0.0, "Q3": 0.0, "Q4": 0.0}
    by_deductor: dict[str, float] = {}

    for e in entries:
        amt = _amt(e.tds_amount_inr)
        if e.section in by_section:
            by_section[e.section] += amt
        if e.quarter in by_quarter:
            by_quarter[e.quarter] += amt
        key = (e.deductor_name or "Unknown").strip() or "Unknown"
        by_deductor[key] = by_deductor.get(key, 0.0) + amt

    return {
        "total_tds_deducted": float(total),
        "by_section": {k: float(v) for k, v in by_section.items()},
        "by_quarter": {k: float(v) for k, v in by_quarter.items()},
        "by_deductor": [{"deductor_name": k, "total_tds": float(v)} for k, v in by_deductor.items()],
        "entries": [_entry_out(e) for e in entries],
        "currency": "INR",
    }


# GET /api/tds — list all TDS entries for current user
@router.get("")
async def list_tds(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(TDSEntry)
        .where(TDSEntry.user_id == current_user.id)
        .order_by(TDSEntry.created_at.desc())
    )
    entries = result.scalars().all()
    return {
        "ok": True,
        "items": [_entry_out(e) for e in entries],
        "count": len(entries),
        "currency": "INR",
    }


# DELETE /api/tds/{entry_id} — delete a TDS entry
@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tds_entry(
    entry_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(TDSEntry).where(
            TDSEntry.id == entry_id,
            TDSEntry.user_id == current_user.id,
        )
    )
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="TDS entry not found")
    await db.delete(entry)
    await db.commit()


# POST /api/tds/import — bulk import from Form 26AS CSV
@router.post("/import")
async def import_tds(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Placeholder for Form 26AS / AIS bulk import.
    Future: Accept CSV file, parse deductor TAN, section, quarter, amount and bulk-insert.
    Currently returns a descriptive message of what to send.
    """
    return {
        "ok": True,
        "message": "Form 26AS / AIS import — upload CSV with columns: deductor_name, deductor_tan, amount, section (194J/194C/192), quarter (Q1-Q4)",
        "user_id": str(current_user.id),
        "note": "POST to /api/tds/entry for each row from your Form 26AS statement.",
    }
