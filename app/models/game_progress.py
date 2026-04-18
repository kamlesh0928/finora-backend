import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Float, DateTime, ForeignKey, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base

def _utcnow():
    return datetime.now(timezone.utc)

class GameProgress(Base):
    __tablename__ = "game_progress"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    module: Mapped[str] = mapped_column(
        String(30), nullable=False
    )  # budgeting, fraud, emergency, scenario
    scenario_id: Mapped[str] = mapped_column(String(100), nullable=False)
    decision_index: Mapped[int] = mapped_column(Integer, nullable=False)
    decision_title: Mapped[str] = mapped_column(String(255), nullable=False)
    savings_impact: Mapped[float] = mapped_column(Float, default=0.0)
    stress_impact: Mapped[float] = mapped_column(Float, default=0.0)
    wallet_impact: Mapped[float] = mapped_column(Float, default=0.0)
    notes: Mapped[str] = mapped_column(Text, nullable=True)

    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    synced: Mapped[bool] = mapped_column(default=True)
