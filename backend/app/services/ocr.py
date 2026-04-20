import base64
import json
import os
import re
import uuid
from datetime import date
from datetime import datetime as dt

import httpx

from app.models.receipt import Receipt
from app.utils.db import AsyncSessionLocal


async def process_receipt_image(image_bytes: bytes, user_id: str, financial_year: str):
    """
    Sends a receipt image to OpenRouter Vision API (qwen/qwen2.5-vl-72b-instruct),
    extracts structured data, and saves it to the DB.
    """
    b64 = base64.b64encode(image_bytes).decode("utf-8")
    api_key = os.environ.get("OPENROUTER_API_KEY", "")

    payload = {
        "model": "qwen/qwen2.5-vl-72b-instruct",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
                    {
                        "type": "text",
                        "text": (
                            "Extract from this receipt and return ONLY a valid JSON object with these exact keys: "
                            "merchant_name (string), amount (number, no currency symbol), date (YYYY-MM-DD string), "
                            "gstin (string or null), gst_amount (number, default 0), expense_category (string), "
                            "is_80c (boolean), is_80d (boolean). "
                            "Do not include any explanation or markdown, just raw JSON."
                        ),
                    },
                ],
            }
        ],
    }

    data = _default_data()
    try:
        async with httpx.AsyncClient(timeout=45) as client:
            resp = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://taxflow.ai",
                    "X-Title": "TaxFlow AI",
                },
                json=payload,
            )
            resp.raise_for_status()
            result = resp.json()
            text = result["choices"][0]["message"]["content"]
            data = _parse_json_safe(text)
    except Exception:
        pass  # Fall back to default_data — receipt still saved as Uncategorized

    try:
        date_str = data.get("date") or str(date.today())
        parsed_date = dt.strptime(date_str[:10], "%Y-%m-%d").date()
    except (ValueError, TypeError):
        parsed_date = date.today()

    async with AsyncSessionLocal() as db:
        receipt = Receipt(
            id=uuid.uuid4(),
            user_id=uuid.UUID(user_id),
            financial_year=financial_year,
            merchant=data.get("merchant_name") or "Unknown",
            amount=float(data.get("amount") or 0),
            date=parsed_date,
            gstin=data.get("gstin"),
            gst_amount=float(data.get("gst_amount") or 0),
            category=data.get("expense_category") or "Uncategorized",
            section_80c=bool(data.get("is_80c", False)),
            section_80d=bool(data.get("is_80d", False)),
        )
        db.add(receipt)
        await db.commit()
        await db.refresh(receipt)
    return {
        "id": str(receipt.id),
        "merchant": receipt.merchant,
        "amount": float(receipt.amount or 0),
        "category": receipt.category,
        "section_80c": receipt.section_80c,
        "section_80d": receipt.section_80d,
    }


def _default_data() -> dict:
    return {
        "merchant_name": "Unknown",
        "amount": 0,
        "date": str(date.today()),
        "gstin": None,
        "gst_amount": 0,
        "expense_category": "Uncategorized",
        "is_80c": False,
        "is_80d": False,
    }


def _parse_json_safe(text: str) -> dict:
    """
    Robustly extracts JSON from LLM output that may contain markdown fences,
    extra text before/after, or whitespace.
    """
    # Remove markdown code fences
    text = re.sub(r"```(?:json)?", "", text, flags=re.IGNORECASE).strip()
    text = text.strip("`").strip()

    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Find the first { ... } block
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    return _default_data()
