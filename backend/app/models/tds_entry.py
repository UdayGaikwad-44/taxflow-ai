import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class TDSEntry(Base):
    __tablename__ = "tds_entries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True, nullable=False)

    deductor_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    tan: Mapped[str | None] = mapped_column(String(20), nullable=True)  # deductor TAN
    section: Mapped[str | None] = mapped_column(String(20), nullable=True)  # e.g., 194J
    quarter: Mapped[str | None] = mapped_column(String(2), nullable=True)  # Q1..Q4
    financial_year: Mapped[str | None] = mapped_column(String(9), index=True, nullable=True)  # FY2025-26
    credited_date: Mapped[date | None] = mapped_column(Date, index=True, nullable=True)
    amount_credited_inr: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    tds_amount_inr: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

