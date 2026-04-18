import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base

def _utcnow():
    return datetime.now(timezone.utc)

class UserAchievement(Base):
    __tablename__ = "user_achievements"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    badge_id: Mapped[str] = mapped_column(String(50), nullable=False)
    badge_name: Mapped[str] = mapped_column(String(100), nullable=False)
    badge_description: Mapped[str] = mapped_column(Text, nullable=True)
    badge_icon: Mapped[str] = mapped_column(String(50), nullable=True)

    earned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
