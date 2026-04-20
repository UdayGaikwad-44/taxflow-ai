import io
import uuid
from datetime import date
from typing import Any

import pandas as pd

from app.models.transaction import Transaction
from app.utils.db import AsyncSessionLocal


# ─── Narration Categorizer ──────────────────────────────────────────────────────

def categorize_narration(narration: str) -> tuple[str, bool, str | None]:
    """
    Categorizes a transaction narration into (category, is_deductible, section).
    Returns sensible defaults for uncategorized items.
    """
    n = (narration or "").upper()

    def has(*keywords: str) -> bool:
        return any(k in n for k in keywords)

    # Food & Meals
    if has("ZOMATO", "SWIGGY", "RESTAURANT", "CAFE", "HOTEL FOOD", "DUNZO"):
        return ("Meals", True, "37(1)")
    # Internet / Telecom
    if has("AIRTEL", "JIO", "BSNL", "INTERNET", "VODAFONE", "VI "):
        return ("Internet", True, "37(1)")
    # Insurance 80C
    if has("LICPREMIUM", "LIC PREMIUM", "LIC "):
        return ("Insurance-80C", True, "80C")
    # Insurance 80D (Health)
    if has("STAR HEALTH", "NIVA BUPA", "HDFC ERGO", "HEALTH INS", "MEDICAL INS"):
        return ("Insurance-80D", True, "80D")
    # Travel
    if has("IRCTC", "MAKEMYTRIP", "GOIBIBO", "INDIGO", "SPICEJET", "AIRINDIA", "OLA", "UBER"):
        return ("Travel", True, "37(1)")
    # Software / SaaS
    if has("ADOBE", "MICROSOFT", "GOOGLE WORKSPACE", "GITHUB", "NOTION", "SLACK", "ZOOM"):
        return ("Software-SaaS", True, "37(1)")
    # Office Supplies
    if has("STATIONERY", "AMAZON BUSINESS", "FLIPKART BUSINESS"):
        return ("Office Supplies", True, "37(1)")
    # Investments (80C)
    if has("PPF", "ELSS", "MUTUAL FUND", "SIP", "NSC", "SUKANYA", "NPS"):
        return ("Investment-80C", True, "80C")
    # Rent
    if has("RENT", "HOUSE RENT", "OFFICE RENT"):
        return ("Rent", True, "37(1)")
    # Professional fees
    if has("CA FEE", "AUDIT FEE", "LEGAL FEE", "ADVOCATE"):
        return ("Professional Fees", True, "37(1)")
    # Shopping (not deductible)
    if has("AMAZON", "FLIPKART", "MYNTRA"):
        return ("Shopping", False, None)
    # Entertainment (not deductible)
    if has("NETFLIX", "SPOTIFY", "PRIME VIDEO", "HOTSTAR", "YOUTUBE PREMIUM"):
        return ("Entertainment", False, None)
    # Income
    if has("SALARY", "SAL CREDIT", "STIPEND"):
        return ("Salary", False, None)
    if has("UPI CR", "NEFT CR", "IMPS CR", "INB CR", "ACH CR"):
        return ("Income", False, None)
    # ATM / Cash
    if has("ATM", "CASH WITHDRAWAL", "CASH WD"):
        return ("Cash", False, None)
    # EMI / Loan
    if has("EMI", "LOAN", "NACH"):
        return ("EMI-Loan", False, None)

    return ("Uncategorized", False, None)


# ─── Schema Detection ─────────────────────────────────────────────────────────

def _detect_schema(df: pd.DataFrame) -> dict[str, Any]:
    """Detects which bank format the CSV belongs to."""
    cols = [str(c) for c in df.columns.tolist()]

    # HDFC Bank
    if all(c in cols for c in ["Date", "Narration", "Withdrawal Amt.", "Deposit Amt."]):
        return {"bank": "HDFC", "date": "Date", "text": "Narration", "debit": "Withdrawal Amt.", "credit": "Deposit Amt."}

    # SBI Bank
    if all(c in cols for c in ["Txn Date", "Description", "Debit", "Credit"]):
        return {"bank": "SBI", "date": "Txn Date", "text": "Description", "debit": "Debit", "credit": "Credit"}

    # ICICI Bank
    if all(c in cols for c in ["Transaction Date", "Transaction Remarks", "Amount (INR)", "Type (Dr/Cr)"]):
        return {"bank": "ICICI", "date": "Transaction Date", "text": "Transaction Remarks", "amount": "Amount (INR)", "type": "Type (Dr/Cr)"}

    # Axis Bank
    if all(c in cols for c in ["Tran Date", "PARTICULARS", "DR", "CR"]):
        return {"bank": "AXIS", "date": "Tran Date", "text": "PARTICULARS", "debit": "DR", "credit": "CR"}
    # Axis alternate format
    if all(c in cols for c in ["Transaction Date", "Transaction Details", "Debit Amount", "Credit Amount"]):
        return {"bank": "AXIS", "date": "Transaction Date", "text": "Transaction Details", "debit": "Debit Amount", "credit": "Credit Amount"}

    # Kotak Mahindra Bank
    if all(c in cols for c in ["Dt", "Narration", "Debit", "Credit"]):
        return {"bank": "KOTAK", "date": "Dt", "text": "Narration", "debit": "Debit", "credit": "Credit"}
    if all(c in cols for c in ["Transaction Date", "Description", "Debit Amount", "Credit Amount"]):
        return {"bank": "KOTAK", "date": "Transaction Date", "text": "Description", "debit": "Debit Amount", "credit": "Credit Amount"}

    # Yes Bank
    if all(c in cols for c in ["Transaction Date", "Transaction Details", "Withdrawals", "Deposits"]):
        return {"bank": "YES", "date": "Transaction Date", "text": "Transaction Details", "debit": "Withdrawals", "credit": "Deposits"}

    # IndusInd Bank
    if all(c in cols for c in ["Value Date", "Description / Narration", "Debit", "Credit"]):
        return {"bank": "INDUSIND", "date": "Value Date", "text": "Description / Narration", "debit": "Debit", "credit": "Credit"}

    # Generic fallback — smart column detection
    date_col = next((c for c in cols if any(k in c.lower() for k in ["date", "dt"])), cols[0])
    text_col = next((c for c in cols if any(k in c.lower() for k in ["narr", "desc", "remark", "particular", "detail"])), cols[min(1, len(cols)-1)])
    amt_col = next((c for c in cols if any(k in c.lower() for k in ["amount", "amt", "value"])), cols[min(2, len(cols)-1)])

    return {"bank": "GENERIC", "date": date_col, "text": text_col, "amount": amt_col}


