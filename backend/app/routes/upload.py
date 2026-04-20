import asyncio
import uuid
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, Query, UploadFile

from app.models.user import User
from app.services.parser import parse_bank_csv
from app.services.ocr import process_receipt_image
from app.utils.auth import get_current_user

router = APIRouter()


async def _run_parse_bank_csv(contents: bytes, user_id: str, financial_year: str):
    """Wrapper to safely run the async parser in a BackgroundTask."""
    await parse_bank_csv(contents, user_id, financial_year)


async def _run_ocr(contents: bytes, user_id: str, financial_year: str):
    """Wrapper to safely run the async OCR processor in a BackgroundTask."""
    await process_receipt_image(contents, user_id, financial_year)


@router.post("/bank-statement")
async def upload_bank_statement(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    financial_year: str = Query("FY2025-26", description="Financial year, e.g. FY2025-26"),
):
    contents = await file.read()
    job_id = str(uuid.uuid4())
    background_tasks.add_task(
        _run_parse_bank_csv, contents, str(current_user.id), financial_year
    )
    return {
        "message": "Bank statement upload received. Processing in background.",
        "job_id": job_id,
        "filename": file.filename,
        "financial_year": financial_year,
        "tip": "Refresh transactions in a few seconds to see parsed entries.",
    }


@router.post("/receipt")
async def upload_receipt(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    financial_year: str = Query("FY2025-26", description="Financial year, e.g. FY2025-26"),
):
    contents = await file.read()
    job_id = str(uuid.uuid4())
    background_tasks.add_task(
        _run_ocr, contents, str(current_user.id), financial_year
    )
    return {
        "message": "Receipt upload received. AI OCR processing in background.",
        "job_id": job_id,
        "filename": file.filename,
        "financial_year": financial_year,
        "tip": "Refresh receipts in a few seconds to see the extracted data.",
    }
