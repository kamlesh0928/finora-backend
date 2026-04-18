import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Float, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base

def _utcnow():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=True)  # Nullable for Google OAuth authenticated users
    role: Mapped[str] = mapped_column(String(50), nullable=True)  # User demographic category for personalized content
    language: Mapped[str] = mapped_column(String(10), default="en")
    auth_provider: Mapped[str] = mapped_column(String(20), default="email")  # Identifier for the authentication method used

    # Game state
    wallet_balance: Mapped[float] = mapped_column(Float, default=5000.0)
    emergency_fund: Mapped[float] = mapped_column(Float, default=0.0)
    financial_health_score: Mapped[int] = mapped_column(default=50)
    stress_level: Mapped[float] = mapped_column(Float, default=0.20)
    safety_score: Mapped[int] = mapped_column(default=50)

    # Stats
    total_earned: Mapped[float] = mapped_column(Float, default=0.0)
    total_spent: Mapped[float] = mapped_column(Float, default=0.0)
    scenarios_completed: Mapped[int] = mapped_column(default=0)
    current_streak: Mapped[int] = mapped_column(default=0)
    longest_streak: Mapped[int] = mapped_column(default=0)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)
    last_login_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    last_sync_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
