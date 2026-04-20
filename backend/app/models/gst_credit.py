import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class GSTCredit(Base):
    __tablename__ = "gst_credits"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True, nullable=False)

    invoice_date: Mapped[date | None] = mapped_column(Date, index=True, nullable=True)
    vendor_gstin: Mapped[str | None] = mapped_column(String(20), nullable=True)
    invoice_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    taxable_value_inr: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    gst_amount_inr: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    itc_eligible: Mapped[str] = mapped_column(String(10), nullable=False, default="yes")  # yes|no

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

