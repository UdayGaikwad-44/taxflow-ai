"""
AI Chat Route — POST /api/ai/chat

Uses OpenRouter API with a general-purpose LLM (meta-llama/llama-3.3-70b-instruct or similar).
Injects the user's financial summary as system context so the AI can answer
tax questions specific to the user's situation.
"""
import json
import os
from decimal import Decimal
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.transaction import Transaction
from app.models.tds_entry import TDSEntry
from app.models.receipt import Receipt
from app.models.user import User
from app.utils.auth import get_current_user
from app.utils.db import get_db
from app.utils.tax_calc import calculate_tax

router = APIRouter(prefix="/ai")

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "meta-llama/llama-3.3-70b-instruct"  # fast, capable, free tier available


class ChatMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []
    model: Optional[str] = None


def _f(v) -> float:
    if v is None:
        return 0.0
    return float(v) if isinstance(v, Decimal) else float(v)


async def _build_financial_context(user: User, db: AsyncSession) -> str:
    """Builds a concise financial summary to inject as system context."""
    txn_result = await db.execute(select(Transaction).where(Transaction.user_id == user.id))
    txns = txn_result.scalars().all()

    tds_result = await db.execute(select(TDSEntry).where(TDSEntry.user_id == user.id))
    tds_entries = tds_result.scalars().all()

    rec_result = await db.execute(select(Receipt).where(Receipt.user_id == user.id))
    receipts = rec_result.scalars().all()

    total_income = sum(_f(t.amount_inr) for t in txns if t.direction == "in")
    total_expenses = sum(abs(_f(t.amount_inr)) for t in txns if t.direction == "out" and t.deductible)
    deduction_80c = min(sum(abs(_f(t.amount_inr)) for t in txns if (t.section or "") == "80C"), 150_000)
    deduction_80c += min(sum(_f(r.amount) for r in receipts if r.section_80c), max(0, 150_000 - deduction_80c))
    deduction_80d = min(sum(abs(_f(t.amount_inr)) for t in txns if (t.section or "") == "80D"), 25_000)
    taxable_income = max(0.0, total_income - total_expenses - deduction_80c - deduction_80d)
    tax_liability = calculate_tax(taxable_income)
    tds_total = sum(_f(e.tds_amount_inr) for e in tds_entries)
    gst_itc = sum(_f(r.gst_amount) for r in receipts if _f(r.gst_amount) > 0)

    return f"""
You are TaxFlow AI, an expert Indian tax assistant for FY 2025-26.
Always give practical, actionable advice specific to the user's actual financial data below.
Always refer to amounts in ₹ INR. Be concise and friendly.

USER PROFILE:
- Name: {user.full_name or user.email}
- User Type: {user.user_type or 'Not specified'} 
- Recommended ITR Form: {user.itr_form or 'Not determined'}

FINANCIAL SUMMARY (FY 2025-26):
- Total Income: ₹{total_income:,.2f}
- Deductible Expenses: ₹{total_expenses:,.2f}
- 80C Deductions: ₹{deduction_80c:,.2f} (limit ₹1,50,000)
- 80D Deductions: ₹{deduction_80d:,.2f} (limit ₹25,000)
- Taxable Income (estimated): ₹{taxable_income:,.2f}
- Estimated Tax Liability: ₹{tax_liability:,.2f}
- TDS Already Deducted: ₹{tds_total:,.2f}
- Net Tax Payable: ₹{max(0, tax_liability - tds_total):,.2f}
- GST ITC Available: ₹{gst_itc:,.2f}
- Transactions Recorded: {len(txns)}
- Receipts Uploaded: {len(receipts)}
- TDS Entries: {len(tds_entries)}

TAX REGIME: New Regime (FY 2025-26 slabs with Section 87A rebate — income up to ₹12L is tax-free).

Answer only tax-related questions. If asked non-tax questions, politely redirect to tax topics.
""".strip()


@router.post("/chat")
async def ai_chat(
    payload: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="OpenRouter API key not configured. Set OPENROUTER_API_KEY in .env"
        )

    system_context = await _build_financial_context(current_user, db)
    model = payload.model or DEFAULT_MODEL

    messages = [{"role": "system", "content": system_context}]
    for msg in payload.history[-10:]:  # Keep last 10 messages for context
        messages.append({"role": msg.role, "content": msg.content})
    messages.append({"role": "user", "content": payload.message})

    request_payload = {
        "model": model,
        "messages": messages,
        "max_tokens": 1024,
        "temperature": 0.3,
    }

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                OPENROUTER_URL,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://taxflow.ai",
                    "X-Title": "TaxFlow AI",
                },
                json=request_payload,
            )
            resp.raise_for_status()
            result = resp.json()
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="AI service timed out. Please try again.")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"AI service error: {e.response.status_code}")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI service unavailable: {str(e)}")

    try:
        reply = result["choices"][0]["message"]["content"]
        tokens_used = result.get("usage", {})
    except (KeyError, IndexError):
        raise HTTPException(status_code=502, detail="Unexpected response from AI service")

    return {
        "reply": reply,
        "model": model,
        "tokens_used": tokens_used,
    }
