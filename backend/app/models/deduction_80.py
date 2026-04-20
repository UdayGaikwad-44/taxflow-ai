import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Deduction80(Base):
    __tablename__ = "deductions_80"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True, nullable=False)

    section: Mapped[str] = mapped_column(String(20), nullable=False)  # e.g., 80C, 80D
    instrument: Mapped[str | None] = mapped_column(String(200), nullable=True)  # PPF, ELSS, Mediclaim
    paid_date: Mapped[date | None] = mapped_column(Date, index=True, nullable=True)
    amount_inr: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    proof_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

