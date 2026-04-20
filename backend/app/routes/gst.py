from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal
from app.models.receipt import Receipt
from app.models.user import User
from app.utils.auth import get_current_user
from app.utils.db import get_db

router = APIRouter()

@router.get("/itc-summary")
async def gst_itc_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Receipt).where(Receipt.user_id == current_user.id))
    receipts = result.scalars().all()

    def amt(v):
        if v is None: return 0.0
        return float(v) if isinstance(v, Decimal) else float(v)

    # Group by GST rate
    by_rate = {"5%": 0.0, "12%": 0.0, "18%": 0.0, "28%": 0.0, "unknown": 0.0}
    total_itc = 0.0
    valid_receipts = []

    for r in receipts:
        gst = amt(r.gst_amount)
        if gst <= 0:
            continue
        total_itc += gst
        base = amt(r.amount)
        rate = "unknown"
        if base > 0:
            pct = round((gst / base) * 100)
            if pct <= 6: rate = "5%"
            elif pct <= 13: rate = "12%"
            elif pct <= 19: rate = "18%"
            elif pct <= 29: rate = "28%"
        by_rate[rate] = by_rate.get(rate, 0.0) + gst
        valid_receipts.append({
            "merchant": r.merchant,
            "amount": float(amt(r.amount)),
            "gst_amount": gst,
            "gstin": r.gstin,
            "category": r.category,
            "date": str(r.date) if r.date else None,
        })

    return {
        "total_itc_available": round(total_itc, 2),
        "by_rate": by_rate,
        "receipts_with_gst": len(valid_receipts),
        "total_receipts": len(receipts),
        "entries": valid_receipts,
        "alert": f"You have ₹{total_itc:,.2f} in unclaimed GST ITC — claim before March 31" if total_itc > 0 else "No GST ITC found. Upload receipts with GSTIN to detect credits.",
        "currency": "INR"
    }
