import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base

def _utcnow():
    return datetime.now(timezone.utc)

class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    tx_type: Mapped[str] = mapped_column(String(10), nullable=False)  # Type of transaction: 'credit' or 'debit'
    category: Mapped[str] = mapped_column(String(30), nullable=False)  # Broad category of the financial activity (e.g., budgeting, fraud, etc.)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    source_module: Mapped[str] = mapped_column(
        String(30), nullable=True
    )  # Reference to the game module (e.g., smart_budgeting, fraud_prevention)
    scenario_id: Mapped[str] = mapped_column(String(100), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    synced: Mapped[bool] = mapped_column(default=True)
