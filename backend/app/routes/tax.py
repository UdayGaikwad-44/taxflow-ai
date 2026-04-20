from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.transaction import Transaction
from app.models.user import User
from app.utils.auth import get_current_user, get_current_user_id
from app.utils.db import get_db

router = APIRouter(prefix="/tax")


def calculate_tax(income: float) -> float:
    """
    2025-26 new regime slabs + 4% cess.
    Section 87A rebate: if total income <= 12,00,000 => tax = 0.
    """
    income = max(0.0, float(income))
    if income <= 1_200_000:
        return 0.0

    slabs = [
        (400_000, 0.00),
        (800_000, 0.05),
        (1_200_000, 0.10),
        (1_600_000, 0.15),
        (2_000_000, 0.20),
        (2_400_000, 0.25),
        (float("inf"), 0.30),
    ]

    tax = 0.0
    prev = 0.0
    remaining = income

    for upper, rate in slabs:
        band = min(remaining, upper - prev)
        if band > 0:
            tax += band * rate
            remaining -= band
        prev = upper
        if remaining <= 0:
            break

    return float(tax * 1.04)


# Endpoint 17
@router.get("/optimize")
async def optimize_tax(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Transaction).where(Transaction.user_id == current_user.id))
    txns = result.scalars().all()

    def amt(v) -> float:
        if v is None:
            return 0.0
        if isinstance(v, Decimal):
            return float(v)
        return float(v)

    total_income = sum(amt(t.amount_inr) for t in txns if t.direction == "in")
    total_expenses = sum(
        abs(amt(t.amount_inr))
        for t in txns
        if t.direction == "out" and bool(getattr(t, "deductible", False)) and (t.section or "") not in ("80C", "80D")
    )

    raw_80c = sum(abs(amt(t.amount_inr)) for t in txns if (t.section or "") == "80C")
    raw_80d = sum(abs(amt(t.amount_inr)) for t in txns if (t.section or "") == "80D")
    deduction_80c = float(min(raw_80c, 150_000))
    deduction_80d = float(min(raw_80d, 25_000))

    presumptive_income = total_income * 0.50
    taxable_itr4 = presumptive_income
    tax_itr4 = calculate_tax(taxable_itr4)

    taxable_itr3 = total_income - total_expenses - deduction_80c - deduction_80d
    if taxable_itr3 < 0:
        taxable_itr3 = 0.0
    tax_itr3 = calculate_tax(taxable_itr3)

    if tax_itr3 <= tax_itr4:
        recommendation = "ITR-3"
        savings = tax_itr4 - tax_itr3
    else:
        recommendation = "ITR-4"
        savings = tax_itr3 - tax_itr4

    return {
        "total_income": float(total_income),
        "total_expenses": float(total_expenses),
        "deduction_80c": float(deduction_80c),
        "deduction_80d": float(deduction_80d),
        "itr4": {
            "taxable_income": float(taxable_itr4),
            "tax": float(tax_itr4),
            "method": "Presumptive (50% of income)",
        },
        "itr3": {
            "taxable_income": float(taxable_itr3),
            "tax": float(tax_itr3),
            "method": "Actual expenses",
        },
        "recommendation": recommendation,
        "savings": float(savings),
        "currency": "INR",
    }


# Endpoint 18
@router.post("/report/generate")
def generate_report(user_id: str = Depends(get_current_user_id)):
    return {"ok": True, "user_id": user_id, "message": "Generate tax report placeholder"}


