import uuid
from datetime import datetime

from sqlalchemy import DateTime, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class TaxReport(Base):
    __tablename__ = "tax_reports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True, nullable=False)

    financial_year: Mapped[str] = mapped_column(String(9), index=True, nullable=False)  # e.g., 2025-2026
    regime: Mapped[str] = mapped_column(String(20), nullable=False)  # old | new

    taxable_income_inr: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    tax_liability_inr: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    tds_credit_inr: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    advance_tax_paid_inr: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    refund_or_payable_inr: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0)

    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    report_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)

