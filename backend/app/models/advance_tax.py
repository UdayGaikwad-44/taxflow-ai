import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class AdvanceTax(Base):
    __tablename__ = "advance_tax"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True, nullable=False)

    financial_year: Mapped[str] = mapped_column(String(9), index=True, nullable=False)
    instalment_label: Mapped[str] = mapped_column(String(30), nullable=False)  # Jun/Sep/Dec/Mar
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    paid_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    amount_inr: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    challan_ref: Mapped[str | None] = mapped_column(String(80), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

