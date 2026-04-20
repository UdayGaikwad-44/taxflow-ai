import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Receipt(Base):
    __tablename__ = "receipts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True, nullable=False)
    financial_year: Mapped[str | None] = mapped_column(String(20), nullable=True)
    merchant: Mapped[str | None] = mapped_column(String(200), nullable=True)
    amount: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    date: Mapped[date | None] = mapped_column(Date, nullable=True)
    gstin: Mapped[str | None] = mapped_column(String(20), nullable=True)
    gst_amount: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    section_80c: Mapped[bool] = mapped_column(Boolean, default=False)
    section_80d: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