@router.get("/audit-score")
async def audit_score(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Transaction).where(Transaction.user_id == current_user.id))
    txns = result.scalars().all()

    def amt(v) -> float:
        if v is None:
            return 0.0
        if isinstance(v, Decimal):
            return float(v)
        return float(v)

    total_income = sum(amt(t.amount_inr) for t in txns if t.direction == "in")

    score = 0
    flagged_items: list[str] = []
    fixes: list[str] = []

    def trigger(points: int, flag: str, fix: str):
        nonlocal score
        score += points
        flagged_items.append(flag)
        fixes.append(fix)

    # Signal 1 (25 pts): Large inflows detected
    large_inflows_count = sum(1 for t in txns if t.direction == "in" and amt(t.amount_inr) > 50_000)
    if large_inflows_count > 0:
        trigger(
            25,
            "Large inflows detected — add client invoices",
            "Attach invoices/contracts for large UPI/NEFT/IMPS credits.",
        )

    # Signal 2 (20 pts): Deductions > 60% of income
    total_deductions = sum(abs(amt(t.amount_inr)) for t in txns if bool(getattr(t, "deductible", False)))
    if total_income > 0 and total_deductions > total_income * 0.60:
        trigger(
            20,
            "Deductions exceed 60% of income — attach all receipts",
            "Upload receipts and ensure deductible expenses are business-related.",
        )

    # Signal 3 (20 pts): High-value deductions count
    high_value_ded_count = sum(
        1
        for t in txns
        if bool(getattr(t, "deductible", False)) and abs(amt(t.amount_inr)) > 5_000
    )
    if high_value_ded_count > 2:
        trigger(
            20,
            "High-value deductions found — upload receipts as proof",
            "Upload itemized bills/receipts for deductible spends above ₹5,000.",
        )

    # Signal 4 (15 pts): Round-number transactions divisible by 50,000
    round_count = 0
    for t in txns:
        a = abs(amt(t.amount_inr))
        if a > 0 and (a % 50_000) == 0:
            round_count += 1
    if round_count > 0:
        trigger(
            15,
            "Round-number transactions detected — add narration/purpose",
            "Add detailed narration/purpose and supporting docs for round-number entries.",
        )

    # Signal 5 (10 pts): Cash-like large debits
    large_debits_count = sum(
        1 for t in txns if t.direction == "out" and abs(amt(t.amount_inr)) > 200_000
    )
    if large_debits_count > 0:
        trigger(
            10,
            "Large debits detected — add expense receipts",
            "Upload receipts/invoices for large debits and map them to projects/vendors.",
        )

    # Signal 6 (10 pts): Income concentration
    if total_income > 0:
        max_inflow = 0.0
        for t in txns:
            if t.direction == "in":
                max_inflow = max(max_inflow, amt(t.amount_inr))
        if max_inflow > total_income * 0.80:
            trigger(
                10,
                "Single source dominates income — diversify or document",
                "Keep strong documentation for the primary client/source (SOW, invoices, payments).",
            )

    score = max(0, min(100, int(score)))
    if score <= 40:
        zone = "green"
    elif score <= 70:
        zone = "orange"
    else:
        zone = "red"

    return {
        "score": score,
        "zone": zone,
        "flagged_items": flagged_items,
        "fixes": fixes,
        "total_signals_triggered": len(flagged_items),
        "currency": "INR",
    }



@router.get("/health-score")
async def health_score(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import select
    from app.models.tds_entry import TDSEntry

    result = await db.execute(select(Transaction).where(Transaction.user_id == current_user.id))
    txns = result.scalars().all()

    tds_result = await db.execute(select(TDSEntry).where(TDSEntry.user_id == current_user.id))
    tds_entries = tds_result.scalars().all()

    def amt(v):
        if v is None: return 0.0
        from decimal import Decimal
        return float(v) if isinstance(v, Decimal) else float(v)

    deductible_txns = [t for t in txns if getattr(t, "deductible", False)]
    with_section = [t for t in deductible_txns if t.section]
    coverage = len(with_section) / len(deductible_txns) if deductible_txns else 0
    score1 = round(coverage * 30, 2)

    total_income = sum(amt(t.amount_inr) for t in txns if t.direction == "in")
    total_deductions = sum(abs(amt(t.amount_inr)) for t in txns if getattr(t, "deductible", False))
    audit = 0
    if sum(1 for t in txns if t.direction == "in" and amt(t.amount_inr) > 50000) > 0: audit += 25
    if total_income > 0 and total_deductions > total_income * 0.60: audit += 20
    if sum(1 for t in txns if getattr(t,"deductible",False) and abs(amt(t.amount_inr)) > 5000) > 2: audit += 20
    if sum(1 for t in txns if abs(amt(t.amount_inr)) > 0 and abs(amt(t.amount_inr)) % 50000 == 0) > 0: audit += 15
    score2 = round((1 - audit / 100) * 25, 2)

    total_80c = sum(abs(amt(t.amount_inr)) for t in txns if (t.section or "") == "80C")
    score3 = round(min(total_80c / 150000, 1.0) * 20, 2)

    score4 = 15.0 if tds_entries else 0.0
    score5 = 5.0

    total = min(100, round(score1 + score2 + score3 + score4 + score5))
    zone = "green" if total >= 70 else "orange" if total >= 40 else "red"

    components = {"deduction_coverage": score1, "audit_risk_inverted": score2, "80c_utilization": score3, "advance_tax_compliance": score4, "gst_itc": score5}
    lowest = min(components, key=components.get)
    tips = {"deduction_coverage": "Upload receipts for all deductible expenses", "audit_risk_inverted": "Fix audit risk flags to improve your score", "80c_utilization": f"Invest more in 80C instruments — ₹{150000 - int(total_80c):,} limit remaining", "advance_tax_compliance": "Add TDS entries from your Form 26AS", "gst_itc": "Claim your pending GST Input Tax Credits"}

    return {"score": total, "zone": zone, "components": components, "tip": tips[lowest], "currency": "INR"}