# ─── Type Helpers ─────────────────────────────────────────────────────────────

def _to_date(v: Any) -> date | None:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    dt = pd.to_datetime(v, errors="coerce", dayfirst=True)
    if pd.isna(dt):
        return None
    return dt.date()


def _to_float(v: Any) -> float:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return 0.0
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().replace(",", "").replace("₹", "").replace(" ", "")
    if not s:
        return 0.0
    try:
        return float(s)
    except Exception:
        return 0.0


# ─── Main Parser ──────────────────────────────────────────────────────────────

async def parse_bank_csv(file_bytes: bytes, user_id: str, financial_year: str) -> dict:
    """
    Parses a bank statement CSV and saves transactions to the database.
    Supports HDFC, SBI, ICICI, Axis, Kotak, Yes Bank, IndusInd, and generic CSV formats.
    """
    job_id = str(uuid.uuid4())

    # Try reading CSV; if that fails, try with different separators
    try:
        df = pd.read_csv(io.BytesIO(file_bytes), thousands=",")
    except Exception:
        try:
            df = pd.read_csv(io.BytesIO(file_bytes), sep="\t", thousands=",")
        except Exception:
            return {"total": 0, "credits": 0, "debits": 0, "job_id": job_id, "error": "Could not parse CSV"}

    df = df.dropna(how="all")  # Remove fully empty rows
    # Strip whitespace from column names
    df.columns = [str(c).strip() for c in df.columns]

    schema = _detect_schema(df)
    bank = schema["bank"]
    total = credits = debits = 0
    txns: list[Transaction] = []

    if bank in ("HDFC", "SBI", "AXIS", "KOTAK", "YES", "INDUSIND"):
        # Debit/Credit split columns
        for _, row in df.iterrows():
            txn_date = _to_date(row.get(schema["date"]))
            narration = str(row.get(schema["text"]) or "").strip()
            debit = _to_float(row.get(schema["debit"]))
            credit = _to_float(row.get(schema["credit"]))

            if txn_date is None or (debit == 0 and credit == 0 and not narration):
                continue

            if credit > 0:
                amount = credit
                direction = "in"
                credits += 1
            else:
                amount = -abs(debit)
                direction = "out"
                debits += 1

            category, deductible, section = categorize_narration(narration)
            txns.append(Transaction(
                user_id=user_id,
                txn_date=txn_date,
                description=narration or "Bank transaction",
                amount_inr=amount,
                direction=direction,
                category=category,
                deductible=deductible,
                section=section,
                financial_year=financial_year,
            ))
            total += 1

    elif bank == "ICICI":
        for _, row in df.iterrows():
            txn_date = _to_date(row.get(schema["date"]))
            narration = str(row.get(schema["text"]) or "").strip()
            amt = _to_float(row.get(schema["amount"]))
            txn_type = str(row.get(schema["type"]) or "").strip().upper()

            if txn_date is None or (amt == 0 and not narration):
                continue

            if txn_type.startswith("CR"):
                amount = abs(amt)
                direction = "in"
                credits += 1
            else:
                amount = -abs(amt)
                direction = "out"
                debits += 1

            category, deductible, section = categorize_narration(narration)
            txns.append(Transaction(
                user_id=user_id,
                txn_date=txn_date,
                description=narration or "Bank transaction",
                amount_inr=amount,
                direction=direction,
                category=category,
                deductible=deductible,
                section=section,
                financial_year=financial_year,
            ))
            total += 1

    else:
        # Generic: single amount column, sign determines direction
        for _, row in df.iterrows():
            txn_date = _to_date(row.get(schema["date"]))
            narration = str(row.get(schema["text"]) or "").strip()
            amt = _to_float(row.get(schema["amount"]))

            if txn_date is None or (amt == 0 and not narration):
                continue

            direction = "in" if amt > 0 else "out"
            if direction == "in":
                credits += 1
            else:
                debits += 1

            category, deductible, section = categorize_narration(narration)
            txns.append(Transaction(
                user_id=user_id,
                txn_date=txn_date,
                description=narration or "Bank transaction",
                amount_inr=amt,
                direction=direction,
                category=category,
                deductible=deductible,
                section=section,
                financial_year=financial_year,
            ))
            total += 1

    async with AsyncSessionLocal() as db:
        if txns:
            db.add_all(txns)
        await db.commit()

    return {
        "total": total,
        "credits": credits,
        "debits": debits,
        "job_id": job_id,
        "bank_detected": bank,
    }
