from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal

from app.models.transaction import Transaction
from app.models.tds_entry import TDSEntry
from app.models.user import User
from app.utils.auth import get_current_user
from app.utils.db import get_db
from app.services.pdf_export import generate_tax_report_pdf

router = APIRouter()

@router.get("/generate")
async def generate_report(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    def amt(v):
        if v is None: return 0.0
        return float(v) if isinstance(v, Decimal) else float(v)

    result = await db.execute(select(Transaction).where(Transaction.user_id == current_user.id))
    txns = result.scalars().all()

    tds_result = await db.execute(select(TDSEntry).where(TDSEntry.user_id == current_user.id))
    tds_entries = tds_result.scalars().all()

    transactions = [{"date": str(t.txn_date), "narration": t.description, "amount": amt(t.amount_inr), "category": t.category, "deductible": t.deductible, "section": t.section} for t in txns]

    total_income = sum(amt(t.amount_inr) for t in txns if t.direction == "in")
    total_expenses = sum(abs(amt(t.amount_inr)) for t in txns if t.direction == "out" and t.deductible and (t.section or "") not in ("80C", "80D"))
    deduction_80c = min(sum(abs(amt(t.amount_inr)) for t in txns if (t.section or "") == "80C"), 150000)
    deduction_80d = min(sum(abs(amt(t.amount_inr)) for t in txns if (t.section or "") == "80D"), 25000)

    from app.routes.tax import calculate_tax
    taxable_itr4 = total_income * 0.5
    taxable_itr3 = max(0, total_income - total_expenses - deduction_80c - deduction_80d)

    tax_data = {"total_income": total_income, "total_expenses": total_expenses, "deduction_80c": deduction_80c, "deduction_80d": deduction_80d, "itr4": {"taxable_income": taxable_itr4, "tax": calculate_tax(taxable_itr4), "method": "Presumptive (50% of income)"}, "itr3": {"taxable_income": taxable_itr3, "tax": calculate_tax(taxable_itr3), "method": "Actual expenses"}, "recommendation": "ITR-3" if calculate_tax(taxable_itr3) <= calculate_tax(taxable_itr4) else "ITR-4"}

    audit_score = 0
    if sum(1 for t in txns if getattr(t,"deductible",False) and abs(amt(t.amount_inr)) > 5000) > 2: audit_score += 20
    flagged = []
    if sum(1 for t in txns if t.direction == "in" and amt(t.amount_inr) > 50000) > 0:
        audit_score += 25
        flagged.append("Large inflows detected — add client invoices")
    if sum(1 for t in txns if abs(amt(t.amount_inr)) > 0 and abs(amt(t.amount_inr)) % 50000 == 0) > 0: audit_score += 15
    if total_income > 0 and (total_expenses + deduction_80c + deduction_80d) > total_income * 0.60:
        audit_score += 20
        flagged.append("Deductions exceed 60% of income")
    audit_data = {"score": audit_score, "zone": "green" if audit_score <= 40 else "orange" if audit_score <= 70 else "red", "flagged_items": flagged}

    total_80c = sum(abs(amt(t.amount_inr)) for t in txns if (t.section or "") == "80C")
    health_score = round(min(100, (len([t for t in txns if t.section]) / len(txns) * 30 if txns else 0) + ((1 - audit_score/100) * 25) + (min(total_80c/150000, 1.0) * 20) + (15 if tds_entries else 0) + 5))
    health_data = {"score": health_score, "zone": "green" if health_score >= 70 else "orange" if health_score >= 40 else "red", "tip": "Upload receipts for all deductible expenses"}

    user_data = {"name": current_user.full_name or current_user.email, "itr_form": current_user.itr_form or "ITR-3"}
    tds_data = {"total": sum(float(e.tds_amount_inr or 0) for e in tds_entries)}

    pdf_buffer = generate_tax_report_pdf(user_data, transactions, tax_data, audit_data, tds_data, health_data)

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=taxflow_report_{current_user.id}.pdf"}
    )
