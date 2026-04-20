import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True, nullable=False)

    txn_date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    amount_inr: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)  # ₹
    direction: Mapped[str] = mapped_column(String(10), nullable=False)  # "in" | "out"
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    deductible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    section: Mapped[str | None] = mapped_column(String(30), nullable=True)  # e.g., 37(1), 80C, 80D
    financial_year: Mapped[str | None] = mapped_column(String(9), index=True, nullable=True)  # e.g., 2025-2026
    merchant: Mapped[str | None] = mapped_column(String(200), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

